import boto3
import logging

from botocore.exceptions import ClientError

logger = logging.getLogger("uvicorn.access")

endpoint_url = "http://localhost.localstack.cloud:4566"


def create_table(table_name: str):
    try:
        dynamodb = boto3.resource(
            "dynamodb",
            endpoint_url=endpoint_url,
            aws_access_key_id="test",
            aws_secret_access_key="test",
            region_name="us-east-1",
        )

        table = dynamodb.create_table(
            TableName=table_name,
            KeySchema=[
                {"AttributeName": "client_name", "KeyType": "HASH"},
                {"AttributeName": "client_phone", "KeyType": "RANGE"},
            ],
            AttributeDefinitions=[
                {"AttributeName": "client_name", "AttributeType": "S"},
                {"AttributeName": "client_phone", "AttributeType": "S"},
            ],
            ProvisionedThroughput={"ReadCapacityUnits": 2, "WriteCapacityUnits": 2},
        )

        table.meta.client.get_waiter("table_exists").wait(TableName="users")
        logger.info("Table is now ACTIVE and ready.")
    except ClientError as e:
        logger.error(e)
        return False
    return True


def put_item(**kwargs):
    try:
        dynamodb = boto3.resource(
            "dynamodb",
            endpoint_url=endpoint_url,
            aws_access_key_id="test",
            aws_secret_access_key="test",
            region_name="us-east-1",
        )

        table = dynamodb.Table("nmp-autoavanza-documents")

        table.put_item(
            Item={
                "client_name": kwargs["kwargs"]["client_name"],
                "client_phone": kwargs["kwargs"]["client_phone"],
                "document_name": kwargs["kwargs"]["document_name"],
                "object_name": kwargs["kwargs"]["object_name"],
                "document_type": kwargs["kwargs"]["document_type"],
            },
        )
    except ClientError as e:
        logger.error(e)
        return False
    return True


def get_item(**kwargs):
    try:
        dynamodb = boto3.resource(
            "dynamodb",
            endpoint_url=endpoint_url,
            aws_access_key_id="test",
            aws_secret_access_key="test",
            region_name="us-east-1",
        )

        table = dynamodb.Table("nmp-autoavanza-documents")

        response = table.get_item(
            Key={
                "client_name": kwargs["kwargs"]["client_name"],
                "client_phone": kwargs["kwargs"]["client_phone"],
            }
        )

        logger.info(response['Item'])

        return response['Item']
    except ClientError as e:
        logger.error(e)
        return False
