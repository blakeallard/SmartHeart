# VitalStream API

This is the backend for **VitalStream**, a real-time heart rate and SpO₂ monitoring application. It uses a Flask REST API to receive and serve biometric data collected from a wearable device (e.g. ESP32 + MAX30102) and supports integration with mobile or web apps (e.g. Flutter frontend).

---

## 🚀 Features

- 🫀 Accepts live heart rate and oxygen saturation readings
- 🤖 Uses machine learning for health predictions (optional)
- 🔌 Built with Flask and Docker for easy deployment
- 📂 Supports storing and retrieving readings via REST API

---

## 📦 Project Structure

```
.
├── api_server.py        # Main Flask application
├── requirements.txt     # Python dependencies
├── Dockerfile           # Docker setup for deployment
└── README.md            # You're reading it :)
```

---

## 🐳 Running Locally with Docker

1. Build the Docker image:

```bash
docker build -t vitalstream-api .
```

2. Run the container:

```bash
docker run -p 5000:5000 vitalstream-api
```

Your API will be live at: `http://localhost:5000`

---

## 🌐 API Endpoints

| Method | Endpoint           | Description                         |
|--------|--------------------|-------------------------------------|
| GET    | `/health`          | Check server status                 |
| POST   | `/submit-reading`  | Submit a new BPM/SpO₂ reading       |
| GET    | `/get-readings`    | Fetch user-specific health history |

> Add authentication and error handling in production.

---

## 📡 Deployment

To deploy this API publicly, connect the repo to:
- [Render](https://render.com)
- [Railway](https://railway.app)
- [Fly.io](https://fly.io)

These services support Docker and have free tiers.

---

## 🧠 Future Improvements

- JWT user authentication
- CSV export + analytics dashboard
- Enhanced ML health prediction model
- HTTPS + database integration (PostgreSQL / Firebase)

---

## 📘 License

MIT License — feel free to use, fork, or modify.

---

Built with ❤️ by [Blake Allard](https://github.com/blakeallard)
