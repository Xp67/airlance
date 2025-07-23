from flask import request, jsonify  # type: ignore
from google.cloud import tasks_v2
from google.protobuf import timestamp_pb2 # type: ignore
import datetime
import json
import os

def crea_task_postprocess(filename: str, foto_id: str):
    client = tasks_v2.CloudTasksClient()

    project = os.environ["GOOGLE_CLOUD_PROJECT"]
    location = "europe-west1"
    queue = "default"
    url = f"https://{os.environ['SERVICE_DOMAIN']}/task/elabora-foto"
    parent = client.queue_path(project, location, queue)

    payload = {
        "filename": filename,
        "foto_id": foto_id
    }

    timestamp = timestamp_pb2.Timestamp()
    timestamp.FromDatetime(datetime.datetime.utcnow() + datetime.timedelta(seconds=5))

    task = {
        "http_request": {
            "http_method": tasks_v2.HttpMethod.POST,
            "url": url,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(payload).encode()
        },
        "schedule_time": timestamp
    }

    client.create_task(request={"parent": parent, "task": task})

