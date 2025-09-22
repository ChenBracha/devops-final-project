# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Upgrade pip and install packages
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY ./app /app

# Expose the port the app runs on
EXPOSE 5000

# Run the app using gunicorn WSGI server
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "main:app"]