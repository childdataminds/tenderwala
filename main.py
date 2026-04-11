from flask import Flask, send_from_directory,render_template,request,jsonify
import json,datetime,random,requests, asyncio, aiohttp
from geopy.geocoders import Nominatim
import pytz,os
from apscheduler.schedulers.background import BackgroundScheduler
# from ApplyQuery import Query
from main_class import TenderWala,cities
from flask_caching import Cache

# from ppra_scraping import Faderal_Scraper


tenderwala = TenderWala()

VERIFY_TOKEN = "tenderwala_secure_2026"

global sent
sent = False
global new_user
new_user = False
global registered_user
registered_user = False
global paid_user
paid_user = False

app = Flask(__name__)
cache = Cache(app, config={'CACHE_TYPE': 'simple'})

# scraper = Faderal_Scraper()

# async def scrape_to_db():
#     scraper.scrap_ppra()
#     for data in scraper.ppra_data:
#         resp = await tenderwala.api.utils.check_tenders(data['tender no'])
#         if not resp:
#             row = [data['tender no'],data['title'],data['city'],data['category'],data['date published'],data['opening date'],data['document link']]
#             resp = await tenderwala.api.utils.insert_tenders(row)
#     return True
            

# def refresh_resources():
#     print("Updating Record!!!")
#     resp = scrape_to_db()
#     print("Record Updated!!!")

# # Configure and start the scheduler
# def start_scheduler():
#     print("Schedular Started!")
#     scheduler = BackgroundScheduler()
#     scheduler.add_job(refresh_resources, 'interval', minutes=1)
#     scheduler.start()

def access_cached_data():
    cached_data = cache.get('view//serve_cached_text')
    if cached_data is None:
        text_content = cities()
        cache.set('view//serve_cached_text', text_content, timeout=300)
        return text_content
    else:
        return cached_data

@cache.cached(timeout=300)  # Cache the response for 300 seconds (5 minutes)
async def serve_cached_text():
    city = cities()
    return city

# @app.route('/register&<phone>')
# def register(phone):
    
#     data = {
#         "categories": [],
#         "cities": [],
#         "phone": "",
#         "status": True
#     }
#     # try:
#     #     phone = security_utils.decode_token(phone)
#     #     data["phone"] = str(phone)
#     # except:
#     #     data["text"] = "Invalid Link:🎙Talk with <a href='https://wa.me/message/MA3ND4FQKM6ZH1' target='_blank'>TenderWala</a> to get link!"
#     #     return render_template('account.html',data=data)
    
#     user_resp = api.utils.get_selected_user(phone)
#     res = api.utils.get_selected_visitor(phone)
#     if user_resp[0]:
#         data["text"] = f"You are already Registered with business name {user_resp[1][-1]}"
#         data['status'] = False
#     elif not user_resp[0] and len(user_resp) == 1:
#         data["text"] = f"👉🏻 Hey {res[1][0]}, Register & Get 15 Days FREE Trial"
#         data['phone'] = phone
#     else:
#         data["text"] = "📨 Unable to fetch your data, please refresh this page!"
#         data["status"] = False
#     if data["status"] == True:
        
#         if not res[0]:
#             data["status"] = False
            
#             data["text"] = "🎙️️Talk to <a href='https://wa.me/message/MA3ND4FQKM6ZH1' target='_blank'>TenderWala</a> on whatsapp to get your registration link"
#             # data["phone"] = ""
#     data["categories"] = categories
#     data["cities"] = access_cached_data()
    
#     return render_template('account.html',data=data)

# @app.route('/submit', methods=['POST'])
# def submit():
#     if request.method == "POST":
#         data = request.form.to_dict()
#         email = data.get('email')
#         business_name = data.get('business_name')
#         categories = data.get('categories')
#         cities = data.get('cities')
        
    
#         if email:
        
#             return "Thank you for submitting your email: {}".format(str(data))
#         else:
      
#             return "Error: Invalid email or email not provided"



@app.route('/')
def main():
    return {"message":"TenderWala Backend is live"}

@app.route('/send_message', methods=['POST'])
def send_message_to_admin():
    data = request.get_json()
    message = data.get('message')
    if message:
        tenderwala.api.sender = "923056842507"  # Admin's phone number
        tenderwala.api.send_message(message)
        return jsonify({"status": "Message sent successfully"})
    else:
        return jsonify({"status": "Error: Phone number and message are required"}), 400


@app.route('/media/<path:filename>')
def serve_media(filename):
    return send_from_directory(
        os.path.join(app.root_path, 'static/images'),
        filename
    )
@app.route('/tenderdocs/<path:filename>')
def tenderdoc(filename):
    return send_from_directory(
        os.path.join(app.root_path, 'static/documents'),
        filename
    )

@app.route('/upload', methods=['POST'])
def upload():
    file = request.files['file']
    file.save(os.path.join("uploads", file.filename))
    return {"status": "uploaded"}



