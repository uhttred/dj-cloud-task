import datetime
from typing import Any, Callable, Union
from functools import cached_property, partial
from google.protobuf import timestamp_pb2 # type: ignore

from django.http.request import HttpRequest
from django.utils.module_loading import import_string

from cloudtask.client import CloudTaskClient
from cloudtask.utils import (
    get_internal_task_path,
    get_encoded_payload)

from cloudtask.configs import (
    DCT_SECRET_HEADER_KEY,
    conf)


class CloudTaskRequest:
    request: Union[HttpRequest, None]
    headers: Union[dict, None]

    def __init__(self,
        request: HttpRequest = None, headers: dict = None) -> None:
        self.request = request
        self.headers = headers


class BaseTask(object):
    __name__: str
    execute: Callable
    path: str


class Task(object):
    
    __task: BaseTask
    __data: dict
    __headers: dict
    __sae: str # service account email
    __client: CloudTaskClient
    __queue: str # cloud task queue name
    __local: bool
    __rq: Any # RQ from cloudtask.worker.RQ
    __rq_handler: Any # RQ task handler
    named: Union[bool, str] # named task to avoid duplicated
    url: str

    def __init__(self, task: BaseTask,
            queue: str = None,
            data: dict = {},
            headers: dict = {},
            url: str = None,
            named: Union[bool, str] = False) -> None:
        self.__task = task
        self.__data = data
        self.__headers = headers
        self.__sae = conf.SAE
        self.__queue = queue or conf.get_default_queue_name()
        self.__local = conf.LOCAL_RQ # running locally
        self.named = named
        self.url = url or conf.get_url()
        self.setup()
    
    def setup(self) -> None:
        if not conf.TESTING:
            if self.__local:
                from cloudtask.worker import RQ, handler
                self.__rq = RQ()
                self.__rq_handler = handler
            else:
                self.__client = CloudTaskClient()
        
    def delay(self) -> None:
        """push task to queue"""
        if conf.TESTING:
            self.execute()
        elif not self.__local:
            self.__enqueue(request={'parent': self.queue_path,
                'task': self.get_http_body()})
        else:
            self.__rq.queue.enqueue(self.__rq_handler,
                url=self.url,
                headers=self.headers,
                data=self.datab64encoded)

    push = delay

    def schedule(self, at: datetime.datetime) -> None:
        """schedule task to run later"""
        if conf.TESTING:
            pass
        elif self.__local:
            self.__rq.scheduler.enqueue_at(at, self.__rq_handler,
                url=self.url,
                headers=self.headers,
                data=self.datab64encoded)
        else:
            timestamp = timestamp_pb2.Timestamp()
            timestamp.FromDatetime(at)
            task = self.get_http_body()
            task['schedule_time'] = timestamp
            self.__enqueue(request={'parent': self.queue_path,
                'task': task})
            
    def __enqueue(self, request: dict):
        """creates task"""
        self.__client.create_task(request=request)

    def execute(self) -> Any:
        """run/execute the task immediately without push to cloud task"""
        return self.__task.execute(
            request=CloudTaskRequest(), **self.data)
    
    # used to run the task function with args from cloud task
    def run(self, request: CloudTaskRequest, **kwargs):
        self.__task.execute(request, **kwargs)
    
    def get_http_body(self) -> dict:
        """retruns the request body for HTTP handlers such Cloud Run"""
        body: dict = {
            'http_request': {
                'http_method': 'POST',
                'url': self.url,
                'headers': self.headers,
                'body': self.datab64encoded,
                'oidc_token': {'service_account_email': self.__sae}}
            }
        if self.named:
            body['name'] = self.task_path
        return body
    
    @property
    def queue(self) -> str:
        return self.__queue
    
    @property
    def datab64encoded(self) -> bytes:
        """returns base64 encoded data"""
        payload: dict = dict(
            path=self.local_task_path, # local task path e.g project.app.tasks.welcome
            data=self.data)
        return get_encoded_payload(payload)
    
    @property
    def data(self) -> dict:
        """return the kwords args passed on task function"""
        return self.__data
    
    @data.setter
    def data(self, data: dict) -> None:
        """only update the data"""
        self.__data.update(data)
    
    @property
    def headers(self) -> dict:
        """returns formatted headers with secret header in it"""
        headers: dict = {}
        for name, value in self.__headers.items():
            headers[name.replace('_', '-').upper()] = value
        if conf.SECRET:
            headers[DCT_SECRET_HEADER_KEY] = conf.SECRET
        headers['Content-Type'] = 'application/json'
        return headers        
    
    @property
    def local_task_path(self) -> str:
        """returns the internal/local task path"""
        return self.__task.path
    
    @property
    def task_path(self) -> str:
        """returns the full task path on google cloud task"""
        name: str = (self.named if self.named and isinstance(self.named, str)
            else self.__task.__name__)
        return self.__client.task_path(
            conf.PROJECT, conf.LOCATION, self.queue, name)
    
    @cached_property
    def queue_path(self) -> str:
        """returns the full queue path on google cloud task"""
        return self.__client.queue_path(
            conf.PROJECT, conf.LOCATION, self.__queue)

    def __call__(self) -> Any:
        """run/execute the task immediately without push to cloud task"""
        return self.execute()


def create_base_task(task: Callable, **kwargs):
    execute = partial(task)
    attrs: dict = dict(
        path=get_internal_task_path(task),
        execute=execute,
        __module__=task.__module__,
        __name__=task.__name__,
        __doc__=task.__doc__)
    attrs.update(kwargs)
    return type(task.__name__, (BaseTask,), attrs)()


def get_task_by_path(path: str) -> Task:
    return import_string(path)()
