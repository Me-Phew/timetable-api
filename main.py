import requests
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from config import settings

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


@app.get(settings.BASE_URL, tags=["Docs Redirection"])
def docs_redirection():
    return RedirectResponse(
        f'{settings.BASE_URL}/redoc', status_code=status.HTTP_308_PERMANENT_REDIRECT
    )


@app.get(settings.BASE_URL + "/stops")
def get_stops_data():
    try:
        response = requests.get('https://mpk.nowysacz.pl/jsonStops/stops.json')
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        raise HTTPException(status_code=response.status_code, detail=response.json())

    content = response.json()

    return content
