FROM python:3.11-slim

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir -r Backend/requirements.txt

# Unbuffered so logs show in real time
CMD ["python", "-u", "Backend/api_server.py"]