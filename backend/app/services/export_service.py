from __future__ import annotations

import json
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple

import pandas as pd


class ExportService:
    def __init__(self, export_dir: str | None = None) -> None:
        base_dir = Path(export_dir) if export_dir else Path(tempfile.gettempdir()) / "bansos_exports"
        base_dir.mkdir(parents=True, exist_ok=True)
        self.export_dir = base_dir

    def build_dataframe(self, rows: List[Dict[str, Any]]) -> pd.DataFrame:
        if not rows:
            return pd.DataFrame(
                columns=[
                    "id",
                    "nik",
                    "nama",
                    "pendapatan",
                    "tanggungan",
                    "kondisi_rumah",
                    "pekerjaan",
                    "pendidikan",
                    "jk",
                    "hub_kel",
                    "status_kelayakan",
                    "keterangan",
                    "created_at",
                    "updated_at",
                ]
            )
        frame = pd.DataFrame(rows)
        excluded_columns = {"pendapatan_nilai", "status_aktual"}
        frame = frame.drop(columns=[column for column in excluded_columns if column in frame.columns])

        if "status" in frame.columns:
            frame["status_kelayakan"] = frame["status"]
        elif "status_prediksi" in frame.columns:
            frame["status_kelayakan"] = frame["status_prediksi"]

        frame = frame.drop(columns=[column for column in ["status", "status_prediksi"] if column in frame.columns])

        preferred_columns = [
            "id",
            "nik",
            "nama",
            "pendapatan",
            "tanggungan",
            "kondisi_rumah",
            "pekerjaan",
            "pendidikan",
            "jk",
            "hub_kel",
            "prediction_code",
            "probability",
            "status_kelayakan",
            "keterangan",
            "created_at",
            "updated_at",
        ]
        columns = [column for column in preferred_columns if column in frame.columns] + [
            column for column in frame.columns if column not in preferred_columns
        ]
        return self._sanitize_for_excel(frame.loc[:, columns])

    def _sanitize_value_for_excel(self, value: Any) -> Any:
        if isinstance(value, datetime):
            return value.replace(tzinfo=None) if value.tzinfo else value
        if isinstance(value, (dict, list)):
            return json.dumps(value, ensure_ascii=False)
        return value

    def _sanitize_for_excel(self, dataframe: pd.DataFrame) -> pd.DataFrame:
        sanitized = dataframe.copy()

        for column in sanitized.columns:
            if pd.api.types.is_datetime64tz_dtype(sanitized[column]):
                sanitized[column] = sanitized[column].dt.tz_localize(None)
            else:
                sanitized[column] = sanitized[column].map(self._sanitize_value_for_excel)

        return sanitized

    def export_to_excel(self, rows: List[Dict[str, Any]], filename_prefix: str = "hasil_klasifikasi") -> Tuple[Path, str]:
        dataframe = self.build_dataframe(rows)
        filename = f"{filename_prefix}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.xlsx"
        file_path = self.export_dir / filename
        with pd.ExcelWriter(file_path, engine="openpyxl") as writer:
            dataframe.to_excel(writer, index=False, sheet_name="Hasil Klasifikasi")
        return file_path, filename


def get_export_service() -> ExportService:
    return ExportService()
