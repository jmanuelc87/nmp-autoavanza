import os
import time
import boto3
import uvicorn
import dotenv
import requests

from fastapi import FastAPI, Request, Response

from boto3.dynamodb.conditions import Key

from langchain_openai import ChatOpenAI
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.messages import BaseMessage, HumanMessage
from langchain.prompts import (
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
    MessagesPlaceholder,
    ChatPromptTemplate,
)

dotenv.load_dotenv(dotenv_path=dotenv.find_dotenv())

app = FastAPI()

llm = ChatOpenAI(temperature=0)

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
table_session_active = dynamodb_resource.Table(
    "ApplicationStack-wawasessions64CA0369-0485187a"
)


def query(key, table, keyvalue):
    response = table.query(KeyConditionExpression=Key(key).eq(keyvalue))
    print(response)
    return response["Items"][0]


def save_item_ddb(table, item):
    response = table.put_item(Item=item)
    return response


def update_item_session(table_name_session, value, session_time):
    try:
        response = table_name_session.update_item(
            Key={"phone_number": value},
            UpdateExpression="set session_time=:item1",
            ExpressionAttributeValues={":item1": session_time},
            ReturnValues="UPDATED_NEW",
        )
        print(response)
    except Exception as e:
        print(e)
    else:
        return response


def query_history(key, keyvalue):
    print("Query History")
    table_session_active = dynamodb_resource.Table(
        "ApplicationStack-wawausermetadata49856CA1-68c7a5c2"
    )
    response = table_session_active.query(KeyConditionExpression=Key(key).eq(keyvalue))
    return response["Items"][0]


def get_chat_history(session_id: str):
    try:
        session_data = query("session_id", table_session_active, session_id)
        now = int(time.time())
        diff = now = session_data["session_time"]
        if diff > 300:
            update_item_session(table_session_active, session_id, now)
            id = str(session_id) + "_" + str(now)
            history = []
        else:
            id = str(session_id) + "_" + str(session_data["session_time"])
            history = query_history("session_id", id)["History"]

        print("history", history)

        messages = []
        for message in history:
            messages.append(BaseMessage(message))

        messageHistory = InMemoryChatMessageHistory(messages)

        return messageHistory
    except:
        now = int(time.time())
        id = str(session_id) + "_" + str(now)
        new_row = {"session_id": id, "session_time": now}
        save_item_ddb(table_session_active, new_row)
        history = []
        return InMemoryChatMessageHistory()


prompt = ChatPromptTemplate(
    [
        {
            "role": "system",
            "content": "Eres un asistente servicial.",
        },
        {"role": "user", "content": "{query}"},
    ]
)


@app.post("/api/v1/langchain_agent")
async def langchain_agent(request: Request):
    data = await request.json()

    ## Add prompt template following a state structure states
    pipeline_with_history = RunnableWithMessageHistory(
        prompt | llm,
        get_session_history=get_chat_history,
        input_messages_key="query",
        history_messages_key="history",
    )

    aimessage = pipeline_with_history.invoke(
        {"query": data["body"]}, config={"session_id": data["phone"]}
    )

    response = requests.post(
        "http://localhost:8002/api/v1/send_text_message",
        json={"message": aimessage.content, "phone_number": data["phone"]},
    )

    print("aimessage", aimessage.content)

    return Response(content=response.text)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
