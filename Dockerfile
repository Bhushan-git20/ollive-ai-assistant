FROM python:3.12-slim

# Install Node.js for Next.js frontend
RUN apt-get update && apt-get install -y \
    curl \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Set up a new user named "user" with UID 1000
RUN useradd -m -u 1000 user

# Set environment variables
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH

WORKDIR $HOME/app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install frontend dependencies
COPY frontend/package*.json ./frontend/
RUN cd frontend && (npm ci || npm install)

# Copy the rest of the application files and change ownership
COPY --chown=user:user . $HOME/app

# Switch to the non-root user to build Next.js and run the application
USER user
RUN cd frontend && npm run build

# HuggingFace Spaces expects port 7860 by default
EXPOSE 7860

CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "7860"]
