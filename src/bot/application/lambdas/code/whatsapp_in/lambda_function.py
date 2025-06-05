import os
import sys
import time
import json
import boto3

import logging

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


def get_logger(level):
    root = logging.getLogger()
    if root.handlers:
        for handler in root.handlers:
            root.removeHandler(handler)
    logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s',level=level)
    return root


dynamodb_resource = boto3.resource("dynamodb")
table = dynamodb_resource.Table(os.environ.get("MESSAGES_METADATA"))
log = get_logger(logging.INFO)


def lambda_handler(event, context):

    if event.get("body") is None:
        return BYE

    whatsapp_body = json.loads(event["body"])
    batch = []

    # Do not process messages older than 300 sec
    for entry in whatsapp_body["entry"]:
        for change in entry["changes"]:
            phone_id = change["value"]["metadata"]["phone_number_id"]
            name = change["value"]["contacts"][0]["profile"]["name"]
            messages = change["value"][change["field"]]

            for message in messages:
                timestamp = int(message["timestamp"])
                now = int(time.time())

                if now - timestamp >= 300:
                    continue

                message["messages_id"] = message["id"]
                message["phone_id"] = phone_id
                message["name"] = name

                batch.append(message)

    # Batch writer to dynamo db
    try:
        with table.batch_writer() as writer:
            for item in batch:
                writer.put_item(Item=item)

        log.info("Message Published")
    except ClientError as e:
        log.info("No Messages")
        log.info(e.get("Error"))

    return OK
