import datetime
from typing import Callable
from functools import cached_property, partial
from django.utils.module_loading import import_string

from cloudtask.client import CloudTaskClient, client
from cloudtask.utils import (
    get_internal_task_path,
    get_encoded_payload)

from cloudtask.configurations import (
    DCT_SECRET_HEADER_NAME,
    conf)


class BaseTask(object):
    execute: Callable
    path: str


class Task(object):
    
    __task: BaseTask
    __data: dict
    __headers: dict
    __sae: str # service account email
    __client: CloudTaskClient = client
    __queue: str # cloud task queue name
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
        self.__queue = queue
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
        body: dict = {
            # 'name': self.task_path,
            'http_request': {
                'http_method': 'POST',
                'url': self.url,
                'headers': self.headers,
                'body': self.datab64encoded}
            }
        if self.__sae:
            body['http_request']['oidc_token'] = {
                'service_account_email': self.__sae}
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
        headers: dict
        for name, value in self.__headers.items():
            headers[name.replace('_', '-').upper()] = value
        headers[DCT_SECRET_HEADER_NAME] = conf.SECRET
        headers['Content-Type'] = 'application/json'
        return headers        
    
    @property
    def local_task_path(self) -> str:
        """returns the internal/local task path"""
        return self.__task.path
    
    # @cached_property
    # def task_path(self) -> str:
    #     """returns the full task path on google cloud task"""
    #     return self.__client.task_path(
    #         conf.PROJECT, conf.LOCATION, self.queue, self.__task.path)
    
    @cached_property
    def queue_path(self) -> str:
        """returns the full queue path on google cloud task"""
        return self.__client.queue_path(
            conf.PROJECT, conf.LOCATION, self.__queue)
    
    def __enqueue(self) -> None:
        """Enqueue the task on cloud run"""
        pass

    def __call__(self) -> None:
        self.__task.execute(request=None, **self.data)


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


def get_task_by_path(path: str):
    return import_string(path)
