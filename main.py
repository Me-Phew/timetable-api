from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from config import settings
from routers import stops, tracking_service

app = FastAPI(
    docs_url=settings.BASE_URL + "/docs",
    redoc_url=settings.BASE_URL + "/redoc",
    openapi_url=settings.BASE_URL + "/openapi.json",
    title=settings.API_TITLE,
    version=settings.API_VERSION,
)

ALLOWED_ORIGINS = [
    "*",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(stops.router)
app.include_router(tracking_service.router)


@app.get(settings.BASE_URL, tags=["Docs Redirection"])
def docs_redirection() -> RedirectResponse:
    return RedirectResponse(
        f'{settings.BASE_URL}/redoc', status_code=status.HTTP_308_PERMANENT_REDIRECT
    )
