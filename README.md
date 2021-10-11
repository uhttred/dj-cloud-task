# Django Cloud Task Queue

Integrate your [Django](https://www.djangoproject.com/) application with Google [Cloud Task](https://cloud.google.com/tasks) from [Google Cloud Platform](https://cloud.google.com/). This package provides a simple and easy to use decorator to push tasks to Cloud Task Queue and automatically handle all income task execution requests from Cloud Task. In a single entry point.

At the moment dj-cloud-task only works with HTTP targets such as Cloud Run, Cloud Functions, Compute Engine, ... (in case you are using Google Cloud Platform infrastructure). See the Cloud Task documentation about targets for more [here](https://cloud.google.com/tasks/docs/creating-http-target-tasks)!

### Some Features

* Easily push tasks to Cloud Task using a decorator
* Automatically route all tasks from a single endpoint
* Ease scheduling with native python datetime
* Named task to avoid duplicated
* Local development support (coming soon...)

### Installation

At this moment this package is only available here in Github, you can install it directly from this repository using pip. Later will be available on PyPI.

```sh
pip install -e git+https://github.com/txiocoder/dj-cloud-task.git@main#egg=cloudtask
```

#### Requirements

* Python >= 3.9
* django >= 3.2.*
* google-cloud-tasks >= 2.5.*

These are the officially supported python and packages versions. Other versions will probably work

## Quickstart

### Configure

As stated above, Django Cloud Task is a Django Application. To configure your project you simply need to add ``cloudtask`` to your ``INSTALLED_APPS`` and configure the ``CLOUDTASK`` variable in the ``settings.py`` file. More details about how to configure the CLOUDTASK variable below.

In file ``settings.py``:

```python
INSTALLED_APPS: list = [
    'cloudtask',
]

CLOUDTASK: dict = {
    'PROJECT': 'project',
    'LOCATION': 'europe-west6',
    'SAE': 'user@project.iam.gserviceaccount.com',
    'URL': 'https://handler.com/_tasks/',
    'QUEUE': 'default',
    'SECRET': 'my-very-secrete-key'
}
```

Then, add ``cloudtask.urls`` to your URL configuration to route and handle all task execution requests coming from Cloud Task.

In your ``project.urls``:

```python
from django.urls import path, include

urlpatterns: list = [
    path('_tasks/', include('cloudtask.urls'))
]
```

### Create Tasks

The tasks are simple python functions that could be defined anywhere. But, I suggest you create a file with the name ``tasks.py`` in your django module/app and declare there. To create a task, simply decorate a function with ``cloudtask.decorators.task``. See the example below: 

```python
from cloudtask import (
    CloudTaskRequest,
    task)

@task(queue='default')
def add(request: CloudTaskRequest, a: int = 5, b: int = 4) -> None:
    print(f'Running task with args {a=} and {b=}')
    print(a + b)
```

### Run Tasks

To send a task to Cloud Task call the task function and then call the delay method inside the returned task instance. This will send a request to Cloud Task to enqueue the task and Cloud Task will request to run it as fast as possible.

```python
from .tasks import add

add(a=10, b=30).delay()
# or use the alias push
add(a=30, b=10).push()
```

## GCP Authentication

This module requires to be authenticated with Google Cloud Platform as a service. The GC Platform provides various ways to authenticate with it. See the GC Platform page about authentication strategies [here](https://cloud.google.com/docs/authentication/production).

## Configurations

In this session you will see how to configure cloudtask. We have required attributes, optional but required in task declaration and  only optional attributes.
The required attributes are **PROJECT**, **LOCATION** and **SAE**.

Here the details about all attributes accpeted in ``CLOUDTASK``

| Attribute  | Type    | Required  | Description                            |
|------------|---------|-----------|----------------------------------------|
| PROJECT    | ``str`` | ``True``  | Project ID from Google Cloud Platform  |
| LOCATION   | ``str`` | ``True``  | Cloud Task Queue Location              |
| SAE        | ``str`` | ``True``  | Service Account Email                  |
| URL        | ``str`` | ``False`` | Default URL                            |
| QUEUE      | ``srt`` | ``False`` | Default Queue Name                     |
| SECRET     | ``str`` | ``False`` | Secret key to authorize task execution |

#### URL attribute

The URL attribute is optional, but if you don't set you will need to explicitly pass as  a task decorator argument

```python
from cloudtask import task

@task(queue='emails', url='https://mysite.com/emails-tasks')
def send_email(request, to: str):
    pass
```

You can change the ``url`` of task instance in runtime if you need things to be done more automated.

```python
from .tasks import send_email

task = send_email(to='a@a.com')
task.url = 'https://mysite.com/tasks'
task.push()
```

#### QUEUE attribute

The same as the URL attribute, the QUEUE attribute is optional, and if you don't set it you will need to explicitly pass as a task decorator argument. You cannot change the QUEUE of task instance at runtime.

```python
from cloudtask import task

@task(queue='default')
def send_email(request, to: str):
    pass
```

## Working with Tasks

In this session you will see how to play with tasks. Django Cloud Task provides not just one way to create, push and handle tasks. It's flexible! All defined tasks receive the ``request`` keyword argument which is an instance of ``cloudtask.tasks.CloudTaskRequest`` containing all request information from Cloud Task

### Creating and Push

```python
from cloudtask import (
    CloudTaskRequest,
    task)

@task()
def say_yes(rquest) -> None:
    print('Yes')

@task(queue='default', named=True)
def add(request: CloudTaskRequest, a: int = 5, b: int = 4) -> None:
    print(f'Running task with args {a=} and {b=}')
    print(a + b)

# Pushing to Cloud Task

say_yes().delay() # or with push
add().push()
```


#### Immediately Execute a Task

Sometimes you will need to execute the task function immediately (without pushing to Cloud Task), to do that, just call the ``__cal__`` or ``execute`` method from the returned task instance. The request will have limited information.

```python

from .tasks import add
add(a=5, b=3).__call__()
# or using the alias
add(a=5, b=3)()
# or using the execute method
add(a=5, b=3).execute()
```
#### Scheduling

You can schedule a task to be delivered later using native python datetime.

```python
from datetime import timedelta
from django.utils.timezone import now
from .tasks import add

at = now() + timedelta(days=2)
add(a=3, b=6).schedule(at=at)
```

#### Named Tasks

```python
from .tasks import add

add(a=3, b=6).delay()
add(a=3, b=6).delay()
add(a=3, b=6).delay()
```

By default, the above will run normally. Cloud Task by default adds a unique name for each new task. That makes it possible to have duplicated tasks in the queue, even with the same arguments. If you want a task to only be enqueued once at time, you have to set the task as a named task. Django Cloud Task will give a task name based on the task function name. This feature is very useful when you want to do some recursive tasks.

```python
from cloudtask import task

@task(named=True)
def clean_expired(request):
    pass

clean_expired().delay()
clean_expired().delay() # this line will raise an entity error by Cloud Task
```
