import uuid
import boto3
import logging
import tempfile
import document_service.buckets as s3
import document_service.tables as db

from fastapi import FastAPI, UploadFile
from fastapi.responses import FileResponse
from document_service.lifespan import lifespan

app = FastAPI(lifespan=lifespan)


@app.post("/upload_file")
def upload_file(name: str, phone: str, type: str, blob: UploadFile):
    key = uuid.uuid4().hex

    result = s3.upload_file(blob.file, "nmp-autoavanza-documents", object_name=key)

    if result:
        db.put_item(
            kwargs={
                "client_name": name,
                "client_phone": phone,
                "document_name": blob.filename,
                "object_name": key,
                "document_type": type,
            }
        )

    return result


@app.get("/get_file")
def get_file(name: str, phone: str, type: str):

    item = db.get_item(
        kwargs={"client_name": name, "client_phone": phone, "document_type": "factura"}
    )

    tmp = tempfile.NamedTemporaryFile(mode="w+b", delete=False)

    try:
        s3.download_file(item["object_name"], "nmp-autoavanza-documents", tmp)
        return FileResponse(tmp.name, filename=item["document_name"])
    finally:
        tmp.close()
