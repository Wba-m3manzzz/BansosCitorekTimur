from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field
from app.schemas.common import CamelModel


class WargaCreate(CamelModel):
    nik: str = Field(min_length=1)
    nama: str = Field(min_length=1)
    pendapatan: Any = None
    tanggungan: int = Field(ge=0)
    kondisi_rumah: str = Field(min_length=1)
    pekerjaan: str = Field(min_length=1)
    pendidikan: str = Field(min_length=1)
    jk: Optional[str] = None
    hub_kel: Optional[str] = None
    status_aktual: Optional[str] = None


class WargaUpdate(CamelModel):
    nik: Optional[str] = None
    nama: Optional[str] = None
    pendapatan: Optional[Any] = None
    tanggungan: Optional[int] = Field(default=None, ge=0)
    kondisi_rumah: Optional[str] = None
    pekerjaan: Optional[str] = None
    pendidikan: Optional[str] = None
    jk: Optional[str] = None
    hub_kel: Optional[str] = None
    status_aktual: Optional[str] = None


class WargaPredictionInput(CamelModel):
    pendapatan: Any = None
    pendapatan_nilai: Optional[Decimal] = Field(default=None, ge=0)
    tanggungan: int = Field(ge=0)
    kondisi_rumah: str = Field(min_length=1)
    pekerjaan: str = Field(min_length=1)
    pendidikan: str = Field(min_length=1)
    jk: Optional[str] = None
    hub_kel: Optional[str] = None


class PredictionProbability(CamelModel):
    tidak_layak: float = 0.0
    layak: float = 0.0


class PredictionResult(CamelModel):
    status: str
    prediction_code: int
    probability: Dict[str, float]
    keterangan: str
    features_used: List[float] = Field(default_factory=list)


class WargaRecord(CamelModel):
    id: str
    nik: str
    nama: str
    pendapatan: Optional[Any] = None
    pendapatan_nilai: Optional[Decimal] = None
    tanggungan: int
    kondisi_rumah: str
    pekerjaan: str
    pendidikan: str
    jk: Optional[str] = None
    hub_kel: Optional[str] = None
    status_aktual: Optional[str] = None
    status: Optional[str] = None  # maps to status_prediksi
    keterangan: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class WargaListResponse(CamelModel):
    items: List[WargaRecord]
    total: int


class ProcessAllResponse(CamelModel):
    processed: int
    updated: int
    failed: int
    details: List[Dict[str, Any]]


class WargaByNikResponse(CamelModel):
    id: str
    nik: str
    nama: str
    status: str


class HasilKlasifikasiResponse(CamelModel):
    id: str
    nik: str
    nama: str
    status: str
    keterangan: str
