import os
import json
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


def seed_evaluasi_k():
    csv_path = "data/evaluasi_nilai_k.csv"
    if not os.path.exists(csv_path):
        print(f"Warning: {csv_path} not found. Skipping evaluasi_k seed.")
        return
        
    print("Seeding evaluasi_k table...")
    df = pd.read_csv(csv_path)
    
    rows = []
    for _, row in df.iterrows():
        rows.append({
            "k": int(row["K"]),
            "accuracy": float(row["Accuracy"]),
            "precision_macro": float(row["Precision_Macro"]),
            "recall_macro": float(row["Recall_Macro"]),
            "f1_macro": float(row["F1_Macro"])
        })
        
    if rows:
        supabase.table("evaluasi_k").upsert(rows, on_conflict="k").execute()
        print(f"Successfully seeded {len(rows)} rows into evaluasi_k.")


def seed_model_metadata():
    json_path = "models/model_metadata.json"
    if not os.path.exists(json_path):
        print(f"Warning: {json_path} not found. Skipping model_metadata seed.")
        return
        
    print("Seeding model_metadata table...")
    with open(json_path, "r", encoding="utf-8") as f:
        meta = json.load(f)
        
    response = supabase.table("model_metadata").select("id").limit(1).execute()
    existing = response.data
    
    row = {
        "version": "1.0.0",
        "best_k": int(meta.get("best_k", 7)),
        "features": meta.get("features", []),
        "encoding": meta.get("encoding", {}),
        "accuracy_test": float(meta.get("accuracy_test", 0.0)),
        "f1_macro_test": float(meta.get("f1_macro_test", 0.0)),
        "artifact_path": "models/model_knn_bansos.joblib",
        "notes": "Initial imported metadata from model_metadata.json"
    }
    
    if existing:
        row["id"] = existing[0]["id"]
        
    supabase.table("model_metadata").upsert([row]).execute()
    print("Successfully seeded model_metadata.")


def seed_warga():
    csv_path = "data/hasil_prediksi_penduduk.csv"
    if not os.path.exists(csv_path):
        print(f"Warning: {csv_path} not found. Skipping warga seed.")
        return
        
    print("Seeding warga table...")
    df = pd.read_csv(csv_path)
    
    seen_nik = set()
    rows = []
    for _, row in df.iterrows():
        nik_str = str(row["NIK"]).strip()
        if nik_str.endswith(".0"):
            nik_str = nik_str[:-2]
            
        if not nik_str or nik_str in seen_nik:
            continue
            
        seen_nik.add(nik_str)
            
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
        
    print(f"Parsed {len(rows)} warga records. Sending to Supabase in batches of 100...")
    batch_size = 100
    for i in range(0, len(rows), batch_size):
        batch = rows[i:i+batch_size]
        supabase.table("warga").upsert(batch, on_conflict="nik").execute()
        print(f"Successfully upserted batch {min(i+batch_size, len(rows))}/{len(rows)}")


def main():
    print("=== Supabase Python Seeding Started ===")
    try:
        seed_evaluasi_k()
        seed_model_metadata()
        seed_warga()
        print("=== Seeding Finished Successfully! ===")
    except Exception as exc:
        print(f"Error during seeding: {exc}")
        exit(1)


if __name__ == "__main__":
    main()
