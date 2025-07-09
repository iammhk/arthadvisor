import os
import requests
from dotenv import load_dotenv
load_dotenv()

def send_whatsapp_ticker(phone_number, ticker_text, template_name=None, lang_code="en_US"):
    """
    Send ticker_text to the given phone number using WhatsApp template API.
    If template_name is not provided, uses META_WHATSAPP_TEMPLATE_NAME from env.
    """
    api_url = os.getenv("META_WHATSAPP_API_URL")
    access_token = os.getenv("META_WHATSAPP_ACCESS_TOKEN")
    if not template_name:
        template_name = os.getenv("META_WHATSAPP_TEMPLATE_NAME")
    if not api_url or not access_token or not template_name:
        raise Exception("Meta WhatsApp API credentials or template name not set.")
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    data = {
        "messaging_product": "whatsapp",
        "to": phone_number,
        "type": "template",
        "template": {
            "name": template_name,
            "language": {"code": lang_code},
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
    response = requests.post(api_url, headers=headers, json=data)
    return response

if __name__ == "__main__":
    # Example usage: send_whatsapp_ticker to a test number
    from models import User, GPTTickerLog
    from extensions import db
    from datetime import date
    from flask import Flask

    app = Flask(__name__)
    app.config.from_object('config.Config')
    with app.app_context():
        today = date.today()
        # For each user, get the latest ticker for today
        users = User.query.all()
        for user in users:
            if not user.phone:
                continue
            ticker_log = GPTTickerLog.query.filter_by(user_id=user.id).order_by(GPTTickerLog.created_at.desc()).first()
            if ticker_log and ticker_log.created_at.date() == today:
                ticker_text = ticker_log.ticker_text
                resp = send_whatsapp_ticker(user.phone, ticker_text)
                print(f"Sent to {user.phone}: {resp.status_code} {resp.text}")
