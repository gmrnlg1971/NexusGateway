FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source
COPY nexus_gateway /app/nexus_gateway

# Run FastAPI with uvicorn
CMD ["uvicorn", "nexus_gateway.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
