FROM python:3.12-slim

WORKDIR /app

# Install dependency system
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements terlebih dahulu agar cache docker optimal
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Copy seluruh project
COPY . .

# Flask production port
EXPOSE 5000

# Jalankan menggunakan Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "app:app"]