@app.route('/webhook', methods=["GET", "POST"])
def policy_doc():
    global sent
    global new_user
    global registered_user
    global paid_user

    # 🔐 Webhook Verification
    if request.method == "GET":
        token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")

        if token == VERIFY_TOKEN:
            return challenge, 200
        else:
            return "Verification token mismatch", 403

    # 📩 Incoming Messages
    if request.method == "POST":
            resp = request.get_json()

        # try:
            value = resp['entry'][0]['changes'][0]['value']

            if 'messages' not in value:
                return "No message event", 200

            message = value['messages'][0]
            tenderwala.setup(value)
            # 📝 TEXT MESSAGE
            if message['type'] == "text":
                button_msg = False
                msg_text = message['text']['body']
                norm_text = str(msg_text).strip()
                low_text = norm_text.lower()

                txt = ""
                if tenderwala.process_settings_input(msg_text):
                    button_msg = True
                elif low_text.startswith("direct_ask"):
                    query = norm_text[len("direct_ask"):].strip()
                    if query == "":
                        tenderwala.api.send_message("Please send like: direct_ask construction tenders in lahore")
                    else:
                        tenderwala.direct_ask(query)
                    button_msg = True
                elif tenderwala.api.user_type == "PAID": # 5
                        txt = tenderwala.paid_user_func()
                elif tenderwala.api.user_type == "UNPAID": # 4
                        txt = tenderwala.unpaid_user_func()

                elif tenderwala.api.user_type == "VISITOR": # 1 
                    tenderwala.visitor_user_func()
                elif tenderwala.api.user_type == "REGISTERING": # 2
                    tenderwala.registering_user(msg_text)
                elif tenderwala.api.user_type == "TRIAL": # 3   
                    tenderwala.trial_user_func()
                         

   
                sent = True

                # Send reply (IMPORTANT: you must use Meta send API here)
                     if not button_msg:
                         tenderwala.api.send_btn_msg(txt,["Change Settings","Change Language!"])

            # 🔘 BUTTON REPLY
            elif message['type'] == "interactive":
                if message['interactive']['type'] == "button_reply":
                    button_id = message['interactive']['button_reply']['id']
                    title = message['interactive']['button_reply']['title']
                    # print("Button clicked:", button_id)
                    if title == "Change Language!":
                        lang_resp = tenderwala.change_language()
                        if lang_resp[0]:
                            tenderwala.resend_previous_step()
                    elif title == "Contact Us":
                        tenderwala.api.send_message(tenderwala.lang.contact_us)
                    elif title == "Free Demo": 
                        if tenderwala.api.user_type == "VISITOR":
                            resp = tenderwala.api.utils.update_user_status(tenderwala.api.sender,"REGISTERING")
                            if resp[0]:
                                tenderwala.api.send_message("Sending 10 demo tenders.")
                                tenderwala.send_demo_tenders(limit=10)
                                tenderwala.api.send_btn_msg(tenderwala.lang.ask_prov,["All Regions","Contact Us","Change Language!"],["provinces",0,1])
                            else:
                                tenderwala.api.send_message("Unable to start demo right now. Please try again.")
                        else:
                            tenderwala.api.send_message("Free Demo can only be used once.")
                    elif button_id in tenderwala.api.register_steps:
                        if tenderwala.process_settings_all_button(button_id):
                            pass
                        else:
                            tenderwala.register_step_btn_resp(button_id)
                    elif title == "Benefits":
                        tenderwala.benefits()
                    elif title == "Change Settings":
                        tenderwala.change_settings_func()
                    elif title == "Send Tenders":
                        tenderwala.api.send_message("Fetching tenders based on your settings. Please wait...")
                        resp = tenderwala.send_tenders()
                        if resp[0]:
                            pass
                        else:
                            tenderwala.api.send_message(resp[1])
                    elif title == "Bid Documents" or title == "Tender Summary (AI)" or title == "Remind Me!":
                        btn_id_found = True
                        try:
                            tender_id,table,btn_id = str(button_id).split("&&")
                        except:
                            tenderwala.api.send_message(button_id)
                            btn_id_found = False
                        if btn_id_found:
                            if btn_id == "0":
                                tenderwala.download_bid_docs(tender_id,table)
                            elif btn_id == "1":
                                tenderwala.ai_summary(tender_id,table)
                            elif btn_id == "2":
                                tenderwala.remind_me(tender_id,table)
                    elif title == "Get Old Tenders":
                        tables = str(button_id).lower().split(",")
                        resp = tenderwala.send_tenders(old=True,old_table=tables)
                elif message['interactive']['type'] == "list_reply":
                    list_id = message['interactive']['list_reply'].get('id')
                    title = message['interactive']['list_reply'].get('title', "")
                    tenderwala.handle_change_settings_selection(list_id, title)
            tenderwala.api.utils.update_texted_on(tenderwala.api.sender,str(tenderwala.security_utils.get_datetime()))
        # except Exception as e:
        #     api.sender = "923056842507"
        #     api.send_message(f"Webhook Error: {str(e)}")
            # print("Webhook Error:", e)

            return "EVENT_RECEIVED", 200
    
if __name__ == '__main__':
    # start_scheduler()
    app.run()