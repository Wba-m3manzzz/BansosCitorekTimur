from __future__ import annotations

from collections import Counter
from typing import Any, Dict, List

from app.db.supabase import get_supabase_service_client
from app.schemas.dashboard import DashboardResponse, DistributionItem, EvaluasiKRecord, SummaryResponse
from app.services.predictor import get_prediction_engine


class DashboardService:
    def __init__(self) -> None:
        self.client = get_supabase_service_client()
        self.predictor = get_prediction_engine()

    def _fetch_warga(self) -> List[Dict[str, Any]]:
        response = self.client.table("warga").select("*").order("updated_at", desc=True).execute()
        return response.data or []

    def _fetch_evaluasi_k(self) -> List[Dict[str, Any]]:
        response = self.client.table("evaluasi_k").select("*").order("k", desc=False).execute()
        return response.data or []

    def get_summary(self) -> SummaryResponse:
        warga = self._fetch_warga()
        evaluasi = self._fetch_evaluasi_k()
        total = len(warga)
        layak = sum(1 for item in warga if str(item.get("status_prediksi", "")).strip().lower() == "layak")
        tidak_layak = sum(1 for item in warga if str(item.get("status_prediksi", "")).strip().lower() in {"tidak layak", "tidak_layak"})
        
        # Sort K evaluations to find the best K (highest accuracy)
        best_k = None
        accuracy_test = None
        f1_macro_test = None
        
        if evaluasi:
            # Sort by accuracy descending to find the best metrics
            sorted_eval = sorted(evaluasi, key=lambda x: float(x.get("accuracy") or 0), reverse=True)
            best_row = sorted_eval[0]
            best_k = best_row.get("k")
            accuracy_test = float(best_row.get("accuracy")) if best_row.get("accuracy") is not None else None
            f1_macro_test = float(best_row.get("f1_macro")) if best_row.get("f1_macro") is not None else None
            
        metadata = self.predictor.get_metadata()
        
        return SummaryResponse(
            total_warga=total,
            layak=layak,
            tidak_layak=tidak_layak,
            best_k=best_k or metadata.get("best_k"),
            accuracy_test=accuracy_test or metadata.get("accuracy_test"),
            f1_macro_test=f1_macro_test or metadata.get("f1_macro_test"),
        )

    def get_dashboard(self) -> DashboardResponse:
        warga = self._fetch_warga()
        summary = self.get_summary()

        status_dist = self._build_distribution(warga, "status_prediksi")
        actual_dist = self._build_distribution(warga, "status_aktual")
        pekerjaan_dist = self._build_distribution(warga, "pekerjaan")
        pendidikan_dist = self._build_distribution(warga, "pendidikan")
        kondisi_dist = self._build_distribution(warga, "kondisi_rumah")
        pendapatan_dist = self._build_income_distribution(warga)

        return DashboardResponse(
            summary=summary,
            status_distribution=status_dist,
            actual_status_distribution=actual_dist,
            pendapatan_distribution=pendapatan_dist,
            pekerjaan_distribution=pekerjaan_dist,
            pendidikan_distribution=pendidikan_dist,
            kondisi_rumah_distribution=kondisi_dist,
        )

    def get_evaluasi_k(self) -> List[EvaluasiKRecord]:
        return [EvaluasiKRecord(**item) for item in self._fetch_evaluasi_k()]

    def _build_distribution(self, items: List[Dict[str, Any]], field_name: str) -> List[DistributionItem]:
        total = len(items)
        counter: Counter[str] = Counter()
        for item in items:
            value = item.get(field_name)
            label = str(value).strip() if value is not None and str(value).strip() else "Tidak Diketahui"
            
            # Normalize status labels
            if field_name in {"status_prediksi", "status_aktual"}:
                if label.lower() == "layak":
                    label = "Layak"
                elif label.lower() in {"tidak layak", "tidak_layak", "tidal layak"}:
                    label = "Tidak Layak"
                    
            counter[label] += 1
            
        results = []
        for label, count in counter.most_common():
            share = round(count / total, 3) if total > 0 else 0.0
            results.append(DistributionItem(label=label, value=count, share=share))
        return results

    def _build_income_distribution(self, items: List[Dict[str, Any]]) -> List[DistributionItem]:
        total = len(items)
        counter = {
            "< Rp 500.000": 0,
            "Rp 500.000 - Rp 1.000.000": 0,
            "Rp 1.000.000 - Rp 2.000.000": 0,
            "Rp 2.000.000 - Rp 4.000.000": 0,
            "> Rp 4.000.000": 0,
        }
        for item in items:
            val = item.get("pendapatan_nilai")
            if val is None:
                txt = item.get("pendapatan")
                try:
                    val = self.predictor._parse_income_value(txt, None)
                except Exception:
                    val = 0.0
            
            try:
                num = float(val)
            except (TypeError, ValueError):
                num = 0.0
                
            if num < 500000:
                counter["< Rp 500.000"] += 1
            elif num <= 1000000:
                counter["Rp 500.000 - Rp 1.000.000"] += 1
            elif num <= 2000000:
                counter["Rp 1.000.000 - Rp 2.000.000"] += 1
            elif num <= 4000000:
                counter["Rp 2.000.000 - Rp 4.000.000"] += 1
            else:
                counter["> Rp 4.000.000"] += 1
                
        results = []
        order = [
            "< Rp 500.000",
            "Rp 500.000 - Rp 1.000.000",
            "Rp 1.000.000 - Rp 2.000.000",
            "Rp 2.000.000 - Rp 4.000.000",
            "> Rp 4.000.000",
        ]
        for label in order:
            count = counter[label]
            share = round(count / total, 3) if total > 0 else 0.0
            results.append(DistributionItem(label=label, value=count, share=share))
        return results


def get_dashboard_service() -> DashboardService:
    return DashboardService()
