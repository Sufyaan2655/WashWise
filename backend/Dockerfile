# WashWise backend — container image
FROM python:3.13-slim

WORKDIR /app

# Install dependencies first (better layer caching)
# requirements.txt already includes gunicorn for production use
# (local dev still just runs `python app.py`).
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Gunicorn serves the Flask app. $PORT is provided by the platform
# (e.g. Railway) at runtime; defaults to 5000 for plain `docker run`.
EXPOSE 5000
CMD gunicorn app:app --bind 0.0.0.0:${PORT:-5000}
