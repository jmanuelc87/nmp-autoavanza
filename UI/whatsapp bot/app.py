from flask import Flask, request
import os
import requests

app = Flask(__name__)

# Meta credentials
ACCESS_TOKEN = "EAAZABXF6q620BO18F6GsDYPbI2sN7gnhWxA8i0Lk9o6c9rXvJPL7qOmZCyqIO2WqujZBtmCFkZBuQRKNEZBQ3RYBjeTtfQNBSBTDY8xgn9ecPZBZAh632g5QM54M3fIKzYkgkhvy7zUvcCRqZCANa2wY9HUXrciqL0iaPe1IuKzedCO5ztEJ1sDC9oxKBfDWIWS4BA26TZAYbEtjf6ZCnm2dk9DH05QDbkj5S1A91woK7MkrLfGGwb"
VERIFY_TOKEN = "NMP123"

# User state: tracks what step each user is on
user_state = {}

# Ordered list of required documents
document_steps = [
    "INE_front", "INE_back",
    "LICENSE_front", "LICENSE_back",
    "INVOICE_front", "INVOICE_back"
]

# ===========
# ROUTES
# ===========

@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    if request.method == 'GET':
        mode = request.args.get('hub.mode')
        token = request.args.get('hub.verify_token')
        challenge = request.args.get('hub.challenge')

        if mode == 'subscribe' and token == VERIFY_TOKEN:
            print("✅ Webhook verified!")
            return challenge, 200
        else:
            return '❌ Verification failed', 403

    if request.method == 'POST':
        data = request.get_json()
        print("📩 Webhook triggered!")

        if data.get("entry"):
            for entry in data["entry"]:
                for change in entry["changes"]:
                    value = change["value"]
                    messages = value.get("messages")

                    if messages:
                        for message in messages:
                            phone_number = message["from"]
                            message_type = message["type"]

                            # First-time user setup
                            if phone_number not in user_state:
                                user_state[phone_number] = 0
                                send_message(phone_number, "👋 Hola! Vamos a iniciar. Por favor envía la *foto del frente de tu INE*.")
                                return "ok", 200

                            # If finished
                            step_index = user_state[phone_number]
                            if step_index >= len(document_steps):
                                send_message(phone_number, "✅ Ya recibimos los 6 documentos. ¡Gracias!")
                                return "ok", 200

                            # Handle image upload
                            if message_type == "image":
                                current_step = document_steps[step_index]
                                image_id = message["image"]["id"]
                                file_data = get_image(image_id)

                                filename = f"{current_step}.jpg"
                                folder_path = f"received_images/{phone_number}"
                                os.makedirs(folder_path, exist_ok=True)
                                file_path = os.path.join(folder_path, filename)

                                with open(file_path, "wb") as f:
                                    f.write(file_data)
                                print(f"✅ Image saved as {file_path}")

                                # Move to next step
                                user_state[phone_number] += 1
                                if user_state[phone_number] < len(document_steps):
                                    next_step = document_steps[user_state[phone_number]]
                                    prompt = step_to_prompt(next_step)
                                    send_message(phone_number, prompt)
                                else:
                                    send_message(phone_number, "✅ ¡Todos los documentos han sido recibidos correctamente!")

                            else:
                                send_message(phone_number, "📸 Por favor envía una *imagen*.")
        return "ok", 200

# ===========
# UTILITIES
# ===========

def send_message(to_number, message):
    url = "https://graph.facebook.com/v19.0/659482707251850/messages"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    data = {
        "messaging_product": "whatsapp",
        "to": to_number,
        "type": "text",
        "text": {
            "body": message
        }
    }
    response = requests.post(url, headers=headers, json=data)
    print(f"📤 Sent message: {message} | Status: {response.status_code}")

def get_image(media_id):
    # Step 1: Get image URL
    url = f"https://graph.facebook.com/v19.0/{media_id}"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}"
    }
    response = requests.get(url, headers=headers)
    file_url = response.json().get("url")

    # Step 2: Download the file
    response = requests.get(file_url, headers=headers)
    return response.content

def step_to_prompt(step):
    prompts = {
        "INE_front": "📸 Por favor envía la *foto del frente de tu INE*.",
        "INE_back": "📸 Ahora envía la *foto del reverso de tu INE*.",
        "LICENSE_front": "📸 Envíame la *foto del frente de tu licencia de conducir*.",
        "LICENSE_back": "📸 Ahora envía la *foto del reverso de tu licencia*.",
        "INVOICE_front": "📸 Envíame la *foto del frente de la factura del auto*.",
        "INVOICE_back": "📸 Finalmente, envía la *foto del reverso de la factura*."
    }
    return prompts.get(step, "📸 Por favor envía una imagen.")

# ===========
# START APP
# ===========
if __name__ == '__main__':
    app.run(port=5000)
