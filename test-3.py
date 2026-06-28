import requests

bizGo = "EAASsBF1sVBsBRqcoeRpsIcn5Te3t1jAXKZAGqdlEm0SRyEWt3iqpZB3628UAZCQZAj9sVbFn16ZBDGYOo8M0QZAHzbYKgS7pXWqEQDKUV4jtaBKjMJOUFeF8n3E30ta32uRBx8u77boR8s39k7Yr921Lb0gZAkFXK0wkIGZC1gVGxXrFBRRog8Hiv7ZBkdVF7tXyEY2D4xsqfyeW1ZBWlfmPlHPnj9ckNIUTHSl6MBW0hTEK4VQnS6fDxy64ZBZB7yhVAl1hZBChOtDqZBOu7j6Kug6ZBv3xwZC1ExwC6PGgcQZDZD"
phone_number_id = "1075364032336457"
wa_business_id = "1800540957787205"
verify_token = "bizgo_secure_2026"
base_url = f"https://graph.facebook.com/v22.0/{phone_number_id}/messages"
        
headers = {
    "Authorization": f"Bearer {bizGo}",
    "Content-Type": "application/json"
}
payload = {
            "messaging_product": "whatsapp",
            "to": "923056842507",
            "type": "text",
            "text": {
                "body": "Hi There!"
            },
            "footer": {
                    "text": "Powered by DataMinds!"
                }
        }

response = requests.post(base_url, headers=headers, json=payload)
print(response.json())
