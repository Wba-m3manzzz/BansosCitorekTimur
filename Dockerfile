FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Copy file requirements dari folder backend
COPY backend/requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy seluruh folder project ke dalam container
COPY . .

# Pindah direktori kerja ke dalam folder backend
WORKDIR /app/backend

# Jalankan app.main:app karena file main.py ada di dalam folder app/
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
