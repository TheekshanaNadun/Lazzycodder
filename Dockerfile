FROM python:3.12-slim

# System dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libssl-dev \
    zlib1g-dev \
    libffi-dev \
    ffmpeg \
    python3-distutils \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install critical Python packages first
RUN pip install --no-cache-dir setuptools==68.2.2 wheel

# Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Application code
COPY run.py .

# Persistent storage
VOLUME /app/output

EXPOSE 7860

CMD ["python", "run.py"]
