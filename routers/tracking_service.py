import json

from fastapi import APIRouter, Depends, HTTPException, status
from redis.commands.json.path import Path

from config import settings
from redis_config import redis_client
from schemas.tracking import TrackingRequest
from stops import get_stops_data
from tracking_service import find_bus, find_stop

router = APIRouter(
    prefix=settings.BASE_URL + "/tracking-service", tags=["Tracking Service"]
)


@router.post('/request-tracking')
def request_tracking(tracking_request: TrackingRequest,
                     stops_data=Depends(get_stops_data)):
    stops_data = stops_data.get('st')

    if not stops_data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail='The stop requested to track was not found')

    stop_to_track = find_stop(stop_num=tracking_request.tracking_info.stop_number,
                              stops_data=stops_data)

    if not stop_to_track:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail='The stop requested to track was not found')

    buses = stop_to_track.get('sd')

    bus_to_track = find_bus(bus_num=tracking_request.tracking_info.bus_number,
                            buses=buses)

    if not bus_to_track:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail='The bus requested to track was not found')

    saved_tracking_data = redis_client.json().get('tracking_list')

    if saved_tracking_data:
        if tracking_request.fcm_token in json.dumps(saved_tracking_data):
            # TODO: Improve?
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail='There already exists a tracking session '
                                       'associated to provided data')

        bus = redis_client.json().get(
            'tracking_list',
            Path(f'$.stops.{tracking_request.tracking_info.stop_number}.buses.'
                 f'{tracking_request.tracking_info.bus_number}'))
        if bus:
            redis_client.json().arrappend(
                'tracking_list',
                Path(f'$.stops.{tracking_request.tracking_info.stop_number}.buses.'
                     f'{tracking_request.tracking_info.bus_number}.fcm_tokens'),
                tracking_request.fcm_token)
        else:
            stop = redis_client.json().get(
                'tracking_list',
                Path(f'$.stops.{tracking_request.tracking_info.stop_number}'))
            if stop:
                redis_client.json().set(
                    'tracking_list',
                    Path(f'$.stops.{tracking_request.tracking_info.stop_number}.'
                         f'buses.{tracking_request.tracking_info.bus_number}'),
                    {
                        'fcm_tokens': [
                            tracking_request.fcm_token,
                        ]
                    })
            else:
                redis_client.json().set(
                    'tracking_list',
                    Path(f'$.stops.{tracking_request.tracking_info.stop_number}'),
                    {
                        'buses': {
                            tracking_request.tracking_info.bus_number: {
                                'fcm_tokens': [
                                    tracking_request.fcm_token,
                                ]
                            }
                        }
                    }
                )
    else:
        tracking_data = {
            'stops': {
                tracking_request.tracking_info.bus_number: {
                    'buses': {
                        tracking_request.tracking_info.bus_number: {
                            "fcm_tokens": [
                                tracking_request.fcm_token,
                            ]
                        }
                    }
                }
            }
        }
        redis_client.json().set('tracking_list', Path.root_path(), tracking_data)

    return {'status': 'ok'}


@router.post('/cancel-tracking')
def cancel_tracking(tracking_request: TrackingRequest):
    fcm_token_index = redis_client.json().arrindex(
        'tracking_list',
        Path(f'.stops.{tracking_request.tracking_info.stop_number}.buses.'
             f'{tracking_request.tracking_info.bus_number}.fcm_tokens'),
        tracking_request.fcm_token)

    print(fcm_token_index)

    if not fcm_token_index:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail='Did not found tracking session associated to '
                                   'provided data')

    fcm_token_index = fcm_token_index[0]

    if fcm_token_index == -1:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail='Did not found tracking session associated to '
                                   'provided data')

    redis_client.json().arrpop(
        'tracking_list',
        Path(f'$.stops.{tracking_request.tracking_info.stop_number}.buses.'
             f'{tracking_request.tracking_info.bus_number}.fcm_tokens'),
        fcm_token_index)

    return {'status': 'ok'}
