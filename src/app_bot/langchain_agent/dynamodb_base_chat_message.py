import os
import boto3
import uuid
import time
from typing import List
from langchain_core.messages import AIMessage, HumanMessage, BaseMessage
from langchain_core.chat_history import BaseChatMessageHistory


class DynamoDBChatMessageHistory(BaseChatMessageHistory):
    def __init__(
        self,
        session_id: str,
        table_name: str = "ApplicationStack-wawausermetadata49856CA1-69aa31b4",
    ):
        self.session_id = session_id
        self.table = boto3.resource(
            "dynamodb",
            endpoint_url=os.environ.get(
                "AWS_ENDPOINT_URL", "http://localhost.localstack.cloud:4566"
            ),
            aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID", "test"),
            aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY", "test"),
            region_name="us-east-1",
        ).Table(table_name)

        self._load_messages()

    def _load_messages(self):
        response = self.table.query(
            KeyConditionExpression=boto3.dynamodb.conditions.Key("session_id").eq(
                self.session_id
            ),
            ScanIndexForward=True,
        )
        items = response.get("Items", [])
        self.messages: List[BaseMessage] = []

        for item in items:
            role = item["role"]
            content = item["content"]
            print("History: ", role, content)
            if role == "user":
                self.messages.append(HumanMessage(content=content))
            elif role == "assistant":
                self.messages.append(AIMessage(content=content))

    def add_message(self, message: BaseMessage) -> None:
        self.messages.append(message)
        self._save_message(message)

    def _save_message(self, message: BaseMessage):
        role = "user" if isinstance(message, HumanMessage) else "assistant"
        timestamp = int(time.time() * 1000)
        self.table.put_item(
            Item={
                "session_id": self.session_id,
                "timestamp": timestamp,
                "message_id": str(uuid.uuid4()),
                "role": role,
                "content": message.content,
            }
        )

    def clear(self) -> None:
        self.messages = []
