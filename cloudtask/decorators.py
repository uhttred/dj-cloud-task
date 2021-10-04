from functools import wraps
from cloudtask.tasks import Task, create_base_task


def task(queue: str = 'default', **headers):
    def decorator(func):
        base = create_base_task(func)
        @wraps(func)
        def inner(**kwargs) -> Task:
            # returns new task instance
            return Task(base, queue=queue,
                data=kwargs, headers=headers)
        return inner
    return decorator
