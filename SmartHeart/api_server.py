import eventlet
eventlet.monkey_patch()

from flask import Flask, request, jsonify
from flask_socketio import SocketIO
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
import joblib
import csv
import os
import threading
import time
import serial

# Initialize Flask and SocketIO
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DB_URL")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
socketio = SocketIO(app, cors_allowed_origins="*")

CSV_PATH = "bpm_log.csv"

# Load ML model if available
try:
    model = joblib.load("model.pkl")
except Exception as e:
    print("⚠️ Could not load model.pkl:", e)
    model = None

# Database models
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)

class Reading(db.Model):
    __tablename__ = 'readings'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    bpm = db.Column(db.Integer, nullable=False)
    spo2 = db.Column(db.Integer, nullable=False)
    timestamp = db.Column(db.String, nullable=False)

# Routes
@app.route("/")
def home():
    return "Heart Monitor API is live!"

@app.route("/init-db")
def init_db():
    db.create_all()
    return "✅ Database tables created"

@app.route("/signup", methods=["POST"])
def signup():
    data = request.json
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"error": "Missing username or password"}), 400

    if User.query.filter_by(username=username).first():
        return jsonify({"error": "❌ Username already exists"}), 409

    hashed_pw = generate_password_hash(password)
    new_user = User(username=username, password=hashed_pw)
    db.session.add(new_user)
    db.session.commit()
    return jsonify({"message": "✅ Signup successful"}), 201

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
            "message": "✅ Login successful",
            "user_id": user.id,
            "username": user.username
        }), 200
    else:
        return jsonify({"error": "❌ Invalid credentials"}), 401

@app.route("/submit-reading", methods=["POST"])
def submit_reading():
    data = request.json
    user_id = data.get("user_id")
    bpm = data.get("bpm")
    spo2 = data.get("spo2")
    timestamp = data.get("timestamp")

    if not all([user_id, bpm, spo2, timestamp]):
        return jsonify({"error": "Missing fields"}), 400

    new_reading = Reading(user_id=user_id, bpm=bpm, spo2=spo2, timestamp=timestamp)
    db.session.add(new_reading)
    db.session.commit()
    return jsonify({"message": "✅ Reading saved"}), 201

@app.route("/get-readings", methods=["GET"])
def get_readings():
    user_id = request.args.get("user_id")
    if not user_id:
        return jsonify({"error": "Missing user_id"}), 400

    readings = Reading.query.filter_by(user_id=user_id).order_by(Reading.timestamp.desc()).limit(50).all()
    return jsonify({
        "readings": [
            {"bpm": r.bpm, "spo2": r.spo2, "timestamp": r.timestamp}
            for r in readings
        ]
    })

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

    prediction = model.predict([[bpm, spo2]])[0]
    return jsonify({"prediction": prediction})

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
                "spo2": int(last_row.get("SpO2", 98))
            })
    except Exception as e:
        return jsonify({"error": f"Failed to read CSV: {e}"}), 500

# Serial data thread for waveform broadcasting
def stream_waveform_data():
    try:
        ser = serial.Serial('/dev/cu.usbmodem1101', 115200)
        print("✅ Serial port opened successfully")
    except Exception as e:
        ser = None
        print(f"⚠️ Serial connection failed: {e}")
        return

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
                    continue
        except Exception as e:
            print(f"⚠️ Error reading from serial: {e}")
            break

# Start app
if __name__ == "__main__":
    print("🚀 Starting Flask API server with WebSocket...")
    threading.Thread(target=stream_waveform_data, daemon=True).start()
    socketio.run(app, host="0.0.0.0", port=5050)
