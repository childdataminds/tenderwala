import requests
import json
from server_utilities import Utilities,categories,cities,prov_cities,province,types,prov_indexes

class metaWhatsappAPI:
    def __init__(self) -> None:
        
        self.access_token = "EAANNvSk9ZB0kBQqZAdXS5CLiltHMlQmUSHJ2GZAukFoZATiSkKWNlKpWm7mrclGNYnNZAZBKF6oD9EI58O1gn4U748q8Vx1H4l8OZBE1HTV4jFq2hSnRTJ2SFfJc143k0gRY4qBB1UBd65rVbS2mhakwoG46S0nC4LhrHY6XSRDTjbsZA9bgO32bsniDsaL9SgZDZD"
        self.phone_number_id = "966849733185169"
        self.wa_business_id = "1603869097312326"
        
        self.base_url = f"https://graph.facebook.com/v22.0/{self.phone_number_id}/messages"
        
        self.headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        self.sender = None
        self.sender_name = None
        self.user_type = None
        self.utils = Utilities()
        self.available_template_messages = {
            "welcome_msg": {
                "body_params": []
            },
            "renewal_reminder": {
                "body_params": ["plan_name", "renewal_date"]
            },
            "renewal_confirmation": {
                "body_params": ["user_name", "plan_name"]
            },
            "payment_success": {
                "body_params": ["plan_name"],
                "buttons": [
                    {"sub_type": "quick_reply", "parameter_type": "payload"}
                ]
            },
            "complete_registration": {
                "body_params": [],
                "buttons": [
                    {"sub_type": "quick_reply", "parameter_type": "payload"},
                    {"sub_type": "quick_reply", "parameter_type": "payload"}
                ]
            },
            "re_join": {
                "body_params": [],
                "buttons": [
                    {"sub_type": "quick_reply", "parameter_type": "payload"},
                    {"sub_type": "quick_reply", "parameter_type": "payload"},
                    {"sub_type": "quick_reply", "parameter_type": "payload"}
                ]
            },
            "more_tenders": {
                "body_params": ["remaining_tenders"],
                "buttons": [
                    {"sub_type": "quick_reply", "parameter_type": "payload"}
                ]
            },
            "status_updated": {
                "body_params": ["status_string", "function_status"]
            },
            "remind_tender": {
                "header_params": ["header_text"],
                "body_params": [
                    "title",
                    "opening_date",
                    "department",
                    "city",
                    "remaining_days_and_hours"
                ],
                "buttons": [
                    {"sub_type": "quick_reply", "parameter_type": "payload"},
                    {"sub_type": "quick_reply", "parameter_type": "payload"}
                ]
            },
            "send_tenders": {
                "body_params": [
                    "title",
                    "publish_date",
                    "opening_date",
                    "department",
                    "city",
                    "note"
                ],
                "buttons": [
                    {"sub_type": "quick_reply", "parameter_type": "payload"},
                    {"sub_type": "quick_reply", "parameter_type": "payload"},
                    {"sub_type": "quick_reply", "parameter_type": "payload"}
                ]
            }
        }
        
        self.register_steps = ["provinces","types","punjab_cities","sindh_cities","kpk_cities","ajk_cities","balochistan_cities","gilgit_cities","categories"]

    def _coerce_template_values(self, provided_values, required_keys=None):
        required_keys = required_keys or []
        required_count = len(required_keys)

        if isinstance(provided_values, dict):
            ordered = []
            for index, key in enumerate(required_keys):
                ordered.append(
                    provided_values.get(
                        key,
                        provided_values.get(str(key), provided_values.get(index, provided_values.get(str(index), "")))
                    )
                )
            return ordered

        if provided_values is None:
            values = []
        elif isinstance(provided_values, (list, tuple)):
            values = list(provided_values)
        else:
            values = [provided_values]

        if required_count > 0:
            if len(values) < required_count:
                values.extend([""] * (required_count - len(values)))
            elif len(values) > required_count:
                values = values[:required_count]

        return values
        
    # ------------------ TEXT MESSAGE ------------------
    def send_message(self, text):

        payload = {
            "messaging_product": "whatsapp",
            "to": self.sender,
            "type": "text",
            "text": {
                "body": text
            },
            "footer": {
                    "text": "Powered by DataMinds!"
                }
        }

        response = requests.post(self.base_url, headers=self.headers, json=payload)
        # print(response.json())
        return response.status_code == 200

    # ------------------ TEMPLATE MESSAGE ------------------
    def send_template_msg(self, temp_name, body_params=None, button_payloads=None, language_code="en", button_sub_type="quick_reply", header_params=None):
        template_meta = self.available_template_messages.get(temp_name, {})
        header_fields = template_meta.get("header_params", [])
        body_fields = template_meta.get("body_params", [])
        button_meta = template_meta.get("buttons", [])

        header_params = self._coerce_template_values(header_params, header_fields)
        body_params = self._coerce_template_values(body_params, body_fields)
        button_payloads = self._coerce_template_values(button_payloads, list(range(len(button_meta))))

        template = {
            "name": temp_name,
            "language": {
                "code": language_code
            }
        }

        components = []
        if len(header_params) > 0:
            components.append({
                "type": "header",
                "parameters": [
                    {
                        "type": "text",
                        "text": str(param)
                    }
                    for param in header_params
                ]
            })
        if len(body_params) > 0:
            components.append({
                "type": "body",
                "parameters": [
                    {
                        "type": "text",
                        "text": str(param)
                    }
                    for param in body_params
                ]
            })

        for index, payload_value in enumerate(button_payloads):
            current_button_meta = button_meta[index] if index < len(button_meta) else {}
            current_sub_type = current_button_meta.get("sub_type", button_sub_type)
            parameter_type = current_button_meta.get("parameter_type", "payload")
            parameter_value = payload_value

            if isinstance(payload_value, dict):
                current_sub_type = payload_value.get("sub_type", current_sub_type)
                parameter_type = payload_value.get("parameter_type", parameter_type)
                if parameter_type == "text":
                    parameter_value = payload_value.get("text", payload_value.get("value", ""))
                else:
                    parameter_value = payload_value.get("payload", payload_value.get("value", ""))

            if parameter_type == "text":
                button_parameter = {
                    "type": "text",
                    "text": str(parameter_value)
                }
            else:
                button_parameter = {
                    "type": "payload",
                    "payload": str(parameter_value)
                }

            components.append({
                "type": "button",
                "sub_type": current_sub_type,
                "index": str(index),
                "parameters": [button_parameter]
            })

        if len(components) > 0:
            template["components"] = components

        payload = {
            "messaging_product": "whatsapp",
            "to": self.sender,
            "type": "template",
            "template": template
        }

        response = requests.post(self.base_url, headers=self.headers, json=payload)
        # print(response.json())
        return response.status_code == 200
    def upload_media(self,image):
          image_path = f"files/{image}"
          url = f"https://graph.facebook.com/v22.0/{self.phone_number_id}/media"


          files = {
             "file": (image, open(image_path, "rb"), "image/png"),
             "type": (None, "image/png"),
             "messaging_product": (None, "whatsapp")
           }
 
          response = requests.post(url, headers=self.headers, files=files)
          print("Upload Media: ",response.json())
          return response.json().get("id")
    # ------------------ DOCUMENT MESSAGE ------------------
    def send_document_msg_by_url(self, type_, url,cap="",filename="Untitled"):
        # types: document, image
        payload = {
            "messaging_product": "whatsapp",
            "to": self.sender,
            "type": type_,
            type_: {
                "link": url,
                "caption": cap
            }
        }
        if type_ == "document":
            payload[type_]["filename"] = filename

        response = requests.post(self.base_url, headers=self.headers, json=payload)
        # print(response.json())
        return response.status_code == 200
    def send_document_msg_by_id(self, type_, id_,cap):
        # types: document, image
        payload = {
            "messaging_product": "whatsapp",
            "to": self.sender,
            "type": type_,
            type_: {
                "id": id_,
                "caption": cap,
               
            }
        }

        response = requests.post(self.base_url, headers=self.headers, json=payload)
        print("send_doc: ",response.json())
        return response.status_code == 200

    # ------------------ BUTTON MESSAGE ------------------
    def send_btn_msg(self, txt, btn_list,index_list = []):
        btns = []
        c = 0
        for btn in btn_list:
            if len(index_list) > 0:
                 x = index_list[c]
            else:
               x = c            
            btns.append({
                            "type": "reply",
                            "reply": {
                                "id": str(x),
                                "title": btn
                            }})
            c += 1
        payload = {
            "messaging_product": "whatsapp",
            "to": self.sender,
            "type": "interactive",
            "interactive": {
                "type": "button",
                "body": {
                    "text": txt
                },
                "footer": {
                    "text": "Powered by DataMinds!"
                },
                "action": {
                    "buttons": btns
                }
            }
        }

        response = requests.post(self.base_url, headers=self.headers, json=payload)
        # print(response.json())
        return response.status_code == 200

    # ------------------ LIST MESSAGE ------------------
    def send_list_msg(self,title,sections):
        c = 1
        sect_list = []
        for sect in sections:
            sect_list.append({
                            "id": str(c),
                            "title": sect
                                })
            c += 1
        payload = {
            "messaging_product": "whatsapp",
            "to": self.sender,
            "type": "interactive",
            "interactive": {
                "type": "list",
                "body": {
                    "text": title
                },
                "action": {
                    "button": "Choose one",
                    "sections": [{
                    "title": "Options",
                    "rows":sect_list }
                               ]
                        }
                    
                }
            }
        

        response = requests.post(self.base_url, headers=self.headers, json=payload)
        # print(response.json())
        return response.status_code == 200

    # ------------------ URL BUTTON MESSAGE ------------------
    def send_url_btn_msg(self, txt, url, displayName):

        payload = {
            "messaging_product": "whatsapp",
            "to": self.sender,
            "type": "interactive",
            "interactive": {
                "type": "cta_url",
                "body": {
                    "text": txt
                },
                "action": {
                    "name": "cta_url",
                    "parameters": {
                        "display_text": displayName,
                        "url": url
                    }
                }
            }
        }

        response = requests.post(self.base_url, headers=self.headers, json=payload)
        # print(response.json())
        return response.status_code == 200

    # ------------------ GET TEMPLATES ------------------
    def get_whatsapp_templates(self):

        url = f"https://graph.facebook.com/v22.0/{self.wa_business_id}/message_templates"

        response = requests.get(url, headers=self.headers)
        try:
            payload = response.json()
            if isinstance(payload, dict):
                payload["available_template_messages"] = self.available_template_messages
            return payload
        except Exception:
            return {"available_template_messages": self.available_template_messages}
        
    




# TEMPLATES:
# welcome_msg
# renewal_reminder
# renewal_confirmation
# payment_success
