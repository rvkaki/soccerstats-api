FROM python:3.8-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Run the application
# Fly.io provides PORT env var, default to 8000 if not set
CMD hypercorn main:app --bind "0.0.0.0:${PORT:-8000}"

