from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.http.request import HttpRequest

from cloudtask.tasks import get_task_by_path, CoudTaskRequest
from cloudtask.utils import get_decoded_payload
from cloudtask.configs import (
    DCT_SECRET_HEADER_NAME,
    conf)


@csrf_exempt
def run_task_view(request: HttpRequest):
    if request.method == 'POST':
        headers: dict = request.META
        secret: str = headers.pop(DCT_SECRET_HEADER_NAME, None)
        if conf.SECRET and secret != conf.SECRET:
            return HttpResponse(status=403)
        if (payload := get_decoded_payload(request.body)) is not None:
            local_task_path: str = payload.get('path', '')
            data: dict = payload.get('data', dict())
            try:
                task = get_task_by_path(local_task_path)
                task.run(request=CoudTaskRequest(
                    request=request, headers=headers), **data)
                return JsonResponse({'detail': 'Success'})
            except Exception as e:
                # TODO: add logger
                return HttpResponse(status=500)
        return JsonResponse({'detail': 'Missing request body'}, status=400)
    return HttpResponse(status=405)
