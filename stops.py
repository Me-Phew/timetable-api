import time

import requests
from fastapi import HTTPException, status
from redis.commands.json.path import Path

from redis_config import redis_client


def fetch_stops_data() -> dict:
    try:
        response = requests.get('https://mpk.nowysacz.pl/jsonStops/stops.json', verify='mpk-nowysacz-pl-chain.pem')
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=str(e))
    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        raise HTTPException(status_code=response.status_code,
                            detail=response.json())

    data = response.json()
    redis_client.json().set("stops", Path.root_path(), data)
    redis_client.set("stops_updated", time.time())
    return data


def get_stops_data() -> dict:
    saved_data = redis_client.json().get("stops")
    if saved_data:
        last_updated = float(redis_client.get("stops_updated"))
        time_since_update = time.time() - last_updated

        if time_since_update < 60:
            # If data was updated within the past minute, return it
            return saved_data
        else:
            return fetch_stops_data()
    else:
        return fetch_stops_data()
