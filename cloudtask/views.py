import logging

from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.http.request import HttpRequest

from cloudtask.tasks import get_task_by_path, CloudTaskRequest
from cloudtask.utils import get_decoded_payload
from cloudtask.configs import (
    DCT_SECRET_HEADER_NAME,
    conf)


logger = logging.getLogger(__name__)

@csrf_exempt
def run_task_view(request: HttpRequest):
    if request.method == 'POST':

        headers: dict = request.META
        secret: str = headers.pop(DCT_SECRET_HEADER_NAME, None)
        extra: dict = { # logger extra
            'task_queue_name': headers.get('HTTP_X_CLOUDTASKS_QUEUENAME', ''),
            'task_name': headers.get('HTTP_X_CLOUDTASKS_TASKNAME', '')} 

        if conf.SECRET and secret != conf.SECRET:
            return JsonResponse({
                'detail': 'Cloud task secret mismatch'}, status=403)

        if (payload := get_decoded_payload(request.body)) is not None:
            local_task_path: str = payload.get('path', '')
            data: dict = payload.get('data', dict())
            try:
                task = get_task_by_path(local_task_path)
                task.run(request=CloudTaskRequest(
                    request=request, headers=headers), **data)
            except Exception as e:
                logger.exception(e, extra=extra)
                return HttpResponse(status=500)
            logger.info((
                'Task %s from %s queue executed successfully' % (
                    extra['task_name'], extra['task_queue_name'])),
                extra=extra)
            return JsonResponse({'detail': 'Success'})
        return JsonResponse({'detail': 'Missing request body'}, status=400)
    return HttpResponse(status=405)
