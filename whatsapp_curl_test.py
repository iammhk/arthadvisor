import requests

url = "https://graph.facebook.com/v22.0/728214020370908/messages"
access_token = "EAAU8wLq0epYBPIc1oSrkC9k7TvQWqVXWi7A3nkDLemY2768utEo5hDAGhTbeHWbyZAIEOtK3ngGC93yqL39ghfWzAsVjAwfv4ci8TvIqIXlXkolTWj0EmpG5qZAxmmqemmz1DpwYNxyhZCP7dTnrcJt5Kye8x1OOEt6C3M1RA6m4vAM9ZCgoOEHxsCtHi2wAwWJJpZCJ1GXrteh9V06DxjFkO72zcBAnTDD5jOYAa"

headers = {
    "Authorization": f"Bearer {access_token}",
    "Content-Type": "application/json"
}

data = {
    "messaging_product": "whatsapp",
    "to": "918948889878",
    "type": "template",
    "template": {
        "name": "mrkt_global_advice",
        "language": {"code": "en"}
    }
}

response = requests.post(url, headers=headers, json=data)
print("Status Code:", response.status_code)
print("Response:", response.text)