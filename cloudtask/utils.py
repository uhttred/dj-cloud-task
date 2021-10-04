from typing import Callable

def get_task_path_name(func: Callable) -> str:
    return '.'.join((func.__module__, func.__name__))