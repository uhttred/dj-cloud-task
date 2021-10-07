from django.urls import path
from cloudtask.views import run_task_view

app_name = 'cloudtask'

urlpatterns = [
    path('', run_task_view, name='run_task')
]
