from __future__ import annotations

import json
import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import DBAPIError, OperationalError

from app.core.config import settings
from app.core.errors import AppError
from app.core.logging import configure_logging
from app.routes.market_updates import router as market_updates_router
from app.routes.stocks import router as stocks_router
from app.routes.v1 import router as v1_router


configure_logging(settings.log_level)
logger = logging.getLogger("app")

app = FastAPI(
    title="StoxScoop API",
    version="1.0.0",
    description="Backend for tracking stock market events and event batches.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(AppError)
def app_error_handler(_: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": exc.code, "message": exc.message}},
    )


@app.exception_handler(OperationalError)
@app.exception_handler(DBAPIError)
def db_error_handler(_: Request, exc: Exception) -> JSONResponse:
    if settings.app_env == "local":
        logger.exception("Database error (local env — full traceback): %s", exc)
    return JSONResponse(
        status_code=503,
        content={"error": {"code": "db_unavailable", "message": "Database unavailable. Please retry."}},
    )


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "env": settings.app_env}


@app.middleware("http")
async def log_json_payload(request: Request, call_next):  # type: ignore[no-untyped-def]
    content_type = request.headers.get("content-type", "")
    if "application/json" in content_type:
        body_bytes = await request.body()
        if body_bytes:
            max_len = 50_000
            body_text = body_bytes.decode("utf-8", errors="replace")
            if len(body_text) > max_len:
                body_text = body_text[:max_len] + "...(truncated)"
            try:
                body_json = json.loads(body_text)
            except json.JSONDecodeError:
                body_json = body_text

            logger.info("Request payload: %s %s body=%s", request.method, request.url.path, body_json)

        async def receive() -> dict[str, object]:
            return {"type": "http.request", "body": body_bytes, "more_body": False}

        request = Request(request.scope, receive)

    return await call_next(request)


@app.exception_handler(RequestValidationError)
def validation_exception_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
    logger.warning("Validation error: %s", exc.errors())
    return JSONResponse(status_code=422, content={"detail": exc.errors()})


app.include_router(stocks_router)
app.include_router(v1_router)
app.include_router(market_updates_router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.app_env == "local",
    )
