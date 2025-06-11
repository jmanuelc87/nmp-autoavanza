import os
import boto3
import dotenv
import uvicorn

from fastapi import FastAPI, Request, Query, Response, status

dotenv.load_dotenv(dotenv_path=dotenv.find_dotenv())

app = FastAPI()

# initialize DynamoDB table
dynamodb_resource = boto3.resource(
    "dynamodb",
    endpoint_url=os.environ.get(
        "AWS_ENDPOINT_URL", "http://localhost.localstack.cloud:4566"
    ),
    aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID", "test"),
    aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY", "test"),
    region_name="us-east-1",
)
table = dynamodb_resource.Table("ApplicationStack-wawamessagesmetadataB10E-fef7ffcb")


def process_messages(entries):
    messages = []

    for entry in entries:
        for change in entry["changes"]:
            phone_id = change["value"]["metadata"]["phone_number_id"]
            name = ""
            if hasattr(change["value"], "contacts"):
                name = change["value"]["contacts"][0]["profile"]["name"]
            try:
                incoming = change["value"][change["field"]]

                for message in incoming:
                    message["messages_id"] = message["id"]
                    message["phone_id"] = phone_id
                    message["name"] = name
                    messages.append(message)
            except:
                print("No messages")

    return messages


@app.get("/api/v1/webhook")
def app_webhook_verify(
    hub_mode: str = Query(..., alias="hub.mode"),
    hub_verify_token: str = Query(..., alias="hub.verify_token"),
    hub_challenge: str = Query(..., alias="hub.challenge"),
):
    """Verify webhook subscription challenge."""
    if hub_mode == "subscribe" and hub_verify_token == "NMP2025":
        return Response(content=hub_challenge, status_code=status.HTTP_200_OK)
    else:
        return Response(content="Forbidden", status_code=status.HTTP_403_FORBIDDEN)


@app.post("/api/v1/webhook")
async def app_webhook_post(request: Request):
    """Receive incoming webhook POSTs, process and store messages."""
    payload = await request.json()

    # Extract and process messages from the payload
    entries = payload.get("entry", [])
    messages = process_messages(entries)

    # Batch insert messages in DynamoDB
    with table.batch_writer() as batch:
        for msg in messages:
            batch.put_item(Item=msg)

    return Response(status_code=200)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
