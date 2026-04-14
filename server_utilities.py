# import smtplib
# from email.mime.multipart import MIMEMultipart
# from email.mime.text import MIMEText
import uuid,json
from backend import *

class Utilities:
    def __init__(self):
        pass
    def session_id(self):
        return str(uuid.uuid4())
    def get_selected_visitor(self,phone):
        payload =  {
            "db":"tenderwala",
            "table":"visitors_table",
            "cols":None,
            "ops":"SELECT",
            "where":["phone"],
            "value":[phone]
        }
        resp = db_execute(payload)
        # print("phone: ",phone)
        # print("selected user resp: ",str(resp))
        if resp['status']:
            if len(resp['data']) > 0:
                return [True,resp['data'][0]]
            else:
                return [False]
        else:
            return [False]
    def insert_into_visitor(self,name,phone,date_):
        payload =  {
            "db":"tenderwala",
            "table":"visitors_table",
            "cols":None,
            "ops":"INSERT",
            "where":None,
            "value":[name,phone,date_]
        }
        resp = db_execute(payload)
        return resp
    def get_selected_user(self,phone):
        payload =  {
            "db":"tenderwala",
            "table":"users_table",
            "cols":None,
            "ops":"SELECT",
            "where":["phone"],
            "value":[phone]
        }
        resp = db_execute(payload)
        if resp['status']:
            if len(resp['data']) > 0:
                return [True,resp['data'][0]]
            else:
                return [False]
        else:
            return [False,"اس وقت آپ کی معلومات حاصل کرنا ممکن نہیں ہے ۔ اگر آپ پہلے سے رجسٹر نہیں ہیں تو اپنی رجسٹریشن کا عمل مکمل کریں اور ٹینڈر کی صحولیات حاصل کریں"]
    def insert_into_user(self,name,phone,date_,status):
        payload =  {
            "db":"tenderwala",
            "table":"users_table",
            "cols":["phone","join_date","name","status","lang"],
            "ops":"INSERT",
            "where":None,
            "value":[phone,date_,name,status,"ur"]
        }
        resp = db_execute(payload)
        return resp
    def update_texted_on(self,phone,time):
        payload =  {
            "db":"tenderwala",
            "table":"users_table",
            "cols":["last_texted_on"],
            "ops":"UPDATE",
            "where":["phone"],
            "value":[time,phone]
        }
        resp = db_execute(payload)
        return resp
    def change_language(self,phone,lang):
        if lang == "ur":
             new_lang = "en"
        else:
             new_lang = "ur"
        payload =  {
            "db":"tenderwala",
            "table":"users_table",
            "cols":["lang"],
            "ops":"UPDATE",
            "where":["phone"],
            "value":[new_lang,phone]
        }
        resp = db_execute(payload)
      
        try:
          
           if resp["status"]:
              return True,""
        except:
              return False,resp
        
    def get_unregistered_users(self):
        payload =  {
            "db":"tenderwala",
            "table":"users_table",
            "cols":None,
            "ops":"SELECT",
            "where":["status"],
            "value":['visitor', 'registering']
        }
        resp = db_execute(payload)
        if resp['status']:
            if len(resp['data']) > 0:
                return [True, resp['data']]
            else:
                return [False]
    def update_user_status(self,phone,status):
         
         status_norm = str(status).strip().upper()

         if status_norm == "TRIAL":
            from datetime import datetime, timedelta
            sub_date = (datetime.now() + timedelta(days=3)).isoformat(sep=" ", timespec="seconds")
            payload = {
                "db": "tenderwala",
                "table": "users_table",
                "cols": ["subs_date"],
                "ops": "UPDATE",
                "where": ["phone"],
                "value": [sub_date, phone]
            }
            resp = db_execute(payload)

         payload =  {
            "db":"tenderwala",
            "table":"users_table",
            "cols":["status"],
            "ops":"UPDATE",
            "where":["phone"],
            "value":[status,phone]
         }
         resp = db_execute(payload)
        
         if resp["status"]:
              return True,""
         else:
              return False,resp
         
    def insert_into_imgs(self,title,id_,date_):
        payload =  {
            "db":"tenderwala",
            "table":"manage_images",
            "cols":None,
            "ops":"INSERT",
            "where":None,
            "value":[title,id_,date_]
        }
        resp = db_execute(payload)
        return resp
    def get_imgs(self,title):
        payload =  {
            "db":"tenderwala",
            "table":"manage_images",
            "cols":None,
            "ops":"SELECT",
            "where":["title"],
            "value":[title]
        }
        resp = db_execute(payload)
        if resp["status"]:
           if len(resp["data"]) > 0:
               return [True,resp["data"][0]]
           else:
               return [False]
        else:
            return [False,str(resp)]
    def update_img_ids(self,title,id_,date_):
        payload =  {
            "db":"tenderwala",
            "table":"manage_images",
            "cols":["title"],
            "ops":"UPDATE",
            "where":["img_id","expiry_date"],
            "value":[title,id_,date_]
        }
        resp = db_execute(payload)
        if resp["status"]:
           
               return [True]
           
        else:
            return [False]
    def insert_into_filters(self,phone,col,data,available=False):
        if available:
           where = ["phone"]
           value = [data,phone]
           cols = [col]
           ops = "UPDATE"
        else:
           where = None
           value = [phone,data]
           cols = ["phone",col]
           ops = "INSERT"
        payload =  {
            "db":"tenderwala",
            "table":"filters_table",
            "cols":cols,
            "ops":ops,
            "where":where,
            "value":value
        }
        resp = db_execute(payload)
        return resp
    def get_filters(self,phone=None):
        payload =  {
            "db":"tenderwala",
            "table":"filters_table",
            "cols":["phone","provinces","types","punjab_cities","sindh_cities","kpk_cities","ajk_cities","balochistan_cities","gilgit_cities","categories"],
            "ops":"SELECT",
            "where":["phone"],
            "value":[phone]
        }
        if phone == None:
            payload["where"] = None
            payload["value"] = None
        resp = db_execute(payload)
        if resp["status"]:
           if len(resp["data"]) > 0:
               return [True,resp["data"][0]]
           else:
               return [False]
        else:
            return [False,str(resp)]
    def get_tenders(self,table,col,where=None,value=None):
        payload =  {
            "db":"tenderwala",
            "table":table,
            "cols":col,
            "ops":"SELECT",
            "where":where,
            "value":value
        }
        
        resp = db_execute(payload)
        if resp["status"]:
           if len(resp["data"]) > 0:
               return [True,resp["data"]]
           else:
               return [False]
        else:
            return [False,str(resp)]
    def delete_tender(self,table,id_):
        payload =  {
            "db":"tenderwala",
            "table":table,
            "cols":None,
            "ops":"DELETE",
            "where":["id"],
            "value":[id_]
        }
        resp = db_execute(payload)
        if resp["status"]:
            return [True]
        else:
            return [False,str(resp)]
    def insert_into_tenders(self,table,value):
        payload =  {
            "db":"tenderwala",
            "table":table,
            "cols":None,
            "ops":"INSERT",
            "where":None,
            "value":value
        }
        resp = db_execute(payload)
        return resp
    def update_tenders_sent_to(self,table,sent_to,id_):
        payload =  {
            "db":"tenderwala",
            "table":table,
            "cols":["sent_to"],
            "ops":"UPDATE",
            "where":["id"],
            "value":[sent_to,id_]
        }
        resp = db_execute(payload)
        return resp
    
    def get_unpaid_users(self):
        payload = {
            "db": "tenderwala",
            "table": "users_table",
            "cols": None,  # Fetch all columns
            "ops": "SELECT",
            "where": ['status'],  # No filters to fetch all users
            "value": ['unpaid']
        }
        resp = db_execute(payload)
        if resp["status"]:
            if len(resp["data"]) > 0:
                return [True, resp["data"]]
            else:
                return [False, "No users found."]
        else:
            return [False, str(resp)]
        
    def get_trial_over_users(self):
        from datetime import datetime
        current_date = datetime.now().strftime('%Y-%m-%d')

        payload = {
            "db": "tenderwala",
            "table": "users_table",
            "cols": None,  # Fetch all columns
            "ops": "SELECT",
            "where": ["status", "subs_date !="],
            "value": ["trial", current_date]
        }
        resp = db_execute(payload)
        if resp["status"]:
            if len(resp["data"]) > 0:
                return [True, resp["data"]]
            else:
                return [False, "No users found."]
        else:
            return [False, str(resp)]
    
    

        
#     def send_email(self,to_email, subject, message):
#         # Set up the SMTP server
#         smtp_server = 'mail.pacificproduction.pk'  # Change this to your SMTP server
#         smtp_port = 993  # Change this to your SMTP port
#         smtp_username = 'tenderwala@pacificproduction.pk'  # Change this to your email username
#         smtp_password = 'Mr@03056842507'  # Change this to your email password
    
#         # Create message container
#         msg = MIMEMultipart()
#         msg['From'] = smtp_username
#         msg['To'] = to_email
#         msg['Subject'] = subject
    
#         # Attach message
#         msg.attach(MIMEText(message, 'plain'))
    
#         # Create SMTP session
#         server = smtplib.SMTP(smtp_server, smtp_port)
#         server.starttls()
#         server.login(smtp_username, smtp_password)
    
#         # Send the message
#         server.sendmail(smtp_username, to_email, msg.as_string())
#         server.quit()

