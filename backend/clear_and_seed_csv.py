import os
import pandas as pd
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip()
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip()

if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
    print("Error: SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set in .env")
    exit(1)

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)


def clear_and_seed():
    csv_path = "data/hasil_prediksi_penduduk.csv"
    if not os.path.exists(csv_path):
        print(f"Error: {csv_path} not found.")
        return

    print(f"Reading NIK list from {csv_path}...")
    df = pd.read_csv(csv_path)

    seen_nik = set()
    for _, row in df.iterrows():
        nik_str = str(row["NIK"]).strip()
        if nik_str.endswith(".0"):
            nik_str = nik_str[:-2]
        if nik_str:
            seen_nik.add(nik_str)

    nik_list = list(seen_nik)
    print(f"Found {len(nik_list)} unique NIKs to clear and seed.")

    # 1. Delete existing records from the warga table by NIK in batches
    print("Deleting existing records matching CSV NIKs from 'warga' table...")
    batch_size = 100
    deleted_count = 0
    for i in range(0, len(nik_list), batch_size):
        batch = nik_list[i:i+batch_size]
        try:
            # Delete query where nik is in the batch list
            res = supabase.table("warga").delete().in_("nik", batch).execute()
            deleted_count += len(res.data or [])
        except Exception as e:
            print(f"Error deleting batch {i}: {e}")

    print(f"Successfully deleted existing records.")

    # 2. Seed data
    print("Seeding new data into 'warga' table...")
    rows = []
    inserted_niks = set()
    for _, row in df.iterrows():
        nik_str = str(row["NIK"]).strip()
        if nik_str.endswith(".0"):
            nik_str = nik_str[:-2]

        if not nik_str or nik_str in inserted_niks:
            continue

        inserted_niks.add(nik_str)

        status_actual = str(row.get("Status_Kelayakan", "")).strip()
        status_pred = str(row.get("Prediksi_Kelayakan", "")).strip() or status_actual

        prob = {
            "Layak": 1.0 if status_pred == "Layak" else 0.0,
            "Tidak Layak": 1.0 if status_pred == "Tidak Layak" else 0.0
        }
        keter = "Prioritas menerima bantuan sosial." if status_pred == "Layak" else "Belum memenuhi kriteria bantuan sosial."

        rows.append({
            "nik": nik_str,
            "nama": str(row["Nama"]).strip(),
            "pendapatan": str(row.get("Pendapatan", "")),
            "pendapatan_nilai": float(row["Pendapatan_Nilai"]) if pd.notna(row.get("Pendapatan_Nilai")) else 0.0,
            "tanggungan": int(row["Jumlah_Tanggungan"]) if pd.notna(row.get("Jumlah_Tanggungan")) else 0,
            "kondisi_rumah": str(row.get("Kondisi_Rumah", "")),
            "pekerjaan": str(row.get("Pekerjaan", "")),
            "pendidikan": str(row.get("Pendidikan", "")),
            "jk": str(row.get("JK", "")) if pd.notna(row.get("JK")) else None,
            "hub_kel": str(row.get("Hub_Kel", "")) if pd.notna(row.get("Hub_Kel")) else None,
            "status_aktual": status_actual if pd.notna(row.get("Status_Kelayakan")) else None,
            "status_prediksi": status_pred,
            "prediction_code": int(row["Prediksi_Kelayakan_Kode"]) if pd.notna(row.get("Prediksi_Kelayakan_Kode")) else 0,
            "probability": prob,
            "keterangan": keter
        })

    # Insert batch by batch
    for i in range(0, len(rows), batch_size):
        batch = rows[i:i+batch_size]
        supabase.table("warga").upsert(batch, on_conflict="nik").execute()
        print(f"Successfully seeded batch {min(i+batch_size, len(rows))}/{len(rows)}")

    print("Clear and seed process completed successfully!")


if __name__ == "__main__":
    clear_and_seed()
