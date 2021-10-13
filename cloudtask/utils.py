import base64
import json
from typing import Callable, Union
from cloudtask.encoder import DefaultJSONEncoder


def get_internal_task_path(func: Callable) -> str:
    return '.'.join((func.__module__, func.__name__))

def get_encoded_payload(payload: dict) -> bytes:
    payload_str: str = json.dumps(payload, cls=DefaultJSONEncoder)
    b64_encoded_payload = base64.b64encode(payload_str.encode())
    return b64_encoded_payload

def get_decoded_payload(payload: bytes) -> Union[dict, None]:
    if payload:
        payload_str: str = payload.decode('utf-8')
        b64_decoded_payload: bytes = base64.b64decode(payload_str)
        return json.loads(b64_decoded_payload)
    return None
    