from __future__ import annotations

import logging
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

from app.db.supabase import get_supabase_service_client
from app.services.predictor import get_prediction_engine

logger = logging.getLogger(__name__)


class ImportService:
    def __init__(self) -> None:
        self.client = get_supabase_service_client()
        self.predictor = get_prediction_engine()

    def _normalize_text(self, value: Any) -> str:
        if value is None:
            return ""
        return " ".join(str(value).strip().split())

    def _find_column(self, frame: pd.DataFrame, candidates: List[str]) -> Optional[str]:
        normalized_map = {self._normalize_text(column).lower(): column for column in frame.columns}
        for candidate in candidates:
            key = self._normalize_text(candidate).lower()
            if key in normalized_map:
                return normalized_map[key]
        return None

    def _value(self, row: pd.Series, *candidates: str, default: Any = None) -> Any:
        for candidate in candidates:
            if candidate in row and pd.notna(row[candidate]):
                value = row[candidate]
                if isinstance(value, str):
                    text = value.strip()
                    if text:
                        return text
                else:
                    return value
        return default

    def _clamp_decimal(
        self,
        value: Decimal,
        min_value: Decimal = Decimal("0.00"),
        max_value: Decimal = Decimal("999999999999.99"),
        scale: int = 2,
    ) -> Decimal:
        if value is None:
            return min_value
        if value < min_value:
            value = min_value
        if value > max_value:
            value = max_value
        exponent = Decimal("1").scaleb(-scale)
        return value.quantize(exponent, rounding=ROUND_HALF_UP)

    def _to_decimal(self, value: Any) -> Decimal:
        if value is None or (isinstance(value, float) and pd.isna(value)):
            return Decimal("0.00")
        if isinstance(value, Decimal):
            return self._clamp_decimal(value)
        if isinstance(value, (int, float)):
            try:
                return self._clamp_decimal(Decimal(str(value)))
            except InvalidOperation:
                return Decimal("0.00")

        val_str = str(value).strip().replace(" ", "")

        income_map = {
            "<500.000": Decimal("400000.00"),
            "500.000": Decimal("500000.00"),
            "500.000-1.000.000": Decimal("750000.00"),
            "1.000.000-2.000.000": Decimal("1500000.00"),
            "2.000.000-4.000.000": Decimal("3000000.00"),
            ">4.000.000": Decimal("4500000.00"),
            # Also support without dots
            "<500000": Decimal("400000.00"),
            "500000": Decimal("500000.00"),
            "500000-1000000": Decimal("750000.00"),
            "1000000-2000000": Decimal("1500000.00"),
            "2000000-4000000": Decimal("3000000.00"),
            ">4000000": Decimal("4500000.00"),
        }

        # Check in mapping first
        if val_str in income_map:
            return self._clamp_decimal(income_map[val_str])
        
        # Clean Rp/dots/commas
        text = val_str.lower().replace("rp", "").replace(".", "").replace(",", ".")
        
        # Check in mapping again after cleaning Rp
        if text in income_map:
            return self._clamp_decimal(income_map[text])

        # If it's a range like "1000000-2000000", handle it
        if "-" in text:
            parts = text.split("-")
            if len(parts) == 2:
                try:
                    p1 = "".join(ch for ch in parts[0] if ch.isdigit() or ch == ".")
                    p2 = "".join(ch for ch in parts[1] if ch.isdigit() or ch == ".")
                    if p1 and p2:
                        val = (Decimal(p1) + Decimal(p2)) / 2
                        return self._clamp_decimal(val)
                except (InvalidOperation, ValueError, ZeroDivisionError):
                    pass

        digits = "".join(ch for ch in text if ch.isdigit() or ch == ".")
        if digits:
            try:
                return self._clamp_decimal(Decimal(digits))
            except InvalidOperation:
                pass

        return Decimal("0.00")

    def _to_float(self, value: Any) -> float:
        return float(self._to_decimal(value))

    def _safe_int(self, value: Any, min_value: int = 0, max_value: int = 99999) -> int:
        if value is None or (isinstance(value, float) and pd.isna(value)):
            return min_value
        try:
            result = int(value)
        except (TypeError, ValueError):
            try:
                result = int(float(value))
            except (TypeError, ValueError):
                return min_value
        if result < min_value:
            return min_value
        if result > max_value:
            return max_value
        return result

    def _normalize_sheet_name(self, sheet_name: str | int | None) -> str | int | None:
        if isinstance(sheet_name, str):
            stripped = sheet_name.strip()
            if stripped.isdigit():
                return int(stripped)
            return stripped or 0
        return sheet_name

    def _predict(self, record: Dict[str, Any]) -> Dict[str, Any]:
        prediction_input = {
            "pendapatan": record.get("pendapatan"),
            "pendapatan_nilai": record.get("pendapatan_nilai") or 0,
            "tanggungan": record.get("tanggungan") or 0,
            "kondisi_rumah": record.get("kondisi_rumah") or "",
            "pekerjaan": record.get("pekerjaan") or "",
            "pendidikan": record.get("pendidikan") or "",
            "jk": record.get("jk"),
            "hub_kel": record.get("hub_kel"),
        }
        result = self.predictor.predict(prediction_input)
        return {
            "status_prediksi": result.status,
            "prediction_code": result.prediction_code,
            "probability": result.probability,
            "keterangan": result.keterangan,
        }

    def _map_row(self, row: pd.Series) -> Dict[str, Any]:
        mapping = {
            "nik": self._value(row, "NIK", "nik"),
            "nama": self._value(row, "Nama", "nama"),
            "pendapatan": self._value(row, "Pendapatan", "pendapatan"),
            "pendapatan_nilai": self._to_float(
                self._value(
                    row,
                    "Pendapatan_Nilai",
                    "pendapatan_nilai",
                    default=self._value(row, "Pendapatan", "pendapatan"),
                )
            ),
            "tanggungan": self._safe_int(self._value(row, "Jumlah_Tanggungan", "tanggungan", default=0)),
            "kondisi_rumah": self._value(row, "Kondisi_Rumah", "kondisi_rumah"),
            "pekerjaan": self._value(row, "Pekerjaan", "pekerjaan"),
            "pendidikan": self._value(row, "Pendidikan", "pendidikan"),
            "jk": self._value(row, "JK", "jk"),
            "hub_kel": self._value(row, "Hub_Kel", "hub_kel"),
            "status_aktual": self._value(row, "Status_Kelayakan", "status_aktual"),
        }
        mapping.update(self._predict(mapping))
        return mapping

    def import_excel(self, file_path: str | Path, sheet_name: str | int | None = 0) -> Dict[str, Any]:
        source = Path(file_path)
        if not source.exists():
            raise FileNotFoundError(f"File Excel tidak ditemukan: {source}")

        normalized_sheet_name = self._normalize_sheet_name(sheet_name)
        frame = pd.read_excel(source, sheet_name=normalized_sheet_name)
        rows = []
        failed = 0
        details: List[Dict[str, Any]] = []

        for index, row in frame.iterrows():
            try:
                mapped = self._map_row(row)
                if not mapped.get("nik"):
                    raise ValueError("NIK kosong atau tidak tersedia")
                rows.append(mapped)
                details.append({"row": int(index) + 1, "status": "ok", "nik": mapped.get("nik")})
            except Exception as exc:
                failed += 1
                logger.exception("Baris Excel gagal dipetakan pada indeks %s", index)
                details.append({"row": int(index) + 1, "status": "failed", "error": str(exc)})

        if not rows:
            return {"imported": 0, "updated": 0, "failed": failed, "details": details}

        unique_rows: Dict[str, Dict[str, Any]] = {}
        duplicate_count = 0
        for row in rows:
            nik = str(row.get("nik")).strip()
            if nik in unique_rows:
                duplicate_count += 1
                logger.warning("Duplicate NIK dalam batch import, memilih baris terbaru: %s", nik)
            unique_rows[nik] = row

        if duplicate_count:
            details.append({
                "row": "batch",
                "status": "warning",
                "message": f"{duplicate_count} baris duplikat NIK diabaikan; baris terakhir dipilih per NIK",
            })

        deduped_rows = list(unique_rows.values())
        response = self.client.table("warga").upsert(deduped_rows, on_conflict="nik").execute()
        imported = len(response.data or deduped_rows)
        return {
            "imported": imported,
            "updated": imported,
            "failed": failed,
            "details": details,
        }


def get_import_service() -> ImportService:
    return ImportService()