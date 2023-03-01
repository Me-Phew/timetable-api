import apscheduler.job
import pytz
from apscheduler.jobstores.redis import RedisJobStore
from apscheduler.schedulers.background import BackgroundScheduler

from config import settings
from tracking_service import tracking_task

scheduler = BackgroundScheduler()


def configure_and_start_scheduler() -> apscheduler.job.Job:
    if not scheduler.running:
        jobstores = {"default": RedisJobStore(host=settings.REDIS_HOSTNAME,
                                              port=settings.REDIS_PORT,
                                              password=settings.REDIS_PASSWORD)}

        scheduler.configure(
            jobstores=jobstores, timezone=pytz.timezone("Europe/Warsaw")
        )

        scheduler.start()

        tracking_job = scheduler.add_job(tracking_task,
                                         'interval',
                                         seconds=30,
                                         # minutes=1,
                                         id='tracking_job',
                                         max_instances=1,
                                         replace_existing=True)

        return tracking_job
