from fastapi import APIRouter, Depends

from config import settings
from stops import get_stops_data

router = APIRouter(
    prefix=settings.BASE_URL + "/stops", tags=["Stops"]
)


@router.get('')
def get_stops_data(stops_data=Depends(get_stops_data)):
    return stops_data
