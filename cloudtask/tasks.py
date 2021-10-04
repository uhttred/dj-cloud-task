from typing import Callable
from functools import partial
from cloudtask.utils import get_task_path_name
from django.utils.module_loading import import_string


class BaseTask(object):
    execute: Callable
    path: str


class Task(object):
    
    __queue_path: str
    __task: BaseTask
    __data: dict
    __headers: dict
    queue: str

    def __init__(self, task: BaseTask, queue: str, data: dict = {},
        headers: dict = {}) -> None:
        self.__task = task
        self.__data = data
        self.__headers = headers
        self.queue = queue
    
    def setup(self) -> None:
        """makes basic validations abd setup the task"""
        pass

    def delay(self) -> None:
        """push task to queue"""
        pass

    push = delay

    def execute(self) -> None:
        """runs/execute the task"""
        pass
    
    def get_http_body(self) -> dict:
        """retruns the request body for HTTP handlers such Cloud Run"""
        pass

    def datab64(self) -> str:
        """returns raw base64 encoded data"""
        pass

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
