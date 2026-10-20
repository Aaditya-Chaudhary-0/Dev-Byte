from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError, OperationalError, SQLAlchemyError
from starlette.requests import Request

from app.api.api import api_router
from app.core.config import settings

logger = logging.getLogger(__name__)
cors_origins = [origin.strip() for origin in settings.cors_origins.split(",") if origin.strip()]

app = FastAPI(
    title=settings.app_name,
    version="unversioned",
    description="DEV BYTE API foundation for local development.",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type", "Accept"],
)

app.include_router(api_router, prefix=settings.api_prefix)


@app.exception_handler(IntegrityError)
async def handle_integrity_error(request: Request, exc: IntegrityError) -> JSONResponse:
    logger.info("Request rejected by a database constraint on %s", request.url.path)
    return JSONResponse(
        status_code=409,
        content={"detail": "The request conflicts with existing data"},
    )


@app.exception_handler(OperationalError)
async def handle_database_unavailable(request: Request, exc: OperationalError) -> JSONResponse:
    logger.error("Database unavailable while handling %s", request.url.path)
    return JSONResponse(
        status_code=503,
        content={"detail": "Database service is unavailable"},
    )


@app.exception_handler(SQLAlchemyError)
async def handle_database_error(request: Request, exc: SQLAlchemyError) -> JSONResponse:
    logger.error("Database operation failed while handling %s", request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": "Database operation failed"},
    )


@app.get("/health", tags=["health"], summary="Application health check")
async def health_check() -> dict[str, str]:
    return {"status": "ok", "service": "DEV BYTE API"}


@app.get("/", tags=["meta"])
async def root() -> dict[str, str]:
    return {"message": "DEV BYTE API is running"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
