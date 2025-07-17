# ========== IMPORTS ==========
import os
import eventlet
eventlet.monkey_patch()  # Allows Flask-SocketIO to work properly with threading and sockets


from flask import Flask, request, jsonify  # Core Flask modules for web server and API endpoints
from flask_socketio import SocketIO        # WebSocket support
from flask_sqlalchemy import SQLAlchemy    # ORM to interact with a PostgreSQL database
from sqlalchemy.exc import IntegrityError  # For catching database errors (e.g., duplicate username)
from werkzeug.security import generate_password_hash, check_password_hash  # Password hashing


import joblib        # For loading the trained ML model
import csv           # For reading BPM logs from CSV
import threading     # To run background waveform streaming
import time
import serial        # To read serial data from hardware (e.g. ESP32)
import pandas as pd  # For preparing model input from JSON


# ========== FLASK APP SETUP ==========
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "postgresql://smartheart_db_user:oXyFH5b48Q78PLZtc7xiY7hIAkLGh1PJ@dpg-d1oq4pjuibrs73d2b8ag-a.oregon-postgres.render.com/smartheart_db")
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
    model = joblib.load("Backend/model.pkl")
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

    return jsonify({"prediction": int(prediction)})

@app.route("/latest-data", methods=["GET"])
def latest_data():
    user_id = request.args.get("user_id")

    if not user_id:
        return jsonify({"error": "Missing user_id"}), 400

    try:
        # Fetch most recent reading from the database
        reading = Reading.query.filter_by(user_id=user_id).order_by(Reading.timestamp.desc()).first()
        if not reading:
            return jsonify({"error": "No readings found"}), 404

        return jsonify({
            "bpm": reading.bpm,
            "spo2": reading.spo2,
            "timestamp": reading.timestamp
        }), 200

    except Exception as e:
        return jsonify({"error": f"Failed to fetch reading: {e}"}), 500
    
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
    data      = request.json
    user_id   = data.get("user_id")
    bpm       = data.get("bpm")
    spo2      = data.get("spo2")
    timestamp = data.get("timestamp")

    if not all([user_id, bpm, spo2, timestamp]):
        return jsonify({"error": "Missing fields"}), 400

    try:
        reading       = Reading(
            user_id   = int(user_id),
            bpm       = int(bpm),
            spo2      = int(spo2),
            timestamp = timestamp
        )
        db.session.add(reading)
        db.session.commit()
        return jsonify({"message": "Reading saved"}), 201
    except Exception as e:
        db.session.rollback()
        print(f"[ERROR] Failed to save reading: {e}")  # <--- Add this line
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
        print("[DEBUG] Initializaing database...")
        db.create_all()
        print("[DEBUG] Database tables created.")

@app.route("/init-db", methods=["POST"])
def manual_init_db():
    try:
        db.create_all()
        return jsonify({"message": "Database initialized"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    print("Starting Flask API server with WebSocket...")
    init_db()
    threading.Thread(target=stream_waveform_data, daemon=True).start()
    port = int(os.environ.get("PORT", 5050))  # fallback to 5051 locally
    socketio.run(app, host="0.0.0.0", port=port)