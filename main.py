import logging

import uvicorn
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config import settings
from routers import auth, files

logger = logging.getLogger("uvicorn.error")


async def _handle_unexpected_exception(request: Request, exc: Exception) -> JSONResponse:
    request_id = request.headers.get("x-request-id")
    logger.exception(
        "Unhandled exception during request %s %s (x-request-id=%s)",
        request.method,
        request.url.path,
        request_id,
        exc_info=exc,
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": f"Internal Server Error! Request ID: {request_id}",
        },
    )


def create_app() -> FastAPI:
    fast_api_app = FastAPI(
        title="File Manager API",
        docs_url="/docs" if settings.is_debug else None,
        redoc_url="/redoc" if settings.is_debug else None,
        openapi_url="/openapi.json" if settings.is_debug else None,
    )

    @fast_api_app.middleware("http")
    async def catch_unhandled_exceptions(request: Request, call_next):
        try:
            return await call_next(request)
        except Exception as exc:  # pylint: disable=broad-except
            return await _handle_unexpected_exception(request, exc)

    fast_api_app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allow_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["*"],
    )

    fast_api_app.include_router(auth.router)
    fast_api_app.include_router(files.router)
    return fast_api_app


app = create_app()


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
