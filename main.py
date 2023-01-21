from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi_utils.tasks import repeat_every

from config import settings
from routers import stops, tracking_service
from tracking_service import tracking_logger, tracking_task

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


@app.on_event('startup')
@repeat_every(seconds=60, logger=tracking_logger)
async def run_tracking_task() -> None:
    await tracking_task()


@app.get(settings.BASE_URL, tags=["Docs Redirection"])
def docs_redirection() -> RedirectResponse:
    return RedirectResponse(
        f'{settings.BASE_URL}/redoc', status_code=status.HTTP_308_PERMANENT_REDIRECT
    )
