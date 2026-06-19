FROM python:3.11-slim

# Install Node.js
RUN apt-get update && apt-get install -y curl && \
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs && apt-get clean

WORKDIR /app

# Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Build Next.js frontend (outputs to frontend/out/)
COPY frontend/ ./frontend/
WORKDIR /app/frontend
RUN npm ci && npm run build

# Copy backend
WORKDIR /app
COPY . .

# HF Spaces requires port 7860
EXPOSE 7860
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "7860"]
