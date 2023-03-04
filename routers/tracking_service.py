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
            stops = saved_tracking_data['stops']

            for stop_id, buses in stops.items():
                for bus_id, tracking_data in buses['buses'].items():
                    fcm_tokens = tracking_data['fcm_tokens']

                    if tracking_request.fcm_token in fcm_tokens:
                        if (
                                tracking_request.tracking_info.stop_number == stop_id
                                and tracking_request.tracking_info.bus_number == bus_id
                        ):
                            return {'status': 'ok'}
                        else:
                            fcm_tokens_filtered = [
                                [fcm_token for fcm_token in fcm_tokens if
                                 fcm_token != tracking_request.fcm_token]
                            ]
                            if fcm_tokens_filtered:
                                redis_client.json().set(
                                    'tracking_list',
                                    Path(
                                        f'$.stops.'
                                        f'{tracking_request.tracking_info.stop_number}.'
                                        f'buses.'
                                        f'{tracking_request.tracking_info.bus_number}'),
                                    {
                                        'fcm_tokens': fcm_tokens_filtered
                                    })
                            else:
                                redis_client.json().delete(
                                    'tracking_list',
                                    Path(
                                        f'$.stops.'
                                        f'{tracking_request.tracking_info.stop_number}.'
                                        f'buses.'
                                        f'{tracking_request.tracking_info.bus_number}')
                                )

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
    fcm_tokens = redis_client.json().get(
        'tracking_list',
        Path(f'.stops.{tracking_request.tracking_info.stop_number}.buses.'
             f'{tracking_request.tracking_info.bus_number}.fcm_tokens'))

    if not fcm_tokens:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail='Did not find tracking session associated to '
                                   'provided data')

    fcm_token_index = None

    for index, fcm_token in enumerate(fcm_tokens):
        if fcm_token == tracking_request.fcm_token:
            fcm_token_index = index
            break

    redis_client.json().arrpop(
        'tracking_list',
        Path(f'$.stops.{tracking_request.tracking_info.stop_number}.buses.'
             f'{tracking_request.tracking_info.bus_number}.fcm_tokens'),
        fcm_token_index)

    return {'status': 'ok'}


@router.get('/active-session/{fcm_token}')
def get_active_tracking_session(fcm_token: str):
    saved_tracking_data = redis_client.json().get('tracking_list')
    print(saved_tracking_data)

    if saved_tracking_data:
        if fcm_token in json.dumps(saved_tracking_data):
            stops = saved_tracking_data['stops']

            for stop_id, buses in stops.items():
                for bus_id, tracking_data in buses['buses'].items():
                    fcm_tokens = tracking_data['fcm_tokens']

                    if fcm_token in fcm_tokens:
                        return {
                            'stop_number': stop_id,
                            'bus_number': bus_id,
                        }

    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                        detail='Did not find an active tracking session associated to '
                               'provided token')
