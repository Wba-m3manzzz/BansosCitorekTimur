# BansosWeb

Frontend React untuk sistem klasifikasi penerima bantuan sosial.

## Menjalankan web

Pastikan API KNN sudah berjalan di `http://127.0.0.1:8000`.

```powershell
cd "C:\Users\Muhamad Muslih\Desktop\Skripsi Mansur\BansosWeb"
npm install
npm run dev
```

Jika API berjalan di alamat lain, buat file `.env` dari `.env.example`, lalu ubah:

```text
VITE_API_URL=http://127.0.0.1:8000
```

## Halaman yang memakai API

- Dashboard: `GET /api/summary`
- Data Warga: `GET/POST/PUT/DELETE /api/warga`
- Proses Klasifikasi: `POST /api/process-all` dan `PUT /api/warga/{id}`
- Hasil Klasifikasi: `GET /api/hasil-klasifikasi`
- Export Data: `GET /api/download/hasil-klasifikasi`
- Chatbot cek NIK: `GET /api/warga/by-nik/{nik}`
