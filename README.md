# SmartHeart ❤️📲

SmartHeart is a real-time health monitoring system that reads and analyzes heart rate and SpO₂ data using an ESP32 microcontroller and a MAX30102 pulse oximeter sensor. The system streams data live to a Flask backend and a Flutter mobile app for visualization and health prediction.

## 🩺 Features

- 📟 Real-time BPM and SpO₂ monitoring via MAX30102 sensor  
- 📶 Live data transmission from ESP32 to Flask server (via HTTP and WebSocket)  
- 📱 Flutter app displays waveform + predictions + history  
- 💾 Sensor data logged and stored in a PostgreSQL database  
- 🤖 Machine learning model (Python + joblib) predicts health status from vitals  
- 🌐 Deployable on Render with REST API and WebSocket streaming  

## 🔧 Tech Stack

- **Embedded**: ESP32, MAX30102, C++ (Arduino IDE)  
- **Backend**: Python, Flask, Flask-SocketIO, SQLAlchemy, PostgreSQL  
- **Frontend**: Flutter (Dart), WebSocket client  
- **ML**: scikit-learn, pandas, NumPy, joblib  

## 🚀 How It Works

1. **ESP32 Firmware** collects sensor data and sends it to the Flask API every second  
2. **Flask Backend** logs, processes, and broadcasts data to all connected clients  
3. **ML Model** classifies whether the vitals fall within a healthy range  
4. **Flutter App** receives real-time data and displays waveform + predictions  
5. **Database** stores historical readings per user for analysis and export  

## 📸 Demo

*Coming soon — live screenshots of waveform animation, prediction results, and hardware setup.*

## 🧠 Creator

**Blake Allard**  
Computer Science student passionate about embedded systems, C++, and real-world health tech.  
Guitarist-turned-coder building systems that actually help people.  

---

**SmartHeart is part of a research project at Cal State LA’s SMART IoT program.**

