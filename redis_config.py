import redis

from config import settings

redis_client = redis.Redis(host=settings.REDIS_HOSTNAME,
                           port=settings.REDIS_PORT,
                           password=settings.REDIS_PASSWORD)
