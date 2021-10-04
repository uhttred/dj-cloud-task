import datetime
from typing import Callable
from functools import partial
from django.utils.module_loading import import_string

from cloudtask.utils import (
    get_task_path_name,
    get_encoded_payload)
from cloudtask.configurations import conf


class BaseTask(object):
    execute: Callable
    path: str


class Task(object):
    
    __queue_path: str
    __task: BaseTask
    __data: dict
    __headers: dict
    __sae: str # service account email
    queue: str # cloud task queue name
    url: str

    def __init__(self, task: BaseTask,
            queue: str,
            data: dict = {},
            headers: dict = {},
            url: str = None,
            service_account_email: str = None) -> None:
        self.__task = task
        self.__data = data
        self.__headers = headers
        self.__sae = service_account_email or conf.SAE
        self.queue = queue
        self.url = url or conf.URL
    
    def setup(self) -> None:
        """makes basic validations and setup the task"""
        pass

    def delay(self) -> None:
        """push task to queue"""
        pass

    push = delay

    def schedule(self, at: datetime.datetime) -> None:
        """schedule task to run later"""
        pass

    def execute(self) -> None:
        """runs/execute the task"""
        pass
    
    def get_http_body(self) -> dict:
        """retruns the request body for HTTP handlers such Cloud Run"""
        body = dict(
            task=dict(
                httpRequest=dict(
                    httpMethod='POST',
                    url=self.url,
                    headers=self.headers,
                    body=self.datab64encoded))
                )
        if self.__sae:
            body['task']['httpRequest']['oidcToken'] = dict(
                service_account_email=self.__sae)
        return body

    @property
    def datab64encoded(self) -> bytes:
        """returns base64 encoded data"""
        payload: dict = dict(
            path=self.path, # internal task path e.g project.app.tasks.welcome
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
        """returns formatted header with secret header in it"""
        pass
    
    @property
    def path(self) -> str:
        """returns the internal task path name"""
        return self.__task.path
    
    @property
    def queue_path(self) -> str:
        """returns the full queue path on google cloud task"""
        pass
    
    def __enqueue(self) -> None:
        """Enqueue the task on cloud run"""
        pass

    def __call__(self) -> None:
        self.__task.execute(request=None, **self.data)


def create_base_task(task: Callable, **kwargs):
    execute = partial(task)
    attrs: dict = dict(
        path=get_task_path_name(task),
        execute=execute,
        __module__=task.__module__,
        __name__=task.__name__,
        __doc__=task.__doc__)
    attrs.update(kwargs)
    return type(task.__name__, (BaseTask,), attrs)()


def get_task_by_path(path: str):
    return import_string(path)
