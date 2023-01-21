import asyncio
import datetime
import logging
import sys
import time

import pytz
from redis.commands.json.path import Path

from fcm_manager import create_message, send_messages
from redis_config import redis_client
from stops import get_stops_data

tracking_logger = logging.getLogger('tracking_task')
tracking_logger.addHandler(logging.StreamHandler(sys.stdout))
tracking_logger.setLevel(logging.DEBUG)

tz_warsaw = pytz.timezone('Europe/Warsaw')


def find_stop(*,
              stop_num: int,
              stops_data: dict) -> None | dict:
    found_stop = None

    for stop in stops_data:
        if int(stop['nr']) == stop_num:
            found_stop = stop
            break

    return found_stop


def find_bus(*,
             bus_num: int,
             buses: list) -> None | dict:
    found_bus = None

    for bus in buses:
        if int(bus['li']) == bus_num:
            found_bus = bus
            break

    return found_bus


def update_bus_eta(*, stop_num: int, bus_num: int) -> int | None:
    stops_data = get_stops_data().get('st')

    if not stops_data:
        return None

    tracked_stop = find_stop(stop_num=stop_num,
                             stops_data=stops_data)

    if not tracked_stop:
        return None

    buses = tracked_stop.get('sd')

    if not buses:
        return None

    tracked_bus = find_bus(bus_num=bus_num,
                           buses=buses)

    if not tracked_bus:
        return None

    departure = tracked_bus.get('de')

    if not departure:
        return None

    if ':' in departure:
        departure_time = departure.split(':')
        hour = int(departure_time[0])
        minute = int(departure_time[1])

        warsaw_now = datetime.datetime.now(tz_warsaw)

        # TODO: Fix edge case

        departure_time = datetime.datetime.now().replace(
            hour=hour,
            minute=minute,
            tzinfo=warsaw_now.tzinfo,
        )

        difference = departure_time - warsaw_now
        difference = difference.total_seconds() / 60

        eta = int(difference)
    elif '>>' in departure:
        eta = 0
    else:
        eta = int(departure.split('min')[0])

    redis_client.json().set('tracking_list',
                            Path(f'$.stops.{stop_num}.buses.{bus_num}.eta'),
                            eta)
    redis_client.json().set('tracking_list',
                            Path(f'$.stops.{stop_num}.buses.{bus_num}.eta_updated'),
                            time.time())

    return eta


def remove_bus(*, stop_num: int, bus_num: int) -> None:
    redis_client.json().delete('tracking_list',
                               Path(f'$.stops.{stop_num}.buses.{bus_num}'))


def remove_stop(stop_num: int) -> None:
    redis_client.json().delete('tracking_list', Path(f'$.stops.{stop_num}'))


async def tracking_task():
    tracking_logger.info('Running tracking task')
    start_time = time.time()
    tracking_list = redis_client.json().get('tracking_list')

    if tracking_list:
        for stop_num, stop in tracking_list['stops'].items():
            stop_num = int(stop_num)

            buses = stop['buses']
            if not buses:
                remove_stop(stop_num)

            for bus_num, bus in stop['buses'].items():
                bus_num = int(bus_num)

                bus_fcm_tokens = bus.get('fcm_tokens')

                tracking_logger.debug(f'Bus: {bus_num}, fcm_tokens: {bus_fcm_tokens}')

                if not bus_fcm_tokens:
                    remove_bus(stop_num=stop_num, bus_num=bus_num)

                bus_eta = bus.get('eta')

                if bus_eta:
                    last_updated = float(bus['eta_updated'])
                    time_since_update = time.time() - last_updated

                    if time_since_update > 60:
                        bus_eta = update_bus_eta(stop_num=stop_num, bus_num=bus_num)
                else:
                    bus_eta = update_bus_eta(stop_num=stop_num, bus_num=bus_num)

                if bus_eta is None:
                    remove_bus(stop_num=stop_num, bus_num=bus_num)
                else:
                    if (bus_eta < 30 and bus_eta % 10 == 0) or (
                            bus_eta <= 15 and bus_eta % 5 == 0):
                        if bus_eta == 0:
                            title = 'Bus is leaving NOW >>>'
                        else:
                            title = f'ETA: {bus_eta} minutes'

                        messages = []

                        for fcm_token in bus_fcm_tokens:
                            message = create_message(title=title,
                                                     message=f'Tracking bus number '
                                                             f'{bus_num}',
                                                     fcm_token=fcm_token)
                            messages.append(message)

                        if messages:
                            tracking_logger.info(f'Sending {len(messages)} messages')
                            # Separate messages into 500 sized chunks
                            # to comply with fcm limitation of 500 messages per batch
                            message_chunks = [messages[x:x + 500] for x in
                                              range(0, len(messages), 500)]

                            for message_chunk in message_chunks:
                                asyncio.create_task(send_messages(message_chunk))
                    else:
                        tracking_logger.info(f'Skipping send (eta {bus_eta})')

    tracking_logger.debug(f'Tracking task finished in {time.time() - start_time}')
