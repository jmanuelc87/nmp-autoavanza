import os
import time
import json
import boto3
import decimal
import logging


from boto3.dynamodb.types import TypeDeserializer
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


ERR = {
    "statusCode": 500,
    "headers": {
        "Content-Type": "text/html;charset=UTF-8",
        "charset": "UTF-8",
        "Access-Control-Allow-Origin": "*",
    },
    "body": "Error",
}


class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            if o % 1 > 0:
                return float(o)
            else:
                return int(o)
        return super(DecimalEncoder, self).default(o)


def ddb_deserialize(r, type_deserializer=TypeDeserializer()):
    return type_deserializer.deserialize({"M": r})


def get_logger(level):
    root = logging.getLogger()
    if root.handlers:
        for handler in root.handlers:
            root.removeHandler(handler)
    logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=level)
    return root


def invoke_lambda(function_name, payload):
    lambda_client = boto3.client("lambda")

    try:
        response = lambda_client.invoke(
            FunctionName=function_name,
            InvocationType="Event",
            Payload=json.dumps(payload),
        )

        return response
    except ClientError as e:
        err = e.response
        print(err.get("Error"))
        return ERR


log = get_logger(logging.INFO)


def lambda_handler(events, context):
    # Iterate records
    for record in events["Records"]:
        item = record["dynamodb"]["NewImage"]

        try:
            entry = json.loads(json.dumps(ddb_deserialize(item), cls=DecimalEncoder))
            messages_id = entry["messages_id"]
            event_name = record["eventName"]

            if event_name == "INSERT":
                print("messages_id:", messages_id)
                message_type = entry["type"]

                if message_type == "text":
                    body = entry["text"]["body"]
                    phone = "+" + str(entry["from"])
                    phone_id = entry["phone_id"]

                    payload = {
                        "message_body": body,
                        "phone": phone,
                        "phone_id": phone_id,
                        "message_id": messages_id,
                    }

                    response = invoke_lambda(
                        function_name=os.environ.get("ENV_LANG_CHAIN_AGENT"),
                        payload=payload,
                    )

                    log.info(response)

                elif message_type == "image":
                    id = entry["image"]["body"]
                    caption = entry["image"]["caption"]

                    # search for the image using the META API

            else:
                log.info("No new messages")

        except Exception as e:
            log.error("Error: ", e)
