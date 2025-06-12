import os
import json
import boto3
import time
import decimal
import requests

from boto3.dynamodb.types import TypeDeserializer

# Facebook API token
token = os.environ.get("FB_GRAPH_API_TOKEN", "")

# DynamoDB table name
DYNAMODB_TABLE_NAME = "ApplicationStack-wawamessagesmetadataB10E-2aad007f"

# AWS / LocalStack configuration
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
            # Convert Decimal to int or float
            if o % 1 > 0:
                return float(o)
            else:
                return int(o)
        return super(DecimalEncoder, self).default(o)


def ddb_deserialize(item_map, type_deserializer=TypeDeserializer()):
    """
    Convert a DynamoDB attribute map (M) into a normal Python dict.
    """
    return type_deserializer.deserialize({"M": item_map})


def call_agent(payload):
    try:
        resp = requests.post(
            "http://localhost:8001/api/v1/langchain_agent",
            json=payload,
        )
        resp.raise_for_status()
        print(f"Text POST succeeded: {resp.status_code}")
    except requests.RequestException as e:
        print(f"Text POST failed: {e}")


def process_text_message(entry):
    """
    Handle text messages by forwarding them to an external agent.
    """
    body = entry["text"]["body"]
    phone = entry["from"]
    payload = {"body": body, "phone": phone}

    call_agent(payload)


def process_image_message(entry):
    """
    Handle image messages:
    1. Fetch the image URL from Facebook Graph API.
    2. Download the image binary.
    3. Save it locally as <image_id>.jpg.
    4. Upload to S3
    """
    image_id = entry["image"]["id"]
    phone_number = entry["image"]["from"]
    caption = entry["image"].get("caption", "")

    # Step 1: get the direct URL
    meta_url = f"https://graph.facebook.com/v22.0/{image_id}"
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(meta_url, headers=headers)
    resp.raise_for_status()
    image_url = resp.json().get("url")
    if not image_url:
        print(f"No URL found for image {image_id}")
        return

    # Step 2: download the binary
    image_resp = requests.get(image_url, headers=headers)
    image_resp.raise_for_status()

    # Step 3: save locally
    filename = f"{image_id}.jpg"
    with open(filename, "wb") as img_file:
        img_file.write(image_resp.content)

    # Use the algorithm to crop the image

    # Step 4: upload to S3
    s3_client = boto3.client("s3", **AWS)
    bucket_name = "YOUR_S3_BUCKET"
    s3_key = f"images/{filename}-{caption}-{phone_number}"
    try:
        s3_client.upload_file(filename, bucket_name, s3_key)
        print(f"Uploaded {filename} to s3://{bucket_name}/{s3_key}")
    except Exception as e:
        print(f"Failed to upload to S3: {e}")

    print(f"Downloaded image {image_id} to {filename} with caption: {caption}")

    payload = {"body": caption, "phone": phone_number, "s3_key": s3_key}

    call_agent(payload)


def consume_record(record):
    """
    Deserialize a single DynamoDB stream record and dispatch
    to the appropriate handler.
    """
    new_img = record["dynamodb"]["NewImage"]
    entry = json.loads(json.dumps(ddb_deserialize(new_img), cls=DecimalEncoder))
    event_name = record.get("eventName")
    message_id = entry.get("messages_id")
    print(f"Event: {event_name}, Message ID: {message_id}")

    if event_name == "INSERT":
        message_type = entry.get("type")
        if message_type == "text":
            process_text_message(entry)
        elif message_type == "image":
            process_image_message(entry)


def get_latest_stream_arn(table_name):
    """
    Return the LatestStreamArn for a given DynamoDB table.
    """
    dd_client = boto3.client("dynamodb", **AWS)
    desc = dd_client.describe_table(TableName=table_name)
    return desc["Table"]["LatestStreamArn"]


def get_shard_iterator(stream_arn):
    """
    Given a Stream ARN, return a shard iterator positioned at LATEST.
    """
    ds_client = boto3.client("dynamodbstreams", **AWS)
    stream_desc = ds_client.describe_stream(StreamArn=stream_arn)
    shard_id = stream_desc["StreamDescription"]["Shards"][0]["ShardId"]
    it_resp = ds_client.get_shard_iterator(
        StreamArn=stream_arn,
        ShardId=shard_id,
        ShardIteratorType="LATEST",
    )
    return it_resp["ShardIterator"]


def consume_stream(table_name):
    """
    Poll the DynamoDB stream and process new records.
    """
    stream_arn = get_latest_stream_arn(table_name)
    ds_client = boto3.client("dynamodbstreams", **AWS)
    shard_iterator = get_shard_iterator(stream_arn)

    print(f"Starting to consume stream for table {table_name}...")
    while shard_iterator:
        resp = ds_client.get_records(ShardIterator=shard_iterator, Limit=100)
        for record in resp.get("Records", []):
            try:
                consume_record(record)
            except Exception as e:
                print("Error processing record:", e)
        shard_iterator = resp.get("NextShardIterator")
        time.sleep(1)


if __name__ == "__main__":
    consume_stream(DYNAMODB_TABLE_NAME)
