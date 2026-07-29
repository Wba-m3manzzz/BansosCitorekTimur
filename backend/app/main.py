from __future__ import annotations

import logging
from logging.config import dictConfig
from typing import Any, Dict

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.db.supabase import SupabaseNotConfiguredError, ping_supabase
from app.routers.auth import router as auth_router
from app.routers.chat import router as chat_router
from app.routers.dashboard import router as dashboard_router
from app.routers.export import router as export_router
from app.routers.predict import router as predict_router
from app.routers.warga import router as warga_router
from app.services.predictor import get_prediction_engine


def configure_logging() -> None:
    dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {
                    "format": "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
                }
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "formatter": "default",
                }
            },
            "root": {
                "level": settings.LOG_LEVEL.upper(),
                "handlers": ["console"],
            },
        }
    )


configure_logging()
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    description="FastAPI backend for the Bansos classification system using Supabase and KNN model artifacts.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix=settings.API_PREFIX)
app.include_router(chat_router, prefix=settings.API_PREFIX)
app.include_router(warga_router, prefix=settings.API_PREFIX)
app.include_router(dashboard_router, prefix=settings.API_PREFIX)
app.include_router(predict_router, prefix=settings.API_PREFIX)
app.include_router(export_router, prefix=settings.API_PREFIX)


@app.on_event("startup")
def startup_event() -> None:
    logger.info("Starting %s in %s mode", settings.APP_NAME, settings.APP_ENV)
    try:
        get_prediction_engine().ready
    except Exception:
        logger.exception("Prediction engine warm-up failed")


@app.get("/api/health")
def health() -> Dict[str, Any]:
    db_status: Dict[str, Any]
    try:
        db_ping = ping_supabase()
        db_status = {"status": "connected", **db_ping}
    except SupabaseNotConfiguredError as exc:
        db_status = {"status": "not_configured", "error": str(exc)}
    except Exception as exc:
        db_status = {"status": "error", "error": str(exc)}

    predictor = get_prediction_engine()
    model_status = {
        "ready": predictor.ready,
        "model_path": settings.MODEL_PATH,
        "metadata_path": settings.MODEL_METADATA_PATH,
    }

    api_status = "ok" if db_status.get("status") == "connected" and model_status["ready"] else "degraded"
    return {
        "status": api_status,
        "app_name": settings.APP_NAME,
        "environment": settings.APP_ENV,
        "database": db_status,
        "model": model_status,
    }


@app.exception_handler(SupabaseNotConfiguredError)
def supabase_not_configured_handler(_: Request, exc: SupabaseNotConfiguredError):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": str(exc)},
    )


@app.exception_handler(ValueError)
def value_error_handler(_: Request, exc: ValueError):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": str(exc)},
    )


@app.exception_handler(RuntimeError)
def runtime_error_handler(_: Request, exc: RuntimeError):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": str(exc)},
    )


@app.exception_handler(HTTPException)
def http_exception_handler(_: Request, exc: HTTPException):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
