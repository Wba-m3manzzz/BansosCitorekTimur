# Backend Sistem Klasifikasi Bantuan Sosial

Backend ini dibangun dengan FastAPI dan Supabase sebagai sumber data utama untuk aplikasi klasifikasi bantuan sosial. Arsitektur dibuat modular agar mudah diintegrasikan dengan frontend React, mudah diuji, dan siap dideploy.

## Fitur Utama

- REST API lengkap untuk data warga bantuan sosial
- Prediksi kelayakan menggunakan model KNN dari artifact `joblib`
- Dashboard summary dan data visualisasi siap pakai
- Autentikasi admin berbasis Supabase Auth dan `admin_profiles`
- Export hasil klasifikasi ke Excel
- CRUD data warga langsung ke Supabase
- Proses ulang semua data untuk refresh hasil prediksi
- CORS sudah disiapkan untuk frontend React

## Struktur Project

```text
backend/
  app/
    main.py
    core/config.py
    db/supabase.py
    schemas/
    services/
    routers/
  models/
    model_knn_bansos.joblib
    model_metadata.json
  tests/
  requirements.txt
  .env.example
  README.md
```

## Teknologi

- Python 3.11+
- FastAPI
- Uvicorn
- Pydantic
- python-dotenv
- supabase
- pandas
- joblib
- openpyxl
- scikit-learn
- CORS middleware
- logging dasar

## Instalasi

1. Buat virtual environment.
2. Install dependency:

```bash
pip install -r requirements.txt
```

3. Salin `.env.example` menjadi `.env` lalu isi nilainya.

## Konfigurasi Supabase

Project ini memakai tabel berikut:

- `warga`
- `evaluasi_k`
- `model_metadata`
- `admin_profiles`

### Kolom minimal yang dipakai

`warga`
- `id`, `nik`, `nama`, `pendapatan`, `pendapatan_nilai`, `tanggungan`, `kondisi_rumah`, `pekerjaan`, `pendidikan`, `jk`, `hub_kel`, `status_aktual`, `status_prediksi`, `prediction_code`, `probability`, `keterangan`, `created_at`, `updated_at`

`evaluasi_k`
- `id`, `k`, `accuracy`, `precision_macro`, `recall_macro`, `f1_macro`, `created_at`

`model_metadata`
- `id`, `version`, `best_k`, `features`, `encoding`, `accuracy_test`, `f1_macro_test`, `artifact_path`, `notes`, `created_at`, `updated_at`

`admin_profiles`
- `id`, `user_id`, `full_name`, `role`, `active`, `created_at`, `updated_at`

### Catatan autentikasi admin

- Login admin memakai Supabase Auth.
- Data profil admin dibaca dari tabel `admin_profiles` berdasarkan `user_id`.
- Token akses dikirim dari frontend melalui header `Authorization: Bearer <token>`.
- `SUPABASE_JWT_SECRET` dipakai untuk validasi token saat endpoint `GET /api/auth/me` dipanggil.

## File `.env`

