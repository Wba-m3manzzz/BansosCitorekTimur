from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from app.schemas.common import CamelModel


class PredictRequest(CamelModel):
    nik: Optional[str] = None
    nama: Optional[str] = None
    pendapatan: Any = None
    tanggungan: int = Field(ge=0)
    kondisi_rumah: str = Field(min_length=1)
    pekerjaan: str = Field(min_length=1)
    pendidikan: str = Field(min_length=1)


class PredictResponse(CamelModel):
    status: str
    keterangan: str


class BulkProcessResponse(CamelModel):
    status: str
    processed: int
    message: str
