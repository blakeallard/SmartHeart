# Standard library imports
import os
import threading
import time
import serial
import csv

# Web server & API libraries
from flask             import Flask, request, jsonify
from flask_socketio    import SocketIO
from flask_sqlalchemy  import SQLAlchemy
from sqlalchemy.exc    import IntegrityError
from werkzeug.security import generate_password_hash, check_password_hash

# ML model loading
import joblib

# Patch standard libraries to make them cooperative with eventlet (for WebSocket support)
import eventlet
eventlet.monkey_patch()

# Debug: Print environment variable for database URL
print("DEBUG: DATABASE_URL =", os.environ.get("DATABASE_URL"))

# Initialize Flask app
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")  # PostgreSQL DB URL
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize database connection
db = SQLAlchemy(app)

# Enable WebSocket support
socketio = SocketIO(app, cors_allowed_origins="*")

# Path for CSV backup/logging
CSV_PATH = "bpm_log.csv"

# ---------------------- DATABASE MODELS ----------------------

# User table model
class User(db.Model):
    __tablename__ = 'users'
    id       = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

# Health reading table model
class Reading(db.Model):
    __tablename__ = 'readings'
    id        = db.Column(db.Integer, primary_key=True)
    user_id   = db.Column(db.Integer, db.ForeignKey('users.id'))
    bpm       = db.Column(db.Integer)
    spo2      = db.Column(db.Integer)
    timestamp = db.Column(db.String)

# ---------------------- MODEL LOADING ----------------------

# Load ML model (trained with joblib)
try:
    model = joblib.load("model.pkl")
except Exception as e:
    print("Could not load model.pkl:", e)
    model = None

# ---------------------- API ROUTES ----------------------

@app.route("/")
def home():
    return "Heart Monitor API is live!"

@app.route("/predict", methods=["POST"])
def predict():
    # Receive bpm and spo2 from frontend
    data = request.json
    print("Incoming data:", data)

    bpm  = data.get("bpm")
    spo2 = data.get("spo2")

    # Validate input
    if bpm is None or spo2 is None:
        return jsonify({"error": "Missing bpm or spo2"}), 400

    if model is None:
        return jsonify({"error": "Model not loaded"}), 500

    # Make prediction using trained ML model
    prediction = model.predict([[bpm, spo2]])[0]
    return jsonify({"prediction": prediction})

@app.route("/latest-data", methods=["GET"])
def latest_data():
    # Fetch latest reading for given user_id
    user_id = request.args.get("user_id")
    if not user_id:
        return jsonify({"error": "Missing user_id"}), 400

    latest = (
        Reading.query
        .filter_by(user_id=user_id)
        .order_by(Reading.timestamp.desc())
        .first()
    )

    if latest is None:
        return jsonify({"error": "No readings found"}), 404

    return jsonify({
        "bpm": latest.bpm,
        "spo2": latest.spo2,
        "timestamp": latest.timestamp
    }), 200

@app.route("/signup", methods=["POST"])
def signup():
    # Register a new user
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

@app.route("/login", methods=["POST"])
def login():
    # Authenticate user
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

@app.route("/submit-reading", methods=["POST"])
def submit_reading():
    # Save new health reading
    data = request.json
    user_id   = data.get("user_id")
    bpm       = data.get("bpm")
    spo2      = data.get("spo2")
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

@app.route("/get-readings", methods=["GET"])
def get_readings():
    # Fetch last 50 readings for a user
    user_id = request.args.get("user_id")

    if not user_id:
        return jsonify({"error": "Missing user_id"}), 400

    try:
        rows = Reading.query.filter_by(user_id=user_id).order_by(Reading.timestamp.desc()).limit(50).all()
        readings = [{"bpm": r.bpm, "spo2": r.spo2, "timestamp": r.timestamp} for r in rows]
        return jsonify({"readings": readings})
    except Exception as e:
        return jsonify({"error": f"Failed to fetch readings: {e}"}), 500

# ---------------------- REAL-TIME STREAMING ----------------------

def stream_waveform_data():
    # Background thread: Reads serial data from board and emits over WebSocket
    try:
        ser = serial.Serial('/dev/cu.usbmodem1101', 115200)
        print("Serial port opened successfully!")
    except Exception as e:
        print(f"Serial connection failed: {e}")
        return

    while True:
        try:
            line = ser.readline().decode().strip()
            if line:
                try:
                    # Parse "bpm,spo2" values from serial input
                    bpm_val, spo2_val = map(int, line.split(","))
                    socketio.emit("waveform", {
                        "bpm": bpm_val,
                        "spo2": spo2_val
                    })
                except ValueError:
                    continue  # Skip malformed lines
        except Exception as e:
            print(f"Error reading from serial: {e}")
            break

# ---------------------- DATABASE SETUP ----------------------

def init_db():
    with app.app_context():
        db.create_all()  # Creates tables if they don’t exist

# ---------------------- MAIN ENTRY POINT ----------------------

if __name__ == "__main__":
    print("Starting Flask API server with WebSocket...")
    init_db()
    threading.Thread(target=stream_waveform_data, daemon=True).start()  # Start waveform thread
    socketio.run(app, host="0.0.0.0", port=5051)
