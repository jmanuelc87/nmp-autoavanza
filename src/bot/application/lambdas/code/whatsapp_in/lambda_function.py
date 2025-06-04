import os
import time
import json
import boto3

from botocore.exceptions import ClientError

BYE = {
    "statusCode": 200,
    "headers": {
        "Content-Type": "text/html;charset=UTF-8",
        "charset": "UTF-8",
        "Access-Control-Allow-Origin": "*",
    },
    "body": "bye bye",
}


OK = {
    "statusCode": 200,
    "headers": {
        "Content-Type": "text/html;charset=UTF-8",
        "charset": "UTF-8",
        "Access-Control-Allow-Origin": "*",
    },
    "body": "OK",
}


dynamodb_resource = boto3.resource("dynamodb")
table = dynamodb_resource.Table(os.environ.get("MESSAGES_METADATA"))


def lambda_handler(event, context):

    if event.get("body") is None:
        return BYE

    whatsapp_body = json.loads(event["body"])
    batch = []

    # Do not process messages older than 300 sec
    for entry in whatsapp_body["entry"]:
        for change in entry["changes"]:
            messages = change["value"][change["field"]]

            for message in messages:
                timestamp = int(message["timestamp"])
                now = int(time.time())

                if now - timestamp >= 300:
                    continue

                message["messages_id"] = message["id"]

                batch.append(message)

    # Batch writer to dynamo db
    try:
        with table.batch_writer() as writer:
            for item in batch:
                writer.put_item(Item=item)
    except ClientError as e:
        print("No messages")
        print(e)

    return OK
