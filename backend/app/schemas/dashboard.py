from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from app.schemas.common import CamelModel


class EvaluasiKRecord(CamelModel):
    id: str
    k: int
    accuracy: float
    precision_macro: float
    recall_macro: float
    f1_macro: float
    created_at: Optional[datetime] = None


class SummaryResponse(CamelModel):
    total_warga: int
    layak: int
    tidak_layak: int
    best_k: Optional[int] = None
    accuracy_test: Optional[float] = None
    f1_macro_test: Optional[float] = None


class DistributionItem(CamelModel):
    label: str
    value: int
    share: float


class DashboardResponse(CamelModel):
    summary: SummaryResponse
    status_distribution: List[DistributionItem] = Field(default_factory=list)
    actual_status_distribution: List[DistributionItem] = Field(default_factory=list)
    pendapatan_distribution: List[DistributionItem] = Field(default_factory=list)
    pekerjaan_distribution: List[DistributionItem] = Field(default_factory=list)
    pendidikan_distribution: List[DistributionItem] = Field(default_factory=list)
    kondisi_rumah_distribution: List[DistributionItem] = Field(default_factory=list)


class MetadataOption(CamelModel):
    label: str
    value: str


class ModelMetadataResponse(CamelModel):
    version: Optional[str] = None
    best_k: Optional[int] = None
    features: List[str] = Field(default_factory=list)
    encoding: Dict[str, Any] = Field(default_factory=dict)
    accuracy_test: Optional[float] = None
    f1_macro_test: Optional[float] = None
    artifact_path: Optional[str] = None
    notes: Optional[str] = None
    options: Dict[str, List[str]] = Field(default_factory=dict)
