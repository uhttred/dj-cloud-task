from google.cloud import tasks_v2
# from google.protobuf import timestamp_pb2


class CloudTaskClient(tasks_v2.CloudTasksClient):
    pass


client = CloudTaskClient()
