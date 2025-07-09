import os
import requests

META_WHATSAPP_API_URL = os.getenv("META_WHATSAPP_API_URL")
META_WHATSAPP_ACCESS_TOKEN = os.getenv("META_WHATSAPP_ACCESS_TOKEN")
META_WHATSAPP_PHONE_NUMBER_ID = os.getenv("META_WHATSAPP_PHONE_NUMBER_ID")
META_WHATSAPP_TEMPLATE_NAME = os.getenv("META_WHATSAPP_TEMPLATE_NAME")
META_WHATSAPP_TEMPLATE_LANG = os.getenv("META_WHATSAPP_TEMPLATE_LANG", "en_US")

def send_whatsapp_message(phone_number: str, ticker_text: str):
    url = META_WHATSAPP_API_URL
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
    response = requests.post(url, headers=headers, json=data)
    print("Status Code:", response.status_code)
    print("Response:", response.text)
    return response

if __name__ == "__main__":
    # Test message
    send_whatsapp_message("918948889878", "This is a test message from ArthAdvisor GPT!")
