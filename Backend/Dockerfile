# Use a lightweight Python image
FROM python:3.11-slim

# Set working directory to /app
WORKDIR /app

# Copy everything into /app
COPY . .

# Install dependencies
RUN pip install --no-cache-dir -r Backend/requirements.txt

# Expose the Flask port
EXPOSE 5050

# Run the Flask app
CMD ["python", "Backend/api_server.py"]