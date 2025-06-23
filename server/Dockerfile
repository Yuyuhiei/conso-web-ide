# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set the working directory inside the container
WORKDIR /app

# Install system dependencies, including gcc and supervisor
# THIS IS THE CORRECT PLACE FOR GCC
RUN apt-get update && apt-get install -y gcc build-essential supervisor

# Copy and install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code from the "server" directory
COPY . .

# Copy the supervisor configuration file into the container
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Expose the ports for both servers.
EXPOSE 5000 
EXPOSE 5001 

# Command to run supervisord, which will start both of your python scripts
CMD ["/usr/bin/supervisord"]