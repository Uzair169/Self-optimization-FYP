# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install Flask
RUN pip install Flask

# Expose port 8080 for the price manager
EXPOSE 2000

# Define the command to start the service
CMD ["python", "price_manager.py"]
