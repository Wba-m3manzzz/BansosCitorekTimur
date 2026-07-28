from __future__ import annotations

from fastapi import APIRouter, Depends

from app.dependencies import get_current_admin
from app.schemas.dashboard import DashboardResponse, EvaluasiKRecord, SummaryResponse
from app.services.dashboard_service import DashboardService, get_dashboard_service

router = APIRouter(prefix="", tags=["Dashboard"])


@router.get("/summary", response_model=SummaryResponse)
def summary(
    service: DashboardService = Depends(get_dashboard_service),
    current_admin=Depends(get_current_admin)
):
    return service.get_summary()


@router.get("/dashboard", response_model=DashboardResponse)
def dashboard(
    service: DashboardService = Depends(get_dashboard_service),
    current_admin=Depends(get_current_admin)
):
    return service.get_dashboard()


@router.get("/evaluasi-k", response_model=list[EvaluasiKRecord])
def evaluasi_k(
    service: DashboardService = Depends(get_dashboard_service),
    current_admin=Depends(get_current_admin)
):
    return service.get_evaluasi_k()
