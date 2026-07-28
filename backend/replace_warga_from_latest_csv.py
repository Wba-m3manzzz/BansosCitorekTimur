import os
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path
from typing import Any

import pandas as pd
from dotenv import load_dotenv
from supabase import Client, create_client


ROOT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_CSV_PATH = Path(r"C:\Users\ManZzz\OneDrive - untirta.ac.id\Desktop\MANSUR\backend\data\Data_Penduduk.csv")
BATCH_SIZE = 100


def normalize_text(value: Any) -> str | None:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    text = " ".join(str(value).strip().split())
    return text or None


def normalize_nik(value: Any) -> str:
    text = str(value).strip()
    if text.endswith(".0"):
        text = text[:-2]
    return text


def clamp_decimal(value: Decimal) -> Decimal:
    if value < Decimal("0.00"):
        value = Decimal("0.00")
    if value > Decimal("999999999999.99"):
        value = Decimal("999999999999.99")
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def income_to_decimal(value: Any) -> Decimal:
    text = normalize_text(value)
    if not text:
        return Decimal("0.00")

    income_map = {
        "<500.000": Decimal("400000.00"),
        "500.000": Decimal("500000.00"),
        "500.000-1.000.000": Decimal("750000.00"),
        "1.000.000-2.000.000": Decimal("1500000.00"),
        "2.000.000-4.000.000": Decimal("3000000.00"),
        ">4.000.000": Decimal("4500000.00"),
    }
    compact = text.replace(" ", "")
    if compact in income_map:
        return income_map[compact]

    cleaned = compact.lower().replace("rp", "").replace(".", "").replace(",", ".")
    if "-" in cleaned:
        parts = cleaned.split("-")
        if len(parts) == 2:
            try:
                return clamp_decimal((Decimal(parts[0]) + Decimal(parts[1])) / 2)
            except (InvalidOperation, ValueError):
                pass

    try:
        return clamp_decimal(Decimal(cleaned))
    except InvalidOperation:
        return Decimal("0.00")


def normalize_status(value: Any) -> str | None:
    text = normalize_text(value)
    if not text:
        return None
    mapping = {
        "layak": "Layak",
        "tidak layak": "Tidak Layak",
        "tidal layak": "Tidak Layak",
    }
    return mapping.get(text.lower(), text)


def load_client() -> Client:
    load_dotenv(ROOT_DIR / ".env")
    load_dotenv()

    supabase_url = os.getenv("SUPABASE_URL", "").strip()
    service_role_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip()
    if not supabase_url or not service_role_key:
        raise RuntimeError("SUPABASE_URL dan SUPABASE_SERVICE_ROLE_KEY harus tersedia di .env backend.")

    return create_client(supabase_url, service_role_key)


def clear_warga_table(client: Client) -> int:
    deleted = 0
    while True:
        response = client.table("warga").select("id").limit(BATCH_SIZE).execute()
        rows = response.data or []
        if not rows:
            break

        ids = [row["id"] for row in rows if row.get("id")]
        if not ids:
            break

        client.table("warga").delete().in_("id", ids).execute()
        deleted += len(ids)
        print(f"Menghapus data lama: {deleted} baris")

    return deleted


def build_rows(csv_path: Path) -> list[dict[str, Any]]:
    frame = pd.read_csv(csv_path)
    required_columns = {
        "NIK",
        "Nama",
        "Pendidikan",
        "Pekerjaan",
        "Jumlah_Tanggungan",
        "Pendapatan",
        "Kondisi_Rumah",
        "Status_Kelayakan",
    }
    missing = required_columns.difference(frame.columns)
    if missing:
        raise ValueError(f"Kolom wajib tidak ditemukan pada CSV: {sorted(missing)}")

    rows: list[dict[str, Any]] = []
    seen_nik: set[str] = set()
    for index, row in frame.iterrows():
        nik = normalize_nik(row["NIK"])
        if not nik:
            raise ValueError(f"NIK kosong pada baris CSV ke-{index + 2}")
        if nik in seen_nik:
            raise ValueError(f"NIK duplikat pada CSV: {nik}")
        seen_nik.add(nik)

        rows.append(
            {
                "nik": nik,
                "nama": normalize_text(row["Nama"]) or "",
                "pendapatan": normalize_text(row["Pendapatan"]),
                "pendapatan_nilai": float(income_to_decimal(row["Pendapatan"])),
                "tanggungan": int(row["Jumlah_Tanggungan"]),
                "kondisi_rumah": normalize_text(row["Kondisi_Rumah"]) or "",
                "pekerjaan": normalize_text(row["Pekerjaan"]) or "",
                "pendidikan": normalize_text(row["Pendidikan"]) or "",
                "jk": normalize_text(row.get("JK")),
                "hub_kel": normalize_text(row.get("Hub_Kel")),
                "status_aktual": normalize_status(row.get("Status_Kelayakan")),
                "status_prediksi": None,
                "prediction_code": None,
                "probability": {},
                "keterangan": None,
            }
        )

    return rows


def seed_warga_table(client: Client, rows: list[dict[str, Any]]) -> int:
    inserted = 0
    for start in range(0, len(rows), BATCH_SIZE):
        batch = rows[start : start + BATCH_SIZE]
        client.table("warga").upsert(batch, on_conflict="nik").execute()
        inserted += len(batch)
        print(f"Memasukkan data baru: {inserted}/{len(rows)} baris")
    return inserted


def main() -> None:
    csv_path = Path(os.getenv("DATA_PENDUDUK_CSV", DEFAULT_CSV_PATH))
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV dataset terbaru tidak ditemukan: {csv_path}")

    print(f"Membaca dataset terbaru: {csv_path}")
    rows = build_rows(csv_path)
    print(f"Total data valid dari CSV: {len(rows)} baris")

    client = load_client()
    deleted = clear_warga_table(client)
    inserted = seed_warga_table(client, rows)

    print("Selesai mengganti dataset warga.")
    print(f"Data lama dihapus : {deleted}")
    print(f"Data baru masuk   : {inserted}")
    print("Catatan: hasil klasifikasi sengaja dikosongkan. Jalankan proses klasifikasi dari halaman web.")


if __name__ == "__main__":
    main()
