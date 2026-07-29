# Gunakan base image Python yang stabil dan ringan
FROM python:3.11-slim

# Pastikan log Python langsung muncul tanpa di-buffer
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Set working directory utama
WORKDIR /app

# Copy file requirements.txt dari folder backend
COPY backend/requirements.txt .

# Install seluruh dependency Python
RUN pip install --no-cache-dir -r requirements.txt

# Copy seluruh isi proyek ke dalam container
COPY . .

# Pindah ke direktori backend agar uvicorn menemukan file main.py
WORKDIR /app/backend

# Jalankan Uvicorn menggunakan port dinamis dari Railway ($PORT)
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]