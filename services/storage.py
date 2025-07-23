from google.cloud import storage, secretmanager
from google.oauth2 import service_account # type: ignore
import json, os
from datetime import timedelta
import threading

_signed_client = None
_signed_lock = threading.Lock()

def firma_url(blob_path: str, metodo: str = "PUT", durata_minuti: int = 10, content_type: str = "application/octet-stream") -> str:
    global _signed_client

    # inizializza una sola volta il client con chiave da Secret Manager
    if _signed_client is None:
        with _signed_lock:
            if _signed_client is None:
                _signed_client = _init_signed_client()

    bucket = _signed_client.bucket("fotomireamakeup")
    blob = bucket.blob(blob_path)

    url = blob.generate_signed_url(
        version="v4",
        expiration=timedelta(minutes=durata_minuti),
        method=metodo,
        content_type = content_type,
    )
    return url


def _init_signed_client() -> storage.Client:
    secret_client = secretmanager.SecretManagerServiceClient()
    project_id = "mireamakeup"
    secret_name = "sa-url-signer"

    secret_path = f"projects/{project_id}/secrets/{secret_name}/versions/latest"
    response = secret_client.access_secret_version(request={"name": secret_path})
    payload = response.payload.data.decode("UTF-8")

    key_data = json.loads(payload)
    credentials = service_account.Credentials.from_service_account_info(key_data)

    return storage.Client(credentials=credentials, project=project_id)


