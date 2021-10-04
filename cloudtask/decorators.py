from functools import wraps
from cloudtask.tasks import Task, create_base_task


def task(queue: str, url: str = None, headers: dict = {}):
    def decorator(func):
        base = create_base_task(func)
        @wraps(func)
        def inner(**kwargs) -> Task:
            return Task(base, queue=queue,
                data=kwargs, headers=headers, url=url)
        return inner
    return decorator
