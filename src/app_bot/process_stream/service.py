import os
import json
import boto3
import time
import decimal
import requests

from boto3.dynamodb.types import TypeDeserializer

DYNAMODB_TABLE_NAME = "ApplicationStack-wawamessagesmetadataB10E-fef7ffcb"

AWS = {
    "endpoint_url": os.environ.get(
        "AWS_ENDPOINT_URL", "http://localhost.localstack.cloud:4566"
    ),
    "aws_access_key_id": os.environ.get("AWS_ACCESS_KEY_ID", "test"),
    "aws_secret_access_key": os.environ.get("AWS_SECRET_ACCESS_KEY", "test"),
    "region_name": "us-east-1",
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


def process_text_message(entry):
    body = entry["text"]["body"]
    phone = entry["from"]
    payload = {"body": body, "phone": phone}

    try:
        response = requests.post(
            "http://localhost:8001/api/v1/langchain_agent", json=payload
        )
        response.raise_for_status()
        print(f"POST succeeded: {response.status_code}")
    except requests.RequestException as e:
        print(f"POST failed: {e}")


def process_image_message(entry):
    print("image")


def consume_record(record):
    entry = json.loads(
        json.dumps(ddb_deserialize(record["dynamodb"]["NewImage"]), cls=DecimalEncoder)
    )
    message_id = entry.get("messages_id")
    event_name = record.get("eventName")

    print(event_name, message_id)

    if event_name == "INSERT":
        message_type = entry.get("type")
        if message_type == "text":
            process_text_message(entry)
        elif message_type == "image":
            process_image_message(entry)


def get_latest_stream_arn(table_name):
    dynamodb = boto3.client("dynamodb", **AWS)
    desc = dynamodb.describe_table(TableName=table_name)
    return desc["Table"]["LatestStreamArn"]


def get_shard_iterator(stream_arn):
    client = boto3.client("dynamodbstreams", **AWS)
    stream_desc = client.describe_stream(StreamArn=stream_arn)
    shard_id = stream_desc["StreamDescription"]["Shards"][0]["ShardId"]
    iterator_resp = client.get_shard_iterator(
        StreamArn=stream_arn, ShardId=shard_id, ShardIteratorType="LATEST"
    )
    return iterator_resp["ShardIterator"]


def consume_stream(table_name):
    stream_arn = get_latest_stream_arn(table_name)
    client = boto3.client("dynamodbstreams", **AWS)
    shard_iterator = get_shard_iterator(stream_arn)

    print(f"Consuming DynamoDB Stream for table: {table_name}")
    while True:
        response = client.get_records(ShardIterator=shard_iterator, Limit=100)
        records = response.get("Records", [])
        for record in records:
            try:
                consume_record(record)
            except Exception as e:
                print("Error:", e)

        shard_iterator = response.get("NextShardIterator")
        if not shard_iterator:
            break

        time.sleep(0.25)


if __name__ == "__main__":
    consume_stream(DYNAMODB_TABLE_NAME)
