# Use the official Python base image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080

# Set working directory
WORKDIR /app

# Copy dependency files
COPY requirements.txt ./

# Install dependencies
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy the rest of the application code
COPY . .

# Set the entrypoint to use Gunicorn with 4 workers, listening on PORT
#CMD ["gunicorn", "--bind", ":8080", "--timeout", "1200", "run:app"]

# Set workers to 1 because I also set concurrency to 1. This is because Cloud Run 
# blocks on long running tasks (which this app has a lot of). 
# So, we're creating a Cloud run instance to handle each request.
CMD ["gunicorn", "--bind", ":8080", "--timeout", "1200", "--workers", "1", "--threads", "16", "run:app"]
