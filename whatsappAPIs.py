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
        
        self.register_steps = ["provinces","types","punjab_cities","sindh_cities","kpk_cities","ajk_cities","blochi_cities","gilgit_cities","categories"]
        
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
    def send_template_msg(self,temp_name):

        payload = {
            "messaging_product": "whatsapp",
            "to": self.sender,
            "type": "template",
            "template": {
                "name": temp_name,
                "language": {
                    "code": "en"
                },
                # "components": [
                #     {
                #         "type": "button",
                #         "sub_type": "url",
                #         "index": "0",
                #         "parameters": [
                #             {
                #                 "type": "text",
                #                 "text": " "
                #             }
                #         ]
                #     }
                # ]
            }
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
            return response.json()
        except Exception:
            return {}




# TEMPLATES:
# welcome_msg
# renewal_reminder
# renewal_confirmation
# payment_success