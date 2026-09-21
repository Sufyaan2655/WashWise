# WashWise backend — container image
FROM python:3.13-slim

WORKDIR /app

# Install dependencies first (better layer caching)
# gunicorn is added here (container-only; local dev uses `python app.py`)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn==23.0.0

# Copy the application code
COPY . .

# Gunicorn serves the Flask app in the container on port 5000
EXPOSE 5000
CMD ["gunicorn", "-b", "0.0.0.0:5000", "app:app"]
