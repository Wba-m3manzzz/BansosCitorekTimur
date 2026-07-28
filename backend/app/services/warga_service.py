from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from app.db.supabase import get_supabase_service_client
from app.schemas.warga import WargaCreate, WargaPredictionInput, WargaRecord, WargaUpdate
from app.services.predictor import get_prediction_engine

logger = logging.getLogger(__name__)


class WargaService:
    DB_COLUMNS = {
        "id",
        "nik",
        "nama",
        "pendapatan",
        "pendapatan_nilai",
        "tanggungan",
        "kondisi_rumah",
        "pekerjaan",
        "pendidikan",
        "jk",
        "hub_kel",
        "status_aktual",
        "status_prediksi",
        "prediction_code",
        "probability",
        "keterangan",
        "created_at",
        "updated_at",
    }

    def __init__(self) -> None:
        self.client = get_supabase_service_client()
        self.predictor = get_prediction_engine()

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def _filter_db_columns(self, data: Dict[str, Any]) -> Dict[str, Any]:
        return {key: value for key, value in data.items() if key in self.DB_COLUMNS}

    def _normalize_payload(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        cleaned = {key: value for key, value in payload.items() if value is not None}
        
        # If pendapatan_nilai is missing but pendapatan is present, try parsing it
        if ("pendapatan_nilai" not in cleaned or cleaned["pendapatan_nilai"] is None) and "pendapatan" in cleaned:
            cleaned["pendapatan_nilai"] = self.predictor._parse_income_value(str(cleaned["pendapatan"]), None)
            
        if "pendapatan_nilai" in cleaned and cleaned["pendapatan_nilai"] is not None:
            try:
                cleaned["pendapatan_nilai"] = float(cleaned["pendapatan_nilai"])
            except (TypeError, ValueError):
                cleaned["pendapatan_nilai"] = 0.0
        if "tanggungan" in cleaned and cleaned["tanggungan"] is not None:
            try:
                cleaned["tanggungan"] = int(cleaned["tanggungan"])
            except (TypeError, ValueError):
                cleaned["tanggungan"] = 0
        return cleaned

    def _payload_for_prediction(self, data: Dict[str, Any]) -> WargaPredictionInput:
        return WargaPredictionInput(
            pendapatan=str(data.get("pendapatan") or ""),
            pendapatan_nilai=data.get("pendapatan_nilai") or 0,
            tanggungan=int(data.get("tanggungan") or 0),
            kondisi_rumah=str(data.get("kondisi_rumah") or ""),
            pekerjaan=str(data.get("pekerjaan") or ""),
            pendidikan=str(data.get("pendidikan") or ""),
            jk=data.get("jk"),
            hub_kel=data.get("hub_kel"),
        )

    def _attach_prediction(self, data: Dict[str, Any]) -> Dict[str, Any]:
        prediction = self.predictor.predict(self._payload_for_prediction(data))
        return {
            **data,
            "status_prediksi": prediction.status,
            "prediction_code": prediction.prediction_code,
            "probability": prediction.probability,
            "keterangan": prediction.keterangan,
        }

    def _row_to_record(self, row: Dict[str, Any]) -> WargaRecord:
        data = dict(row)
        if "status_prediksi" in data:
            data["status"] = data["status_prediksi"]
        return WargaRecord(**data)

    def list_warga(self, search: Optional[str] = None, status: Optional[str] = None) -> List[WargaRecord]:
        query = self.client.table("warga").select("*")
        if search:
            query = query.or_(f"nama.ilike.%{search}%,nik.ilike.%{search}%")
        if status and status != "Semua":
            query = query.eq("status_prediksi", status)
            
        response = query.order("updated_at", desc=True).execute()
        return [self._row_to_record(item) for item in response.data or []]

    def get_warga_by_id(self, warga_id: str) -> Optional[WargaRecord]:
        response = self.client.table("warga").select("*").eq("id", warga_id).limit(1).execute()
        items = response.data or []
        if not items:
            return None
        return self._row_to_record(items[0])

    def get_warga_by_nik(self, nik: str) -> Optional[WargaRecord]:
        response = self.client.table("warga").select("*").eq("nik", nik).limit(1).execute()
        items = response.data or []
        if not items:
            return None
        return self._row_to_record(items[0])

    def get_warga_by_name(self, name: str) -> Optional[WargaRecord]:
        cleaned_name = name.strip()
        if not cleaned_name:
            return None

        exact_response = (
            self.client.table("warga")
            .select("*")
            .ilike("nama", cleaned_name)
            .limit(1)
            .execute()
        )
        exact_items = exact_response.data or []
        if exact_items:
            return self._row_to_record(exact_items[0])

        partial_response = (
            self.client.table("warga")
            .select("*")
            .ilike("nama", f"%{cleaned_name}%")
            .order("updated_at", desc=True)
            .limit(1)
            .execute()
        )
        partial_items = partial_response.data or []
        if not partial_items:
            return None
        return self._row_to_record(partial_items[0])

    def create_warga(self, payload: WargaCreate) -> WargaRecord:
        data = self._normalize_payload(payload.model_dump(mode="json"))
        data["id"] = str(uuid4())
        data["created_at"] = self._now()
        data["updated_at"] = self._now()
        db_data = self._filter_db_columns(data)
        response = self.client.table("warga").insert(db_data).execute()
        items = response.data or []
        if not items:
            created = self.get_warga_by_id(data["id"])
            if created is None:
                raise RuntimeError("Gagal menyimpan data warga")
            return created
        return self._row_to_record(items[0])

    def update_warga(self, warga_id: str, payload: WargaUpdate) -> Optional[WargaRecord]:
        existing = self.get_warga_by_id(warga_id)
        if existing is None:
            return None
        update_data = self._normalize_payload(payload.model_dump(mode="json", exclude_unset=True))
        if not update_data:
            update_data = {}
        update_data["updated_at"] = self._now()
        db_data = self._filter_db_columns(update_data)
        response = self.client.table("warga").update(db_data).eq("id", warga_id).execute()
        items = response.data or []
        if not items:
            updated = self.get_warga_by_id(warga_id)
            if updated is None:
                raise RuntimeError("Gagal memperbarui data warga")
            return updated
        return self._row_to_record(items[0])

    def delete_warga(self, warga_id: str) -> bool:
        self.client.table("warga").delete().eq("id", warga_id).execute()
        return True

    def process_warga(self, warga_id: str) -> Optional[WargaRecord]:
        existing = self.get_warga_by_id(warga_id)
        if existing is None:
            return None

        payload = existing.model_dump(mode="json")
        merged = self._attach_prediction(payload)
        merged["updated_at"] = self._now()
        db_data = self._filter_db_columns(merged)
        response = self.client.table("warga").update(db_data).eq("id", warga_id).execute()
        items = response.data or []
        if not items:
            processed = self.get_warga_by_id(warga_id)
            if processed is None:
                raise RuntimeError("Gagal memproses data warga")
            return processed
        return self._row_to_record(items[0])

    def process_all(self) -> Dict[str, Any]:
        warga_list = self.list_warga()
        processed = len(warga_list)
        updated = 0
        failed = 0
        details: List[Dict[str, Any]] = []

        for warga in warga_list:
            try:
                payload = warga.model_dump(mode="json")
                merged = self._attach_prediction(payload)
                merged["updated_at"] = self._now()
                db_data = self._filter_db_columns(merged)
                response = self.client.table("warga").update(db_data).eq("id", warga.id).execute()
                if response.data:
                    updated += 1
                    details.append(
                        {
                            "id": warga.id,
                            "status_prediksi": merged["status_prediksi"],
                            "prediction_code": merged["prediction_code"],
                        }
                    )
                else:
                    failed += 1
            except Exception as exc:
                logger.exception("Failed processing warga %s", warga.id)
                failed += 1
                details.append({"id": warga.id, "error": str(exc)})

        return {
            "processed": processed,
            "updated": updated,
            "failed": failed,
            "details": details,
        }

    def get_hasil_klasifikasi(self, search: Optional[str] = None, status: Optional[str] = None) -> List[WargaRecord]:
        rows = self.list_warga(search=search, status=status)
        return [row for row in rows if str(row.status or "").strip().lower() in {"layak", "tidak layak"}]


def get_warga_service() -> WargaService:
    return WargaService()
