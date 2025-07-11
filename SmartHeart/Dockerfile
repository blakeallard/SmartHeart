# Use a lightweight Python image
FROM python:3.11-slim

# Set working directory in container
WORKDIR /app

# Copy everything from current directory to /app in the container
COPY . /app

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose the Flask port
EXPOSE 5050

# Run the Flask app
CMD ["python", "api_server.py"]