import os
import time
import boto3
import uvicorn
import dotenv
import requests

from fastapi import FastAPI, Request, Response

from boto3.dynamodb.conditions import Key
from decimal import Decimal
from dynamodb_base_chat_message import DynamoDBChatMessageHistory

from langchain_openai import ChatOpenAI
from langchain_core.chat_history import (
    InMemoryChatMessageHistory,
    BaseChatMessageHistory,
)
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

TIME = 360

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
    "ApplicationStack-wawasessions64CA0369-059ff3eb"
)


def query_session(key, table, keyvalue):
    response = table.query(KeyConditionExpression=Key(key).eq(keyvalue))
    items = response["Items"]
    return response["Items"][0] if len(items) > 0 else {}


def save_item_session(table, item):
    response = table.put_item(Item=item)
    return response


def update_item_session(table_name_session, value, session_time):
    try:
        response = table_name_session.update_item(
            Key={"session_id": value},
            UpdateExpression="set session_time=:item1",
            ExpressionAttributeValues={":item1": session_time},
            ReturnValues="UPDATED_NEW",
        )
    except Exception as e:
        print(e)
    else:
        return response


def get_chat_history(session_id: str):
    try:
        session_data = query_session("session_id", table_session_active, session_id)
        print("session_data", session_data)
        now = int(time.time())
        diff = now - session_data["session_time"]
        if diff > TIME:
            print("Create new session")
            update_item_session(table_session_active, session_id, now)
            id = str(session_id)
            return DynamoDBChatMessageHistory(session_id=id)
        else:
            print("Retrieve old session")
            id = str(session_id)
            return DynamoDBChatMessageHistory(session_id=id)
    except Exception as e:
        print("New User", e)
        now = int(time.time())
        id = str(session_id)
        print(id)
        new_row = {
            "session_id": id,
            "session_time": now,
            "session_state": "start",
        }

        save_item_session(table_session_active, new_row)
        return DynamoDBChatMessageHistory(session_id=id)


def get_current_state(session_id):
    try:
        session_data = query_session("session_id", table_session_active, session_id)
        now = int(time.time())
        diff = now - session_data["session_time"]
        session_state = None
        if diff > TIME:
            update_current_state(session_data["session_id"], "start")
            session_state = "start"
        else:
            session_state = session_data["session_state"]
    except:
        session_state = "start"

    return session_state


def update_current_state(session_id, state):
    try:
        response = table_session_active.update_item(
            Key={"session_id": session_id},
            UpdateExpression="set session_state=:item1",
            ExpressionAttributeValues={":item1": state},
            ReturnValues="UPDATED_NEW",
        )
        print("Updated state to:", state)
    except Exception as e:
        print(e)
    else:
        return response


def get_system_prompt(state):
    prompts = {
        "start": "Eres un asistente servicial, saludas al usuario, explicas el simulador autoavanza, que es un sistema de credito prendario por el vehiculo del cliente, y pides de forma amable la foto frontal de la INE",
        "awaiting_ine_front": "Eres un asistente servicial, y pides de forma amable la foto trasera de la INE",
        "awaiting_ine_back": "Eres un asistente servicial, y pides de forma amable la foto frontal de la tarjeta de circulacion",
        "awaiting_tc_front": "Eres un asistente servicial, y pides de forma amable la foto trasera de la tarjeta de circulacion",
        "awaiting_tc_back": "Eres un asistente servicial, y pides de forma amable la foto frontal de la factura del vehiculo",
        "awaiting_invoice_front": "Eres un asistente servicial, y pides de forma amable la foto trasera de la factura del vehiculo",
        "awaiting_invoice_back": "Eres un asistente servicial, y de acuerdo al resultado de las siguientes reglas decides si procedes a la oferta final o no.",
        "awaiting_final_offer": "",
    }

    return prompts[state]


def get_next_state(state):
    condition_states = {
        "start": "awaiting_ine_front",
        "awaiting_ine_front": "awaiting_ine_back",
        "awaiting_ine_back": "awaiting_tc_front",
        "awaiting_tc_front": "awaiting_tc_back",
        "awaiting_tc_back": "awaiting_invoice_front",
        "awaiting_invoice_front": "awaiting_invoice_back",
        "awaiting_invoice_back": "awaiting_final_offer",
    }
    return condition_states[state]


def get_pipeline(state):
    pipeline_states = {
        "start": prompt | llm,
        "awaiting_ine_front": prompt | llm,
        "awaiting_ine_back": prompt | llm,
        "awaiting_tc_front": prompt | llm,
        "awaiting_tc_back": prompt | llm,
        "awaiting_invoice_front": prompt | llm,
        "awaiting_invoice_back": prompt | llm,
        "awaiting_final_offer": prompt | llm,
    }
    return pipeline_states[state]


current_state = "start"

prompt = ChatPromptTemplate.from_messages(
    [
        SystemMessagePromptTemplate.from_template("{prompt_query}"),
        MessagesPlaceholder(variable_name="history"),
        HumanMessagePromptTemplate.from_template("{query}"),
    ]
)


@app.post("/api/v1/langchain_agent")
async def langchain_agent(request: Request):
    data = await request.json()

    current_state = get_current_state(data["phone"])

    pipeline = get_pipeline(current_state)

    pipeline_with_history = RunnableWithMessageHistory(
        pipeline,
        get_session_history=get_chat_history,
        input_messages_key="query",
        history_messages_key="history",
    )

    prompt_query = get_system_prompt(current_state)

    aimessage = pipeline_with_history.invoke(
        {"query": data["body"], "prompt_query": prompt_query},
        config={"session_id": data["phone"]},
    )

    response = requests.post(
        "http://localhost:8002/api/v1/send_text_message",
        json={"message": aimessage.content, "phone_number": data["phone"]},
    )

    next_state = get_next_state(current_state)

    update_current_state(data["phone"], next_state)

    return Response(content=response.text)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
