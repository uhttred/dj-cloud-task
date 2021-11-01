from typing import Union
from functools import wraps
from cloudtask.tasks import Task, create_base_task


def task(queue: str = None, named: Union[bool, str] = False, url: str = None, headers: dict = {}):
    def decorator(func):
        base = create_base_task(func)
        @wraps(func)
        def inner(**kwargs) -> Task:
            return Task(base, queue=queue, named=named,
                data=kwargs, headers=headers, url=url)
        return inner
    return decorator
