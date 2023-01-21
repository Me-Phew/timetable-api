from pydantic import BaseModel


class TrackingInfo(BaseModel):
    stop_number: int
    bus_number: int


class TrackingRequest(BaseModel):
    fcm_token: str
    tracking_info: TrackingInfo
