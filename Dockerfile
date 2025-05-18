# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Copy the dependencies file to the working directory
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the content of the local src directory to the working directory
COPY ./app /app  
# The second argument is the name of the directory in the container where the files will be copied.

# Make port 10000 available to the world outside this container
EXPOSE 10000

# Define environment variable
ENV FLASK_APP=main.py
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_RUN_PORT=10000 
# Gunicorn will use this if not specified in CMD

# Run app.py when the container launches
# Use Gunicorn for production
CMD ["gunicorn", "--bind", "0.0.0.0:10000", "main:app"]