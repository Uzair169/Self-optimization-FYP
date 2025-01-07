# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install Flask and requests
RUN pip install Flask requests prometheus-client

# Make port 5000 available to the world outside this container
EXPOSE 5000
EXPOSE 9099

# Define the command to start the service
CMD ["python", "optimize.py"]
