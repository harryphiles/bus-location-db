# Use the official Python image as the base image
FROM python:3.12-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Set the working directory in the container
WORKDIR /app
# add logs folder
RUN mkdir logs

# Copy the project files into the container
COPY . .

# Install project dependencies
RUN apt-get update && \
    apt-get -y install libpq-dev gcc && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir -r requirements.txt

# Command to run the Python script
CMD ["python", "main.py"]
