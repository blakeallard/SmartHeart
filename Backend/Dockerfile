# Use a lightweight Python image
FROM python:3.11-slim

# Set working directory to /app/Backend
WORKDIR /app/Backend

# Copy everything into /app (so we can access both Backend and other folders if needed)
COPY . /app

# Correct path now that we are in /app/Backend
RUN pip install --no-cache-dir -r requirements.txt

# Expose the Flask port
EXPOSE 5050

# Run the Flask app
CMD ["python", "api_server.py"]