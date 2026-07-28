from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.dependencies import get_current_admin
from app.schemas.dashboard import ModelMetadataResponse
from app.schemas.predict import BulkProcessResponse, PredictRequest, PredictResponse
from app.services.predictor import PredictionEngine, get_prediction_engine
from app.services.warga_service import WargaService, get_warga_service

router = APIRouter(prefix="", tags=["Predict"])


@router.get("/metadata", response_model=ModelMetadataResponse)
def metadata(predictor: PredictionEngine = Depends(get_prediction_engine)):
    metadata_info = predictor.get_metadata()
    return ModelMetadataResponse(**metadata_info)


@router.post("/predict", response_model=PredictResponse)
def predict(payload: PredictRequest, predictor: PredictionEngine = Depends(get_prediction_engine)):
    prediction = predictor.predict(payload)
    return PredictResponse(
        status=prediction.status,
        keterangan=prediction.keterangan
    )


@router.post("/process-all", response_model=BulkProcessResponse)
def process_all(
    service: WargaService = Depends(get_warga_service),
    current_admin=Depends(get_current_admin)
):
    result = service.process_all()
    return BulkProcessResponse(
        status="success",
        processed=result.get("processed", 0),
        message="Berhasil memproses ulang perhitungan klasifikasi seluruh data warga."
    )


@router.post("/process-warga/{warga_id}")
def process_warga(
    warga_id: str,
    service: WargaService = Depends(get_warga_service),
    current_admin=Depends(get_current_admin)
):
    warga = service.process_warga(warga_id)
    if warga is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Data warga tidak ditemukan")
    return warga
