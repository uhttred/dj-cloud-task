import requests
from redis import Redis
from rq import Queue, Worker
from rq_scheduler import Scheduler

from cloudtask.configs import  (
    WORKER_QUEUE_NAME,
    conf)


class RQ:
    """
    RQ for local development support
    """
    worker: Worker
    queue: Queue
    scheduler: Scheduler
    connection: Redis
    queue_name: str = WORKER_QUEUE_NAME

    def __init__(self) -> None:
        self.connection = Redis() if not conf.LOCAL_RQ_URL else Redis.from_url(conf.LOCAL_RQ_URL)
        self.queue = Queue(self.queue_name, connection=self.connection)
        self.scheduler = Scheduler(self.queue_name, connection=self.connection)
        self.worker = Worker([self.queue], connection=self.connection)


def handler(data: bytes, url: str, headers: dict) -> None:
    """
    Simulates Cloud Task call to handle tasks locally
    """
    with requests.post(url=url, headers=headers,
        data=data) as r:
        pass
