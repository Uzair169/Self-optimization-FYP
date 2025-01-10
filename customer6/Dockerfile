# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install Flask
RUN pip install Flask pandapower requests

# Make port 5006 available to the world outside this container
EXPOSE 5006

# Define the command to start the service
CMD ["python", "customer6.py"]
