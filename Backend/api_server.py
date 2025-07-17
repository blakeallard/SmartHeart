# ========== IMPORTS ==========
import os
import eventlet
eventlet.monkey_patch()  # Allows Flask-SocketIO to work properly with threading and sockets


from flask import Flask, request, jsonify  # Core Flask modules for web server and API endpoints
from flask_socketio import SocketIO        # WebSocket support
from flask_sqlalchemy import SQLAlchemy    # ORM to interact with a PostgreSQL database
from sqlalchemy.exc import IntegrityError  # For catching database errors (e.g., duplicate username)
from werkzeug.security import generate_password_hash, check_password_hash  # Password hashing


import joblib     # For loading the trained ML model
import csv        # For reading BPM logs from CSV
import threading  # To run background waveform streaming
import time
import serial     # To read serial data from hardware (e.g. ESP32)
import pandas as pd  # For preparing model input from JSON


# ========== FLASK APP SETUP ==========
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")  # Render env var or fallback
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# ========== DATABASE SETUP ==========
db = SQLAlchemy(app)

# User table schema
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

# Reading table schema (each row = 1 health record)
class Reading(db.Model):
    __tablename__ = 'readings'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    bpm = db.Column(db.Integer)
    spo2 = db.Column(db.Integer)
    timestamp = db.Column(db.String)  # Optional: consider changing to DateTime

# WebSocket support with CORS enabled for frontend
socketio = SocketIO(app, cors_allowed_origins="*")

# Path to CSV file that stores log history
CSV_PATH = "bpm_log.csv"

# ========== LOAD ML MODEL ==========
try:
    model = joblib.load("model.pkl")
except Exception as e:
    print("Could not load model.pkl:", e)
    model = None


# ========== ROUTES / API ENDPOINTS ==========

# Home route for health check
@app.route("/")
def home():
    return "Heart Monitor API is live!"


# Predict endpoint: receives BPM and SpO₂, runs through ML model
@app.route("/predict", methods=["POST"])
def predict():
    data = request.json
    print("Incoming data:", data)

    bpm = data.get("bpm")
    spo2 = data.get("spo2")

    if bpm is None or spo2 is None:
        return jsonify({"error": "Missing bpm or spo2"}), 400

    if model is None:
        return jsonify({"error": "Model not loaded"}), 500

    # Format input for model prediction
    X_input = pd.DataFrame([[bpm, spo2]], columns=['BPM', 'SpO2'])
    prediction = model.predict(X_input)[0]

    return jsonify({"prediction": prediction})


# Get latest row from CSV for display on app startup
@app.route("/latest-data", methods=["GET"])
def latest_data():
    if not os.path.exists(CSV_PATH):
        return jsonify({"error": "No CSV data found"}), 404

    try:
        with open(CSV_PATH, "r") as file:
            reader = csv.DictReader(file)
            rows = list(reader)
            if not rows:
                return jsonify({"error": "CSV is empty"}), 404
            last_row = rows[-1]
            return jsonify({
                "bpm": int(last_row["BPM"]),
                "spo2": int(last_row.get("SpO2", 98))  # fallback if missing
            })
    except Exception as e:
        return jsonify({"error": f"Failed to read CSV: {e}"}), 500


# Signup route for registering new users
@app.route("/signup", methods=["POST"])
def signup():
    data = request.json
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"error": "Missing username or password"}), 400

    hashed_pw = generate_password_hash(password)

    try:
        new_user = User(username=username, password=hashed_pw)
        db.session.add(new_user)
        db.session.commit()
        return jsonify({"message": "Signup successful"}), 201
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Username already exists"}), 409


# Login route for authenticating existing users
@app.route("/login", methods=["POST"])
def login():
    data = request.json
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"error": "Missing username or password"}), 400

    user = User.query.filter_by(username=username).first()

    if user and check_password_hash(user.password, password):
        return jsonify({
            "message": "Login successful",
            "user_id": user.id,
            "username": username
        }), 200
    else:
        return jsonify({"error": "Invalid credentials"}), 401


# Submit a reading to the database
@app.route("/submit-reading", methods=["POST"])
def submit_reading():
    data = request.json
    user_id = data.get("user_id")
    bpm = data.get("bpm")
    spo2 = data.get("spo2")
    timestamp = data.get("timestamp")

    if not all([user_id, bpm, spo2, timestamp]):
        return jsonify({"error": "Missing fields"}), 400

    try:
        reading = Reading(user_id=user_id, bpm=bpm, spo2=spo2, timestamp=timestamp)
        db.session.add(reading)
        db.session.commit()
        return jsonify({"message": "Reading saved"}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to save reading: {e}"}), 500


# Get most recent 50 readings for a user
@app.route("/get-readings", methods=["GET"])
def get_readings():
    user_id = request.args.get("user_id")

    if not user_id:
        return jsonify({"error": "Missing user_id"}), 400

    try:
        rows = Reading.query.filter_by(user_id=user_id).order_by(
            Reading.timestamp.desc()
        ).limit(50).all()

        readings = [{
            "bpm": r.bpm,
            "spo2": r.spo2,
            "timestamp": r.timestamp
        } for r in rows]

        return jsonify({"readings": readings})
    except Exception as e:
        return jsonify({"error": f"Failed to fetch readings: {e}"}), 500


# Background thread to read sensor data over serial and emit via WebSocket
def stream_waveform_data():
    try:
        ser = serial.Serial('/dev/cu.usbmodem1101', 115200)
        print("Serial port opened successfully!")
    except Exception as e:
        ser = None
        print(f"Serial connection failed: {e}")
        return  # Exit thread gracefully

    while True:
        try:
            line = ser.readline().decode().strip()
            if line:
                try:
                    bpm_val, spo2_val = map(int, line.split(","))
                    socketio.emit("waveform", {
                        "bpm": bpm_val,
                        "spo2": spo2_val
                    })
                except ValueError:
                    continue  # Ignore malformed lines
        except Exception as e:
            print(f"Error reading from serial: {e}")
            break  # Prevent infinite loop

# Create DB tables if they don’t exist
def init_db():
    with app.app_context():
        db.create_all()


# ========== ENTRY POINT ==========
if __name__ == "__main__":
    print("Starting Flask API server with WebSocket...")
    init_db()
    threading.Thread(target=stream_waveform_data, daemon=True).start()
    socketio.run(app, host="0.0.0.0", port=5051)