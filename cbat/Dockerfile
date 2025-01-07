# Use Python slim image
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Copy files
COPY . /app

# Install Flask
RUN pip install Flask

# Expose the port
EXPOSE 8080

# Run the service
CMD ["python", "cbat.py"]
