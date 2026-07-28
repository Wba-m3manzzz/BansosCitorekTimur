from __future__ import annotations

from typing import Optional
from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse

from app.dependencies import get_current_admin
from app.schemas.warga import HasilKlasifikasiResponse
from app.services.export_service import ExportService, get_export_service
from app.services.warga_service import WargaService, get_warga_service

router = APIRouter(prefix="", tags=["Export"])


@router.get("/hasil-klasifikasi", response_model=list[HasilKlasifikasiResponse])
def hasil_klasifikasi(
    search: Optional[str] = None,
    status: Optional[str] = None,
    service: WargaService = Depends(get_warga_service),
    current_admin=Depends(get_current_admin)
):
    rows = service.get_hasil_klasifikasi(search=search, status=status)
    return [
        HasilKlasifikasiResponse(
            id=item.id,
            nik=item.nik,
            nama=item.nama,
            status=item.status or "Tidak Layak",
            keterangan=item.keterangan or ""
        )
        for item in rows
    ]


@router.get("/download/hasil-klasifikasi")
def download_hasil_klasifikasi(
    warga_service: WargaService = Depends(get_warga_service),
    export_service: ExportService = Depends(get_export_service),
    current_admin=Depends(get_current_admin)
):
    rows = [item.model_dump() for item in warga_service.get_hasil_klasifikasi()]
    file_path, filename = export_service.export_to_excel(rows)
    return FileResponse(
        path=str(file_path),
        filename=filename,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
