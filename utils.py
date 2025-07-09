import os
import requests

META_WHATSAPP_API_URL = os.getenv("META_WHATSAPP_API_URL")
META_WHATSAPP_ACCESS_TOKEN = os.getenv("META_WHATSAPP_ACCESS_TOKEN")
META_WHATSAPP_TEMPLATE_NAME = os.getenv("META_WHATSAPP_TEMPLATE_NAME")
META_WHATSAPP_TEMPLATE_LANG = os.getenv("META_WHATSAPP_TEMPLATE_LANG", "en_US")

def send_whatsapp_message(phone_number: str, ticker_text: str):
    """
    Send a WhatsApp message to the given phone number using the Meta API and a template with one variable (ticker_text).
    """
    headers = {
        "Authorization": f"Bearer {META_WHATSAPP_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    data = {
        "messaging_product": "whatsapp",
        "to": phone_number,
        "type": "template",
        "template": {
            "name": META_WHATSAPP_TEMPLATE_NAME,
            "language": {"code": META_WHATSAPP_TEMPLATE_LANG},
            "components": [
                {
                    "type": "body",
                    "parameters": [
                        {"type": "text", "text": ticker_text}
                    ]
                }
            ]
        }
    }
    response = requests.post(META_WHATSAPP_API_URL, headers=headers, json=data)
    return response
