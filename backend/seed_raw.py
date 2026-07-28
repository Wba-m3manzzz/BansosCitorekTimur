import os
import pandas as pd
from dotenv import load_dotenv
from supabase import create_client, Client
from app.services.import_service import ImportService

# Load environment variables
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip()
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip()

if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
    print("Error: SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set in .env")
    exit(1)

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)


def seed_raw_csv():
    csv_path = "data/Data_Penduduk.csv"
    if not os.path.exists(csv_path):
        print(f"Error: {csv_path} not found.")
        return

    print(f"Reading raw data from {csv_path}...")
    df = pd.read_csv(csv_path)

    # Use the same logic as ImportService to ensure compatibility with model predictions
    import_service = ImportService()

    rows = []
    seen_nik = set()

    for index, row in df.iterrows():
        try:
            # Map row using ImportService logic (which handles NIK, name, predictions, etc.)
            mapped = import_service._map_row(row)
            nik_str = str(mapped.get("nik")).strip()
            
            if not nik_str or nik_str in seen_nik:
                continue
                
            seen_nik.add(nik_str)
            rows.append(mapped)
        except Exception as e:
            print(f"Error parsing row {index}: {e}")

    print(f"Parsed {len(rows)} valid warga records. Inserting into Supabase in batches...")
    
    batch_size = 100
    for i in range(0, len(rows), batch_size):
        batch = rows[i:i+batch_size]
        supabase.table("warga").upsert(batch, on_conflict="nik").execute()
        print(f"Successfully upserted batch {min(i+batch_size, len(rows))}/{len(rows)}")

    print("Seeding raw CSV data completed successfully!")


if __name__ == "__main__":
    seed_raw_csv()
