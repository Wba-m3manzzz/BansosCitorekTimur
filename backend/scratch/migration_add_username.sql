-- Migration: Tambah kolom username ke tabel admin_profiles
-- Jalankan di Supabase SQL Editor jika prisma db push gagal

-- 1. Tambah kolom username (nullable dulu agar tidak error pada data existing)
ALTER TABLE admin_profiles ADD COLUMN IF NOT EXISTS username TEXT;

-- 2. Isi username untuk admin yang sudah ada (pakai bagian sebelum @ dari email di auth.users)
UPDATE admin_profiles ap
SET username = split_part(u.email, '@', 1)
FROM auth.users u
WHERE ap.user_id = u.id::text
  AND ap.username IS NULL;

-- 3. Jadikan NOT NULL dan UNIQUE setelah data terisi
ALTER TABLE admin_profiles ALTER COLUMN username SET NOT NULL;
ALTER TABLE admin_profiles ADD CONSTRAINT admin_profiles_username_key UNIQUE (username);

-- 4. Buat index untuk performa query
CREATE INDEX IF NOT EXISTS admin_profiles_username_idx ON admin_profiles (username);

-- Verifikasi hasil
SELECT id, user_id, username, full_name, role, active FROM admin_profiles;