Contoh isi `.env`:

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_JWT_SECRET=your-jwt-secret
APP_NAME=backend
APP_ENV=development
VITE_API_URL=http://localhost:8000
MODEL_PATH=models/model_knn_bansos.joblib
MODEL_METADATA_PATH=models/model_metadata.json
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
LOG_LEVEL=INFO
```

## Menjalankan Backend

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Health check:

```bash
GET http://localhost:8000/api/health
```

## Endpoint API

### Health dan metadata
- `GET /api/health`
- `GET /api/metadata`

### Dashboard
- `GET /api/summary`
- `GET /api/dashboard`
- `GET /api/evaluasi-k`

### Warga
- `GET /api/warga`
- `GET /api/warga/{id}`
- `GET /api/warga/by-nik/{nik}`
- `POST /api/warga`
- `PUT /api/warga/{id}`
- `DELETE /api/warga/{id}`
- `POST /api/warga/import/excel`

### Prediksi
- `POST /api/predict`
- `POST /api/process-all`

### Hasil klasifikasi
- `GET /api/hasil-klasifikasi`
- `GET /api/download/hasil-klasifikasi`

### Auth
- `POST /api/auth/login`
- `POST /api/auth/logout`
- `GET /api/auth/me`

## Contoh Request

### Login admin

```json
{
  "email": "admin@example.com",
  "password": "secret-password"
}
```

### Input prediksi manual

```json
{
  "pendapatan": "1-3 juta",
  "pendapatan_nilai": 2000000,
  "tanggungan": 3,
  "kondisi_rumah": "sedang",
  "pekerjaan": "buruh",
  "pendidikan": "smp",
  "jk": "laki-laki",
  "hub_kel": "kepala_keluarga"
}
```

### Tambah warga

```json
{
  "nik": "3210000000000001",
  "nama": "Budi Santoso",
  "pendapatan": "1-3 juta",
  "pendapatan_nilai": 2000000,
  "tanggungan": 3,
  "kondisi_rumah": "sedang",
  "pekerjaan": "buruh",
  "pendidikan": "smp",
  "jk": "laki-laki",
  "hub_kel": "kepala_keluarga",
  "status_aktual": "Layak"
}
```

## Contoh Response

### `/api/predict`

```json
{
  "prediction": {
    "status": "Layak",
    "prediction_code": 1,
    "probability": {
      "Layak": 0.87,
      "Tidak Layak": 0.13
    },
    "keterangan": "Layak menerima bantuan sosial",
    "features_used": [2000000.0, 3.0, 1.0, 1.0, 2.0, 1.0, 1.0]
  },
  "metadata_version": "1.0.0",
  "model_ready": true
}
```

### `/api/health`

```json
{
  "status": "degraded",
  "app_name": "backend",
  "environment": "development",
  "database": {
    "status": "not_configured",
    "error": "SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY are required"
  },
  "model": {
    "ready": true,
    "model_path": "models/model_knn_bansos.joblib",
    "metadata_path": "models/model_metadata.json"
  }
}
```

## Alur Integrasi dengan Frontend React

1. Frontend login ke `POST /api/auth/login`.
2. Simpan `access_token` di state atau storage yang aman sesuai kebijakan frontend.
3. Kirim token ke semua request protected melalui `Authorization: Bearer <token>`.
4. Pakai `GET /api/summary` dan `GET /api/dashboard` untuk dashboard.
5. Gunakan `GET /api/warga` dan CRUD endpoint untuk manajemen data.
6. Gunakan `POST /api/predict` untuk prediksi manual tanpa menyimpan data.
7. Gunakan `POST /api/process-all` setelah data berubah besar-besaran.
8. Gunakan `GET /api/download/hasil-klasifikasi` untuk export Excel.

## Jalankan Test

```bash
pytest
```

## Import Data dari Excel ke Supabase

Jika kamu punya file Excel seperti `Data_Penduduk.xlsx`, backend menyediakan endpoint import:

```bash
POST /api/warga/import/excel?file_path=C:\\Users\\Muhamad Muslih\\Desktop\\Skripsi Mansur\\KNN_Bansos_Python\\Data_Penduduk.xlsx
```

Endpoint ini akan:
- membaca file Excel
- memetakan kolom ke tabel `warga`
- menghitung prediksi KNN
- melakukan `upsert` ke Supabase berdasarkan `nik`

Kolom Excel yang didukung fleksibel, misalnya:
- `NIK`
- `Nama`
- `Pendapatan`
- `Pendapatan_Nilai`
- `Jumlah_Tanggungan`
- `Kondisi_Rumah`
- `Pekerjaan`
- `Pendidikan`
- `JK`
- `Hub_Kel`
- `Status_Kelayakan`

## Catatan Deploy

- Simpan semua credential di environment variable.
- Gunakan service role key hanya di backend.
- Frontend React hanya memakai API JSON dari backend ini.
- File Excel tidak dipakai sebagai database utama, hanya untuk import awal atau export hasil.
