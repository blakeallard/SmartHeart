# Use a lightweight Python image
FROM python:3.11-slim

# Set working directory to /app/Backend
WORKDIR /app/Backend

# Copy everything into /app (so we can access both Backend and other folders if needed)
COPY . /app

# Install dependencies from Backend/requirements.txt
RUN pip install --no-cache-dir -r Backend/requirements.txt

# Expose the Flask port
EXPOSE 5050

# Run the Flask app
CMD ["python", "Backend/api_server.py"]