import os
import sys
from pathlib import Path

# Add backend directory to path so we can import app modules
backend_dir = Path(r"c:\Users\Muhamad Muslih\Desktop\Skripsi Mansur\backend")
sys.path.insert(0, str(backend_dir))

from dotenv import load_dotenv
load_dotenv(dotenv_path=backend_dir / ".env")

from supabase import create_client, Client
from app.services.predictor import get_prediction_engine
from app.schemas.warga import WargaPredictionInput

SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip()
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip()

if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
    print("Error: SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set in .env")
    sys.exit(1)

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
predictor = get_prediction_engine()

def main():
    print("=== Fetching citizens from warga table ===")
    res = supabase.table("warga").select("*").execute()
    warga_list = res.data or []
    print(f"Found {len(warga_list)} warga records to check.")

    corrected_count = 0
    updated_records = []

    for index, warga in enumerate(warga_list):
        nik = warga.get("nik")
        nama = warga.get("nama")
        raw_pendapatan = warga.get("pendapatan")
        old_val = warga.get("pendapatan_nilai")
        
        # Calculate correct income value using our fixed parser
        correct_val = predictor._parse_income_value(raw_pendapatan, None)
        
        # We also need to rerun predictions since the incorrect income value polluted the KNN inputs
        prediction_input = WargaPredictionInput(
            pendapatan=raw_pendapatan or "",
            pendapatan_nilai=correct_val,
            tanggungan=int(warga.get("tanggungan") or 0),
            kondisi_rumah=warga.get("kondisi_rumah") or "",
            pekerjaan=warga.get("pekerjaan") or "",
            pendidikan=warga.get("pendidikan") or "",
            jk=warga.get("jk"),
            hub_kel=warga.get("hub_kel"),
        )
        
        prediction = predictor.predict(prediction_input)
        
        # If income value is different or classification result changed, update it
        # Note: We always update to ensure clean predictions
        is_different = float(old_val or 0) != float(correct_val) or warga.get("status_prediksi") != prediction.status
        
        if is_different:
            corrected_count += 1
            if corrected_count <= 10:
                print(f"Correcting {nama} ({nik}): {raw_pendapatan} -> Old Val: {old_val}, New Val: {correct_val} | Prediction: {warga.get('status_prediksi')} -> {prediction.status}")
        
        # Merge updated columns with the original record to preserve not-null constraints
        updated_warga = dict(warga)
        updated_warga.update({
            "pendapatan_nilai": correct_val,
            "status_prediksi": prediction.status,
            "prediction_code": prediction.prediction_code,
            "probability": prediction.probability,
            "keterangan": prediction.keterangan
        })
        updated_records.append(updated_warga)

    print(f"\nTotal records with corrected values or predictions: {corrected_count}/{len(warga_list)}")
    
    if updated_records:
        print("\nUpdating database in batches of 100...")
        batch_size = 100
        for i in range(0, len(updated_records), batch_size):
            batch = updated_records[i:i+batch_size]
            # We use upsert since we have 'id' and 'nik' to perform updates
            supabase.table("warga").upsert(batch, on_conflict="nik").execute()
            print(f"Successfully updated batch {min(i+batch_size, len(updated_records))}/{len(updated_records)}")
            
    print("\n=== Database fix process completed! ===")

if __name__ == "__main__":
    main()
