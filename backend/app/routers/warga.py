from __future__ import annotations

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status

from app.dependencies import get_current_admin
from app.schemas.warga import WargaCreate, WargaRecord, WargaUpdate, WargaByNikResponse
from app.services.import_service import ImportService, get_import_service
from app.services.warga_service import WargaService, get_warga_service

router = APIRouter(prefix="/warga", tags=["Warga"])


@router.get("", response_model=list[WargaRecord])
def list_warga(
    search: Optional[str] = None,
    status: Optional[str] = None,
    service: WargaService = Depends(get_warga_service),
    current_admin=Depends(get_current_admin)
):
    return service.list_warga(search=search, status=status)


@router.get("/{warga_id}", response_model=WargaRecord)
def get_warga(
    warga_id: str,
    service: WargaService = Depends(get_warga_service),
    current_admin=Depends(get_current_admin)
):
    warga = service.get_warga_by_id(warga_id)
    if warga is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Data warga tidak ditemukan")
    return warga


@router.get("/by-nik/{nik}", response_model=WargaByNikResponse)
def get_warga_by_nik(nik: str, service: WargaService = Depends(get_warga_service)):
    warga = service.get_warga_by_nik(nik)
    if warga is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="NIK warga tidak ditemukan.")
    return WargaByNikResponse(
        id=warga.id,
        nik=warga.nik,
        nama=warga.nama,
        status=warga.status or "Belum Diproses"
    )


@router.get("/by-name/{name}", response_model=WargaByNikResponse)
def get_warga_by_name(name: str, service: WargaService = Depends(get_warga_service)):
    warga = service.get_warga_by_name(name)
    if warga is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Nama warga tidak ditemukan.")
    return WargaByNikResponse(
        id=warga.id,
        nik=warga.nik,
        nama=warga.nama,
        status=warga.status or "Belum Diproses"
    )


@router.post("", response_model=WargaRecord, status_code=status.HTTP_201_CREATED)
def create_warga(
    payload: WargaCreate,
    service: WargaService = Depends(get_warga_service),
    current_admin=Depends(get_current_admin)
):
    try:
        return service.create_warga(payload)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.put("/{warga_id}", response_model=WargaRecord)
def update_warga(
    warga_id: str,
    payload: WargaUpdate,
    service: WargaService = Depends(get_warga_service),
    current_admin=Depends(get_current_admin)
):
    warga = service.update_warga(warga_id, payload)
    if warga is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Data warga tidak ditemukan")
    return warga


@router.delete("/{warga_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_warga(
    warga_id: str,
    service: WargaService = Depends(get_warga_service),
    current_admin=Depends(get_current_admin)
):
    deleted = service.delete_warga(warga_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Data warga tidak ditemukan")
    return None


@router.post("/import/excel")
def import_from_excel(
    file_path: str,
    sheet_name: str | int | None = 0,
    service: ImportService = Depends(get_import_service),
    current_admin=Depends(get_current_admin)
):
    try:
        return service.import_excel(file_path=file_path, sheet_name=sheet_name)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
