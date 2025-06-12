import requests
import asyncio
import uvicorn

from fastapi import FastAPI, Request

app = FastAPI()


def send_to_whatsapp(message: str, phone_number: str) -> tuple[int, dict]:
    url = "https://graph.facebook.com/v22.0/671091322757721/messages"
    headers = {
        "Authorization": "Bearer EAAR9QaZBRJ1sBOx1gZCBvqZCJr3rfHQ2tl1fDGsxGnbWOceSl22aHAco7AjN7R7DMUBkJKfqeaXbTkybU03eqSlBE2u9AHv5qA0ZBxwZAktn4kIFuYvrR2aQf6mD6fRifThORoZBJRvgybePHwBnLKIlFSaSHdZBJ4pQnGf0q1ZBWAWq5sKUAwonZCav1BlZAfulAphvb8GB3pFGfHdwKXfbI82aCv70mLJRJRzdawh8G5OVuZBjVmo0ZBsZD",
        "Content-Type": "application/json",
    }

    whatsapp_payload = {
        "messaging_product": "whatsapp",
        "to": phone_number,
        "type": "text",
        "text": {"body": message},
    }
    response = requests.post(url, headers=headers, json=whatsapp_payload)

    print(response)

    return response.status_code, response.json()


@app.post("/api/v1/send_text_message")
async def app_out(request: Request):
    # Read the JSON payload from the incoming request
    payload = await request.json()
    # Extract the message and phone_number fields from the payload
    message = payload.get("message", "")
    phone_number = payload.get("phone_number", "")

    # Send to WhatsApp in a thread to avoid blocking the event loop
    loop = asyncio.get_event_loop()
    status_code, response_json = await loop.run_in_executor(
        None, send_to_whatsapp, message, phone_number
    )

    return {
        "whatsapp_api_status": status_code,
        "whatsapp_api_response": response_json,
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8002)
