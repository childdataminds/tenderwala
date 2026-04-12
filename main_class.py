from whatsappAPIs import metaWhatsappAPI,categories,cities,province,prov_cities,types,prov_indexes
from msg_templates import Urdu,English
from utils import ScrapingUtils
from backend import db_execute
import threading
import os
import re
import json
import pickle
import requests
import tempfile
import datetime
import zipfile
from uuid import uuid4
from urllib.parse import unquote, urljoin
from sindh_ppra import Sindh_Scrapper

# Hardcoded OpenAI config.
# Paste your API key below to enable OpenAI features without env vars.
HARDCODED_OPENAI_API_KEY = "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"
HARDCODED_OPENAI_MODEL = "gpt-4o-mini"

class TenderWala:
    def __init__(self):
        self.security_utils = ScrapingUtils()
        self.api = metaWhatsappAPI()
        self.img_url = "https://tenderwala.thedataminds.us/media/"
        self.settings_edit_context = {}
    def setup(self,value):
        message = value['messages'][0]
        self.api.sender = message['from']
        self.api.sender_name = str(value['contacts'][0]['profile']['name'])
        user_resp = self.api.utils.get_selected_user(self.api.sender)
        self.paid_user = False
        self.registered_user = False
        self.new_user = False
        if not user_resp[0]:
                user_resp = self.api.utils.insert_into_user(
                    self.api.sender_name,
                    str(self.api.sender),
                    self.security_utils.get_datetime(),
                    "VISITOR"
                )
                self.api.user_type = "VISITOR"
                lang_ = "ur"
        else:
                # print("resp: ",user_resp[1])
                self.api.user_type = user_resp[1][2]
                lang_ = "ur"
                if len(user_resp[1]) > 6 and str(user_resp[1][6]).strip().lower() in ["ur", "en"]:
                    lang_ = str(user_resp[1][6]).strip().lower()
            
        if lang_ == "ur":
                self.lang = Urdu()
        else:
                self.lang = English()
            

        self.lang.sender = self.api.sender
        self.lang.user = self.api.sender_name
        self.lang.messages()

        self.is_prov_cities = False
        self.available = True
        self.filter_data = None
        self.filters_list = self.api.register_steps[1:]
    def paid_user_func(self):
        name = self.api.sender_name if self.api.sender_name else "Customer"
        txt = f"""
Welcome back, {name}!

Your TenderWala account is active and ready.
Available functions:
1- Send Tenders
2- Change Settings
3- Change Language
4- direct_ask <your requirement>
"""
        self.paid_user = True
        return txt
    def unpaid_user_func(self):
        name = self.api.sender_name if self.api.sender_name else "Customer"
        if self.lang.type == "ur":
            txt = f"""
{name}, aap ki subscription active nahi hai.

Tenders dobara receive karne ke liye apni subscription renew/subscribe karein.
Madad ke liye Contact Us par reply karein.
"""
        else:
            txt = f"""
{name}, your subscription is currently inactive.

Please subscribe again to continue receiving daily tenders.
Reply with Contact Us if you need assistance.
"""
        self.registered_user = True
        return txt
    def visitor_user_func(self):
        if not self.new_user:
            txt = self.lang.new_user_1
            self.new_user = True
        else:
            txt = self.lang.new_user_2

        # resp_img_id = self.api.utils.get_imgs("welcome")
        # print("imgs db resp: ", resp_img_id)
        # send_img = False
        # if resp_img_id[0]:
        #      if not security_utils.check_expiry(resp_img_id[1][-1]):
        #          img_id = resp_img_id[1][1]
        #          send_img = True
        # if not send_img:
        #        img_id = self.api.upload_media("Welcome.png")
        #        resp = self.api.utils.insert_into_imgs("welcome",img_id,security_utils.get_expiry_date(30))
        #        print("insert into imgs db: ",resp)
        #        send_img = True
        # if send_img:
        #      self.api.send_document_msg_by_id("image",img_id)
        self.api.send_document_msg_by_url("image",f"{self.img_url}Welcome.png","")
        
                    

        self.api.send_btn_msg(
            txt,
            ["Free Demo","Change Language!","Contact Us"]
        )
    def _registration_input_help(self, invalid_value=None):
        if self.lang.type == "ur":
            if invalid_value is None:
                return (
                    "Aap ka input samajh nahi aaya. "
                    "Barah-e-karam sirf numbers comma ke sath bhejein (misal: 1,3) ya ALL likhein."
                )
            return (
                f"Yeh value durust nahi hai: {invalid_value}. "
                "Barah-e-karam sahi serial numbers bhejein (misal: 1,3) ya ALL likhein."
            )
        if invalid_value is None:
            return "I could not understand your input. Please send valid serial numbers (example: 1,3) or type ALL."
        return f"Invalid value: {invalid_value}. Please send valid serial numbers (example: 1,3) or type ALL."

    def _is_filter_value_set(self, value):
        if value is None:
            return False
        text = str(value).strip().lower()
        return text not in ["", "empty", "none", "null"]

    def _normalized_selection_value(self, parsed_value):
        if isinstance(parsed_value, str) and parsed_value.strip().lower() == "all":
            return "all"
        if isinstance(parsed_value, list):
            return ",".join([str(x).strip() for x in parsed_value if str(x).strip() != ""])
        return str(parsed_value).strip()

    def _send_registration_next_step_from_filter(self, filter_data):
        name, col, _, _ = self.security_utils.cities_selection_logic(
            filter_data,
            self.lang.province,
            self.filters_list[1:]
        )

        if name is not None and col is not None:
            col_name = col[0]
            step_msg = self.lang.choose_from_img(name[0])
            if col_name == "categories":
                self.api.send_document_msg_by_url("image", f"{self.img_url}categories.png", step_msg)
            else:
                self.api.send_document_msg_by_url("image", f"{self.img_url}{col_name}.png", step_msg)
            return True

        if not self._is_filter_value_set(filter_data[2]):
            self.api.send_btn_msg(self.lang.ask_types, ["All Types", "Contact Us", "Change Language!"], ["types", 0, 1])
            return True

        return False

    def _send_registration_next_step(self):
        filters_resp = self.api.utils.get_filters(self.api.sender)
        if not filters_resp[0]:
            self.api.send_btn_msg(self.lang.ask_prov, ["All Regions", "Contact Us", "Change Language!"], ["provinces", 0, 1])
            return False
        return self._send_registration_next_step_from_filter(filters_resp[1])

    def registering_user(self,msg_text):
        filters_resp = self.api.utils.get_filters(self.api.sender)

        if not filters_resp[0]:
            col = "provinces"
            input_resp = self.security_utils.get_numbers_list(msg_text, province)
            if input_resp[0]:
                selected_value = self._normalized_selection_value(input_resp[1])
                resp = self.api.utils.insert_into_filters(self.api.sender, col, selected_value, False)
                if resp.get("status"):
                    self.api.send_message(self.lang.province_success)
                    if not self._send_registration_next_step():
                        self.api.send_btn_msg(self.lang.ask_types, ["All Types", "Contact Us", "Change Language!"], ["types", 0, 1])
                else:
                    self.api.send_message("Unable to save your region right now. Please try again.")
                return

            invalid_value = None if input_resp[1] is None else str(input_resp[1])
            self.api.send_message(self._registration_input_help(invalid_value))
            self.api.send_btn_msg(self.lang.ask_prov, ["All Regions", "Contact Us", "Change Language!"], ["provinces", 0, 1])
            return

        filter_data = filters_resp[1]
        name, col, _, _ = self.security_utils.cities_selection_logic(filter_data, self.lang.province, self.filters_list[1:])

        if name is not None and col is not None:
            target_col = col[0]
            input_resp = self.security_utils.get_numbers_list(msg_text, prov_cities[target_col]["list"])
            if input_resp[0]:
                selected_value = self._normalized_selection_value(input_resp[1])
                resp = self.api.utils.insert_into_filters(self.api.sender, target_col, selected_value, True)
                if not resp.get("status"):
                    resp = self.api.utils.insert_into_filters(self.api.sender, target_col, selected_value, False)

                if resp.get("status"):
                    self.api.send_message(self.lang.province_success)
                    self._send_registration_next_step()
                else:
                    self.api.send_message("Unable to save your selection right now. Please try again.")
                return

            invalid_value = None if input_resp[1] is None else str(input_resp[1])
            self.api.send_message(self._registration_input_help(invalid_value))
            step_msg = self.lang.choose_from_img(name[0])
            if target_col == "categories":
                self.api.send_document_msg_by_url("image", f"{self.img_url}categories.png", step_msg)
            else:
                self.api.send_document_msg_by_url("image", f"{self.img_url}{target_col}.png", step_msg)
            return

        input_resp = self.security_utils.get_numbers_list(msg_text, types)
        if input_resp[0]:
            selected_value = self._normalized_selection_value(input_resp[1])
            resp = self.api.utils.insert_into_filters(self.api.sender, "types", selected_value, True)
            if not resp.get("status"):
                resp = self.api.utils.insert_into_filters(self.api.sender, "types", selected_value, False)

            if resp.get("status"):
                self.api.send_message(self.lang.province_success)
                self.api.send_btn_msg(self.lang.register_success, ["Send Tenders", "Contact Us", "Change Language!"])
                self.api.utils.update_user_status(self.api.sender, "TRIAL")
            else:
                self.api.send_message("Unable to save contract type right now. Please try again.")
            return

        invalid_value = None if input_resp[1] is None else str(input_resp[1])
        self.api.send_message(self._registration_input_help(invalid_value))
        self.api.send_btn_msg(self.lang.ask_types, ["All Types", "Contact Us", "Change Language!"], ["types", 0, 1])
    
    def benefits(self):
        self.api.send_document_msg_by_url("image",f"https://tenderwala.thedataminds.us/media/benefits.png","")
    def trial_user_func(self):
        self.api.send_btn_msg(self.lang.register_success,["Send Tenders","Benefits","Change Language!"])

    def _set_runtime_language(self, lang_code):
        code = str(lang_code).strip().lower()
        if code == "ur":
            self.lang = Urdu()
        else:
            self.lang = English()
        self.lang.sender = self.api.sender
        self.lang.user = self.api.sender_name
        self.lang.messages()

    def _resend_settings_step(self):
        self._ensure_settings_context()
        ctx = self.settings_edit_context.get(self.api.sender)
        if not ctx:
            return False

        selected_col = ctx.get("col")
        if selected_col is None:
            self.change_settings_func()
            return True

        info = self._settings_target_info(selected_col)
        if selected_col == "categories":
            self.api.send_document_msg_by_url("image", f"{self.img_url}categories.png", info["step_msg"])
            self.api.send_btn_msg(
                "You can also choose all categories.",
                [info["all_btn_title"], "Contact Us", "Change Language!"],
                [info["all_btn_id"], 0, 1]
            )
        else:
            self.api.send_btn_msg(
                info["step_msg"],
                [info["all_btn_title"], "Contact Us", "Change Language!"],
                [info["all_btn_id"], 0, 1]
            )
        return True

    def _resend_registration_step(self):
        filters_resp = self.api.utils.get_filters(self.api.sender)
        if not filters_resp[0]:
            self.api.send_btn_msg(self.lang.ask_prov,["All Regions","Contact Us","Change Language!"],["provinces",0,1])
            return True

        filter_data = filters_resp[1]
        if self._send_registration_next_step_from_filter(filter_data):
            return True

        self.api.send_btn_msg(self.lang.register_success, ["Send Tenders", "Contact Us", "Change Language!"])
        return True

    def resend_previous_step(self):
        if self._resend_settings_step():
            return True

        user_type = str(self.api.user_type).upper() if self.api.user_type is not None else ""
        if user_type == "REGISTERING":
            return self._resend_registration_step()
        if user_type == "TRIAL":
            self.trial_user_func()
            return True
        if user_type == "VISITOR":
            self.visitor_user_func()
            return True
        if user_type == "PAID":
            self.api.send_btn_msg(self.paid_user_func(), ["Change Language!"])
            return True
        if user_type == "UNPAID":
            self.api.send_btn_msg(self.unpaid_user_func(), ["Change Language!"])
            return True
        return False

    def change_language(self):
        new_lang = "en" if self.lang.type == "ur" else "ur"
        resp = self.api.utils.change_language(self.api.sender,self.lang.type)
        if resp[0]:
            self._set_runtime_language(new_lang)
            if new_lang == "en":
                lang_msg = "Your language has been changed to English."
            else:
                lang_msg = "میں اب آپ سے اردو میں بات کروں گا 🤩"
            self.api.send_message(lang_msg)
            return [True, new_lang]
        else:
            self.api.send_btn_msg(str(resp[1]),["Contact Us"])
            return [False, str(resp[1])]
    def _ensure_settings_context(self):
        if not hasattr(self, "settings_edit_context"):
            self.settings_edit_context = {}

    def _settings_target_info(self, col):
        if col == "provinces":
            return {
                "items": province,
                "step_msg": self.lang.ask_prov,
                "all_btn_title": "All Regions",
                "all_btn_id": "provinces",
            }
        if col == "types":
            return {
                "items": types,
                "step_msg": self.lang.ask_types,
                "all_btn_title": "All Types",
                "all_btn_id": "types",
            }
        return {
            "items": prov_cities["categories"]["list"],
            "step_msg": self.lang.choose_from_img("Categories"),
            "all_btn_title": "All Categories",
            "all_btn_id": "categories",
        }

    def _send_settings_city_prompt(self, city_col, city_name):
        step_msg = self.lang.choose_from_img(city_name)
        self.api.send_document_msg_by_url(
            "image",
            f"{self.img_url}{city_col}.png",
            step_msg
        )

    def _start_settings_city_flow(self):
        filters_resp = self.api.utils.get_filters(self.api.sender)
        if not filters_resp[0]:
            return False

        filter_data = filters_resp[1]
        name, col, _, _ = self.security_utils.cities_selection_logic(
            filter_data,
            self.lang.province,
            self.filters_list[1:]
        )
        if name is None or col is None:
            return False

        self.settings_edit_context[self.api.sender] = {
            "col": "provinces",
            "mode": "cities",
            "city_col": col[0]
        }
        self._send_settings_city_prompt(col[0], name[0])
        return True

    def change_settings_func(self):
        self._ensure_settings_context()
        self.settings_edit_context[self.api.sender] = {"col": None}
        self.api.send_list_msg(
            "Choose setting category:",
            ["Provinces", "Categories", "Types"]
        )

    def handle_change_settings_selection(self, list_id, title):
        self._ensure_settings_context()
        map_by_id = {
            "1": "provinces",
            "2": "categories",
            "3": "types"
        }

        selected_col = map_by_id.get(str(list_id).strip())
        if selected_col is None:
            title_text = str(title).strip().lower()
            if "province" in title_text:
                selected_col = "provinces"
            elif "categor" in title_text:
                selected_col = "categories"
            elif "type" in title_text:
                selected_col = "types"

        if selected_col is None:
            self.api.send_message("Invalid setting selection. Please choose Provinces, Categories, or Types.")
            return [False, "invalid_selection"]

        self.settings_edit_context[self.api.sender] = {"col": selected_col}
        info = self._settings_target_info(selected_col)

        if selected_col == "categories":
            self.api.send_document_msg_by_url("image", f"{self.img_url}categories.png", info["step_msg"])
            self.api.send_btn_msg(
                "You can also choose all categories.",
                [info["all_btn_title"], "Contact Us", "Change Language!"],
                [info["all_btn_id"], 0, 1]
            )
        else:
            self.api.send_btn_msg(
                info["step_msg"],
                [info["all_btn_title"], "Contact Us", "Change Language!"],
                [info["all_btn_id"], 0, 1]
            )
        return [True]

    def process_settings_input(self, msg_text):
        self._ensure_settings_context()
        ctx = self.settings_edit_context.get(self.api.sender)
        if not ctx:
            return False

        selected_col = ctx.get("col")
        if selected_col is None:
            return False

        if ctx.get("mode") == "cities":
            city_col = ctx.get("city_col")
            if not city_col:
                return False
            input_resp = self.security_utils.get_numbers_list(msg_text, prov_cities[city_col]["list"])
            if input_resp[0]:
                selected_value = self._normalized_selection_value(input_resp[1])
                resp = self.api.utils.insert_into_filters(self.api.sender, city_col, selected_value, True)
                if not resp.get("status"):
                    resp = self.api.utils.insert_into_filters(self.api.sender, city_col, selected_value, False)

                if resp.get("status"):
                    filters_resp = self.api.utils.get_filters(self.api.sender)
                    if filters_resp[0]:
                        filter_data = filters_resp[1]
                        name, col, _, _ = self.security_utils.cities_selection_logic(
                            filter_data,
                            self.lang.province,
                            self.filters_list[1:]
                        )
                        if name is not None and col is not None:
                            ctx["city_col"] = col[0]
                            self._send_settings_city_prompt(col[0], name[0])
                            return True

                    self.api.send_message(self.lang.province_success)
                    ctx["mode"] = None
                    ctx["col"] = "types"
                    self.api.send_btn_msg(self.lang.ask_types, ["All Types", "Contact Us", "Change Language!"], ["types", 0, 1])
                    return True

                self.api.send_message("Unable to update setting right now. Please try again.")
                return True

            if input_resp[1] is None:
                self.api.send_message(self.lang.keep_registering)
            else:
                self.api.send_message(self.lang.province_error + " " + str(input_resp[1]))
            self._send_settings_city_prompt(city_col, prov_cities[city_col]["name"])
            return True

        info = self._settings_target_info(selected_col)
        input_resp = self.security_utils.get_numbers_list(msg_text, info["items"])

        if input_resp[0]:
            selected_value = self._normalized_selection_value(input_resp[1])
            resp = self.api.utils.insert_into_filters(self.api.sender, selected_col, selected_value, True)
            if not resp.get("status"):
                resp = self.api.utils.insert_into_filters(self.api.sender, selected_col, selected_value, False)

            if resp.get("status"):
                if selected_col == "provinces":
                    self.api.send_message(self.lang.province_success)
                    if self._start_settings_city_flow():
                        return True
                    ctx["col"] = "types"
                    self.api.send_btn_msg(self.lang.ask_types, ["All Types", "Contact Us", "Change Language!"], ["types", 0, 1])
                    return True

                self.api.send_message(self.lang.province_success)
                self.api.send_message("Setting updated successfully.")
                self.settings_edit_context.pop(self.api.sender, None)
                return True

            self.api.send_message("Unable to update setting right now. Please try again.")
            return True

        if input_resp[1] is None:
            self.api.send_message(self.lang.keep_registering)
        else:
            self.api.send_message(self.lang.province_error + " " + str(input_resp[1]))

        if selected_col == "categories":
            self.api.send_document_msg_by_url("image", f"{self.img_url}categories.png", info["step_msg"])
        else:
            self.api.send_btn_msg(
                info["step_msg"],
                [info["all_btn_title"], "Contact Us", "Change Language!"],
                [info["all_btn_id"], 0, 1]
            )
        return True

    def process_settings_all_button(self, button_id):
        self._ensure_settings_context()
        ctx = self.settings_edit_context.get(self.api.sender)
        if not ctx:
            return False

        selected_col = ctx.get("col")
        if selected_col is None or str(button_id) != str(selected_col):
            return False

        resp = self.api.utils.insert_into_filters(self.api.sender, selected_col, "all", True)
        if not resp.get("status"):
            resp = self.api.utils.insert_into_filters(self.api.sender, selected_col, "all", False)

        if resp.get("status"):
            if selected_col == "provinces":
                self.api.send_message(self.lang.province_success)
                if self._start_settings_city_flow():
                    return True
                ctx["col"] = "types"
                self.api.send_btn_msg(self.lang.ask_types, ["All Types", "Contact Us", "Change Language!"], ["types", 0, 1])
                return True

            self.api.send_message(self.lang.province_success)
            self.api.send_message("Setting updated successfully.")
        else:
            self.api.send_message("Unable to update setting right now. Please try again.")

        self.settings_edit_context.pop(self.api.sender, None)
        return True

    def _parse_tender_datetime(self, value):
        if value is None:
            return None
        txt = str(value).strip()
        if txt == "":
            return None

        formats = [
            "%Y-%m-%d %H:%M:%S",
            "%b %d, %Y %I:%M %p",
            "%d %b %Y",
            "%d-%m-%Y",
            "%Y, %m, %d, %H:%M:%S"
        ]
        for fmt in formats:
            try:
                return datetime.datetime.strptime(txt, fmt)
            except Exception:
                continue

        try:
            return datetime.datetime.fromisoformat(txt.replace("T", " ").replace("Z", ""))
        except Exception:
            return None

    def _load_training_tenders(self):
        file_path = os.path.join("files", "training", "tenders_latest.pkl")
        if not os.path.exists(file_path):
            return [False, "Model file not found. Please run train_tenders.py first.", []]

        try:
            with open(file_path, "rb") as fp:
                payload = pickle.load(fp)
        except Exception as e:
            return [False, f"Unable to read model file: {str(e)}", []]

        table_map = payload.get("tables", {}) if isinstance(payload, dict) else {}
        merged = []
        for table_name, rows in table_map.items():
            if not isinstance(rows, list):
                continue
            for row in rows:
                if isinstance(row, dict):
                    item = dict(row)
                    item["table"] = table_name
                    merged.append(item)
        return [True, "", merged]

    def _openai_config(self):
        openai_key = str(HARDCODED_OPENAI_API_KEY).strip()
        if openai_key == "":
            openai_key = os.getenv("OPENAI_API_KEY", "").strip()

        model = str(HARDCODED_OPENAI_MODEL).strip()
        if model == "":
            model = os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip() or "gpt-4o-mini"

        return openai_key, model

    def _fallback_relevant_tenders(self, query, tenders):
        words = [w for w in re.findall(r"[a-zA-Z0-9]+", str(query).lower()) if len(w) > 2]
        ranked = []

        for tender in tenders:
            title = str(tender.get("title", "")).lower()
            dept = str(tender.get("department", "")).lower()
            cat = str(tender.get("category", "")).lower()
            city = str(tender.get("city", "")).lower()
            text = " ".join([title, dept, cat, city])

            score = 0
            for w in words:
                if w in title:
                    score += 4
                elif w in dept:
                    score += 3
                elif w in cat:
                    score += 2
                elif w in city:
                    score += 1
                elif w in text:
                    score += 1

            date_score = self._parse_tender_datetime(tender.get("date_published"))
            if date_score is None:
                date_score = self._parse_tender_datetime(tender.get("date_opening"))
            ranked.append((score, date_score, tender))

        ranked.sort(key=lambda x: (x[0], x[1] or datetime.datetime.min), reverse=True)
        top = [x[2] for x in ranked[:5] if x[0] > 0]

        if len(top) == 0:
            recents = sorted(
                tenders,
                key=lambda t: self._parse_tender_datetime(t.get("date_published"))
                or self._parse_tender_datetime(t.get("date_opening"))
                or datetime.datetime.min,
                reverse=True,
            )
            top = recents[:5]
        return top

    def _format_tender_summary_list(self, tenders):
        lines = ["Latest relevant tenders:"]
        idx = 1
        for tender in tenders:
            line = (
                f"{idx}. {str(tender.get('title', 'Untitled'))}"
                + f" | Dept: {str(tender.get('department', 'N/A'))}"
                + f" | City: {str(tender.get('city', 'N/A'))}"
                + f" | Open: {str(tender.get('date_opening', 'N/A'))}"
                + f" | Ref: {str(tender.get('id', 'N/A'))} ({str(tender.get('table', 'N/A'))})"
            )
            lines.append(line)
            idx += 1
        return "\n".join(lines)

    def direct_ask(self, query_text):
        query = str(query_text).strip()
        if query == "":
            self.api.send_message("Please send your query like: direct_ask construction tenders in lahore")
            return [False, "empty_query"]

        data_resp = self._load_training_tenders()
        if not data_resp[0]:
            self.api.send_message(data_resp[1])
            return [False, data_resp[1]]

        tenders = data_resp[2]
        if len(tenders) == 0:
            self.api.send_message("No tenders found in model file. Please refresh training data.")
            return [False, "no_tenders"]

        # Keep only latest chunk so prompt remains small and relevant.
        tenders = sorted(
            tenders,
            key=lambda t: self._parse_tender_datetime(t.get("date_published"))
            or self._parse_tender_datetime(t.get("date_opening"))
            or datetime.datetime.min,
            reverse=True,
        )[:150]

        openai_key, model = self._openai_config()
        if openai_key != "":
            payload = {
                "model": model,
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "You are a tender assistant. Return max 5 latest relevant tenders in concise WhatsApp style. "
                            "Include title, department, city, opening date, and tender reference (id/table)."
                        )
                    },
                    {
                        "role": "user",
                        "content": (
                            f"User query: {query}\n"
                            + "Tenders JSON: "
                            + json.dumps(tenders, ensure_ascii=False)[:18000]
                        )
                    }
                ],
                "temperature": 0.2
            }
            headers = {
                "Authorization": f"Bearer {openai_key}",
                "Content-Type": "application/json"
            }
            try:
                resp = requests.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=60
                )
                if resp.status_code == 200:
                    answer = resp.json().get("choices", [{}])[0].get("message", {}).get("content", "").strip()
                    if answer != "":
                        self.api.send_message(answer[:3200])
                        return [True]
            except Exception:
                pass

        # Fallback ranking if OpenAI key is missing or request fails.
        selected = self._fallback_relevant_tenders(query, tenders)
        if len(selected) == 0:
            self.api.send_message("I could not find relevant tenders for your query right now.")
            return [False, "no_match"]

        self.api.send_message(self._format_tender_summary_list(selected)[:3200])
        return [True]

    def register_step_btn_resp(self,button_id):
        col = button_id
        
        if col == "provinces":
            resp = self.api.utils.insert_into_filters(self.api.sender, col, "all", False)
            if resp.get("status"):
                self.api.send_message(self.lang.province_success)
                self._send_registration_next_step()
            else:
                self.api.send_message("Unable to save your region right now. Please try again.")
            return

        if col == "types":
            resp = self.api.utils.insert_into_filters(self.api.sender, col, "all", True)
            if not resp.get("status"):
                resp = self.api.utils.insert_into_filters(self.api.sender, col, "all", False)

            if resp.get("status"):
                self.api.send_message(self.lang.province_success)
                self.api.send_btn_msg(self.lang.register_success, ["Send Tenders", "Contact Us", "Change Language!"])
                self.api.utils.update_user_status(self.api.sender, "TRIAL")
            else:
                self.api.send_message("Unable to save contract type right now. Please try again.")
            return

        resp = self.api.utils.insert_into_filters(self.api.sender, col, "all", True)
        if not resp.get("status"):
            resp = self.api.utils.insert_into_filters(self.api.sender, col, "all", False)

        if resp.get("status"):
            self.api.send_message(self.lang.province_success)
            self._send_registration_next_step()
        else:
            self.api.send_message("Unable to save your selection right now. Please try again.")
    def send_tenders(self,cron=False,old=False,old_table = []):
        
        if not cron:
            filters = self.api.utils.get_filters(self.api.sender)
        else:
            filters = self.api.utils.get_filters()
        if not filters[0]:
            if cron:
                return [False,str(filters)]
            return [False,"Your settings are incomplete. Please use Change Settings to select your preferences first."]
        filters = filters[1]
        
        def inner(cron,old,old_table,filters,security_utils,api,lang):
            already_sent_list = []
            not_available_list = []
            count = 0
            if not cron:
                categories = security_utils.map_list(str(filters[-1]),prov_cities["categories"]["list"])
                for prov_i in str(filters[1]).replace(" ","").split(","):
                    never_sent = True
                    for prov in prov_indexes[prov_i]:
                        t = prov.split("_")[0]
                        col = t+"_cities"
                        if old and t not in old_table:
                            continue
                        else:
                            count = 0
                        if col != "federal_cities":
                            prov_name = prov_cities[col]["name"]
                            cities_of_prov = prov_cities[col]["list"]
                            cities_of_prov = security_utils.map_list(filters[prov_cities[col]["col_index"]],cities_of_prov)
                        else:
                            prov_name = "Federal"
                        tenders = api.utils.get_tenders(prov,None)
                        if tenders[0]:
                            for tender in tenders[1]:
                                send = False
                                if col != "federal_cities" and any(str(tender[6]).lower().split(" ")[0] in city for city in cities_of_prov) and (any(str(tender[7]).lower().split(" ")[0] in cat for cat in categories) or str(tender[7]).lower() == "none" ):
                                    send = True
                                    
                                elif col == "federal_cities" and (any(str(tender[7]).lower() in cat for cat in categories) or str(tender[7]).lower() == "none" ):
                                    send = True
                                
                                sent_list = str(tender[-1]).split(",")
                                if send and (old or api.sender not in sent_list):
                                        
                                        never_sent = False
                                        if col == "sindh_cities":
                                            note = f"Estimate Amount of Tender is {tender[-2]}\nOnly *{str(security_utils.days_to_open(col,tender[5]))} day(s) in opening"
                                        else:
                                            note = f"Only *{str(security_utils.days_to_open(col,tender[5]))} day(s) in opening"
                                        data = [tender[1],tender[4],tender[5],tender[2],tender[6],note]
                                        msg = lang.tender_msg(prov_name,data)
                                        api.send_btn_msg(msg,["Bid Documents","Tender Summary (AI)","Remind Me!"],[f"{tender[0]}&&{prov}&&0",f"{tender[0]}&&{prov}&&1",f"{tender[0]}&&{prov}&&2"])

                                        if not old:
                                            if str(tender[-1]).lower() == "none":
                                                sent_to = api.sender
                                            else:
                                                sent_to = str(tender[-1])+f",{api.sender}"
                                            api.utils.update_tenders_sent_to(prov,sent_to,tender[0])
                                        else:
                                            if count == 5:
                                                break
                                            else:
                                                count += 1
                            
                            if never_sent:
                                    already_sent_list.append(prov_name)     
                        else:
                             not_available_list.append(prov_name)
                if not old and len(already_sent_list) > 0:
                    txt = "✅"
                    txt += "\n✅".join(already_sent_list)
                    api.send_btn_msg(lang.all_tenders_already_sent(txt),["Get Old Tenders","Change Settings","Change Language!"],[",".join(already_sent_list),"0","1"]) 
                if len(not_available_list) > 0:
                    txt = "⚠️"
                    txt += "\n⚠️".join(not_available_list)
                    api.send_btn_msg(lang.no_tender_available_msg(txt),["Change Settings","Change Language!"]) 
        thread = threading.Thread(target=inner,args=(cron,old,old_table,filters,self.security_utils,self.api,self.lang,))
        thread.start()
        # inner(cron,filters,self.security_utils,self.api,self.lang)
        return [True]
    def send_demo_tenders(self,limit=10):
        table_map = {
            "federal_table": ("Federal", "federal_cities"),
            "punjab_table": ("Punjab", "punjab_cities"),
            "sindh_table": ("Sindh", "sindh_cities"),
            "kpk_table": ("KPK", "kpk_cities"),
            "ajk_table": ("AJK", "ajk_cities"),
            "gilgit_table": ("Gilgit", "gilgit_cities"),
            "balochistan_table": ("Balochistan", "balochistan_cities")
        }
        sent_count = 0
        for table, table_meta in table_map.items():
            tenders = self.api.utils.get_tenders(table,None)
            if not tenders[0]:
                continue
            prov_name, days_key = table_meta
            for tender in tenders[1]:
                if sent_count >= limit:
                    return sent_count
                try:
                    if self.security_utils.check_expiry(str(tender[5]),table=table):
                        continue
                    if table == "sindh_table":
                        note = f"Estimate Amount of Tender is {tender[-2]}\nOnly *{str(self.security_utils.days_to_open(days_key,tender[5]))} day(s) in opening"
                    else:
                        note = f"Only *{str(self.security_utils.days_to_open(days_key,tender[5]))} day(s) in opening"
                    data = [tender[1],tender[4],tender[5],tender[2],tender[6],note]
                    msg = self.lang.tender_msg(prov_name,data)
                    self.api.send_btn_msg(msg,["Bid Documents","Tender Summary (AI)","Remind Me!"],[f"{tender[0]}&&{table}&&0",f"{tender[0]}&&{table}&&1",f"{tender[0]}&&{table}&&2"])
                    sent_count += 1
                except Exception:
                    continue
        return sent_count
    def download_bid_docs(self,tender_id,table):
        resp = self.api.utils.get_tenders(table,["document"],["id"],[tender_id])
        if resp[0]:
            doc_link = resp[1][0][0]
            if table == "sindh_table":
                sindh_scrap = Sindh_Scrapper(self.security_utils)
                resp = sindh_scrap.get_doc(doc_link)
                if resp[0]:
                    self.api.send_document_msg_by_url(type_="document",url=f"https://tenderwala.thedataminds.us/tenderdocs/{resp[1]}",filename=f"Tenderwala-{str(resp[1])}")
                else:
                    self.api.send_message(f"Download link for this Sindh tender is not available right now. Info: {str(resp[1])}")
            else:
                try:
                    self.api.send_document_msg_by_url(type_="document",url=doc_link,filename=f"Tenderwala-{str(doc_link).split('/')[-1]}")
                except Exception as e:
                    self.api.send_message(f"Doc link: {str(doc_link)}\n{e}")
        else:
            self.api.send_message(f"Download link for this tender is not available. Table: {table} Info: {str(resp[1])}")
    def _summary_month_key(self):
        return datetime.datetime.now().strftime("%Y-%m")

    def _get_ai_summary_usage(self, phone):
        month_key = self._summary_month_key()

        monthly_payload = {
            "db": "tenderwala",
            "table": "ai_summary_usage_table",
            "cols": ["id", "used_count"],
            "ops": "SELECT",
            "where": ["phone", "month_key"],
            "value": [phone, month_key]
        }
        monthly_resp = db_execute(monthly_payload)
        if monthly_resp.get("status"):
            monthly_rows = monthly_resp.get("data", [])
            if len(monthly_rows) > 0:
                best_row = monthly_rows[0]
                best_count = 0
                for row in monthly_rows:
                    try:
                        count = int(row[1])
                    except Exception:
                        count = 0
                    if count >= best_count:
                        best_count = count
                        best_row = row
                return [True, best_count, best_row[0] if len(best_row) > 0 else None]
        else:
            # Fallback to avoid failing on schema mismatch for monthly query.
            monthly_resp = {"status": False, "message": str(monthly_resp)}

        # Fallback: query without id column for monthly tracking.
        monthly_no_id_payload = {
            "db": "tenderwala",
            "table": "ai_summary_usage_table",
            "cols": ["used_count"],
            "ops": "SELECT",
            "where": ["phone", "month_key"],
            "value": [phone, month_key]
        }
        monthly_no_id_resp = db_execute(monthly_no_id_payload)
        if monthly_no_id_resp.get("status"):
            monthly_rows = monthly_no_id_resp.get("data", [])
            if len(monthly_rows) > 0:
                best_count = 0
                for row in monthly_rows:
                    try:
                        count = int(row[0])
                    except Exception:
                        count = 0
                    if count >= best_count:
                        best_count = count
                return [True, best_count, None]

        # Legacy fallback: some deployments track a single counter per phone.
        legacy_with_id_payload = {
            "db": "tenderwala",
            "table": "ai_summary_usage_table",
            "cols": ["id", "used_count"],
            "ops": "SELECT",
            "where": ["phone"],
            "value": [phone]
        }
        legacy_with_id_resp = db_execute(legacy_with_id_payload)
        if legacy_with_id_resp.get("status"):
            rows = legacy_with_id_resp.get("data", [])
            if len(rows) > 0:
                best_row = rows[0]
                best_count = 0
                for row in rows:
                    try:
                        count = int(row[1])
                    except Exception:
                        count = 0
                    if count >= best_count:
                        best_count = count
                        best_row = row
                return [True, best_count, best_row[0] if len(best_row) > 0 else None]

        legacy_no_id_payload = {
            "db": "tenderwala",
            "table": "ai_summary_usage_table",
            "cols": ["used_count"],
            "ops": "SELECT",
            "where": ["phone"],
            "value": [phone]
        }
        legacy_no_id_resp = db_execute(legacy_no_id_payload)
        if legacy_no_id_resp.get("status"):
            rows = legacy_no_id_resp.get("data", [])
            if len(rows) > 0:
                best_count = 0
                for row in rows:
                    try:
                        count = int(row[0])
                    except Exception:
                        count = 0
                    if count >= best_count:
                        best_count = count
                return [True, best_count, None]

        # Broad fallback when where-clause columns differ across deployments.
        phone_scan_payload = {
            "db": "tenderwala",
            "table": "ai_summary_usage_table",
            "cols": ["phone", "used_count"],
            "ops": "SELECT",
            "where": None,
            "value": None
        }
        phone_scan_resp = db_execute(phone_scan_payload)
        if phone_scan_resp.get("status"):
            best_count = None
            for row in phone_scan_resp.get("data", []):
                if len(row) < 2:
                    continue
                if str(row[0]).strip() != str(phone).strip():
                    continue
                try:
                    count = int(row[1])
                except Exception:
                    count = 0
                if best_count is None or count > best_count:
                    best_count = count
            if best_count is not None:
                return [True, best_count, None]

        # If table is missing, allow feature and start from zero.
        message = str(monthly_resp.get("message", ""))
        if "Table Not found" in message and "ai_summary_usage_table" in message:
            return [True, 0, None]

        # If monthly query failed due schema mismatch, try to continue with zero instead of hard-failing.
        message_2 = str(monthly_resp.get("message", ""))
        if "does not exist" in message_2 or "Unknown column" in message_2:
            return [True, 0, None]

        return [False, str(monthly_resp)]

    def _try_usage_write(self, cols, where, values):
        payload = {
            "db": "tenderwala",
            "table": "ai_summary_usage_table",
            "cols": cols,
            "ops": "UPDATE" if where is not None else "INSERT",
            "where": where,
            "value": values
        }
        resp = db_execute(payload)
        return bool(resp.get("status"))

    def _set_ai_summary_usage(self, phone, next_count, row_id=None):
        now_text = str(self.security_utils.get_datetime())
        month_key = self._summary_month_key()
        next_count_text = str(next_count)
        generated_id = f"{month_key}:{str(phone).strip()}:{uuid4().hex}"

        # Insert first when there is no known row id.
        # UPDATE in current DB helper can return success even when 0 rows are affected.
        if row_id is None:
            # Explicit schema insert for the known table definition.
            if self._try_usage_write(
                ["id", "phone", "month_key", "used_count", "updated_on"],
                None,
                [generated_id, phone, month_key, next_count_text, now_text]
            ):
                return True
            insert_attempts = [
                (["id", "phone", "month_key", "used_count", "updated_on"], [generated_id, phone, month_key, next_count_text, now_text]),
                (["id", "phone", "month_key", "used_count"], [generated_id, phone, month_key, next_count_text]),
                (["id", "phone", "used_count", "updated_on"], [generated_id, phone, next_count_text, now_text]),
                (["id", "phone", "used_count"], [generated_id, phone, next_count_text]),
            ]
            for cols, values in insert_attempts:
                if self._try_usage_write(cols, None, values):
                    return True

        # 1) Try updates first (monthly + legacy variants).
        update_attempts = []
        if row_id is not None:
            update_attempts.extend([
                (["used_count", "updated_on"], ["id"], [next_count_text, now_text, row_id]),
                (["used_count"], ["id"], [next_count_text, row_id]),
            ])

        update_attempts.extend([
            (["used_count", "updated_on"], ["phone", "month_key"], [next_count_text, now_text, phone, month_key]),
            (["used_count"], ["phone", "month_key"], [next_count_text, phone, month_key]),
            (["used_count", "updated_on"], ["phone"], [next_count_text, now_text, phone]),
            (["used_count"], ["phone"], [next_count_text, phone]),
        ])

        for cols, where, values in update_attempts:
            if self._try_usage_write(cols, where, values):
                return True

        # 2) Retry inserts for monthly/legacy schemas.
        fallback_inserts = [
            (["id", "phone", "month_key", "used_count", "updated_on"], [generated_id, phone, month_key, next_count_text, now_text]),
            (["id", "phone", "month_key", "used_count"], [generated_id, phone, month_key, next_count_text]),
            (["id", "phone", "used_count", "updated_on"], [generated_id, phone, next_count_text, now_text]),
            (["id", "phone", "used_count"], [generated_id, phone, next_count_text]),
        ]
        for cols, values in fallback_inserts:
            if self._try_usage_write(cols, None, values):
                return True

        # 3) Final retry update by phone in case insert failed due duplicate/constraint race.
        if self._try_usage_write(["used_count"], ["phone"], [next_count_text, phone]):
            return True
        if self._try_usage_write(["used_count", "updated_on"], ["phone"], [next_count_text, now_text, phone]):
            return True

        return False

    def _is_blankish(self, value):
        if value is None:
            return True
        text = str(value).strip().lower()
        return text in ["", "none", "null", "nan", "n/a"]

    def _extract_download_link_from_html(self, base_url, html_text):
        raw = str(html_text or "")
        if raw.strip() == "":
            return None

        try:
            from bs4 import BeautifulSoup

            soup = BeautifulSoup(raw, "html.parser")
            best = None
            for anchor in soup.find_all("a"):
                href = str(anchor.get("href") or "").strip()
                if href == "":
                    continue
                full = urljoin(base_url, href)
                label = anchor.get_text(" ", strip=True).lower()
                href_low = full.lower()

                if any(x in label for x in ["download tender document", "download bidding document", "download document"]):
                    return full

                if best is None and (
                    href_low.endswith(".pdf")
                    or href_low.endswith(".doc")
                    or href_low.endswith(".docx")
                    or "download" in label
                    or "download" in href_low
                ):
                    best = full

            if best is None:
                for node in soup.find_all(attrs={"onclick": True}):
                    onclick = str(node.get("onclick") or "")
                    m = re.search(r"(?:window\.open|location\.href)\(['\"]([^'\"]+)['\"]\)", onclick, flags=re.IGNORECASE)
                    if m:
                        candidate = urljoin(base_url, m.group(1))
                        cand_low = candidate.lower()
                        if any(x in cand_low for x in [".pdf", ".doc", ".docx", "download", "tenderdoc", "bidding"]):
                            return candidate

            if best is None:
                for attr_name in ["data-url", "data-href", "data-download"]:
                    for node in soup.find_all(attrs={attr_name: True}):
                        candidate = urljoin(base_url, str(node.get(attr_name) or "").strip())
                        if candidate.strip() != "":
                            cand_low = candidate.lower()
                            if any(x in cand_low for x in [".pdf", ".doc", ".docx", "download", "tenderdoc", "bidding"]):
                                return candidate
            return best
        except Exception:
            m2 = re.search(r"(?:window\.open|location\.href)\(['\"]([^'\"]+)['\"]\)", raw, flags=re.IGNORECASE)
            if m2:
                return urljoin(base_url, m2.group(1))

            m3 = re.search(r"https?://[^\s\"']+\.(?:pdf|docx?|rtf)(?:\?[^\s\"']*)?", raw, flags=re.IGNORECASE)
            if m3:
                return m3.group(0)

            m = re.search(r"href\s*=\s*[\"']([^\"']+)[\"']", raw, flags=re.IGNORECASE)
            if m:
                return urljoin(base_url, m.group(1))
            return None

    def _http_get_for_docs(self, url, timeout=60):
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/pdf,application/msword,application/vnd.openxmlformats-officedocument.wordprocessingml.document,*/*",
            "Accept-Language": "en-US,en;q=0.9",
        }
        return requests.get(url, timeout=timeout, headers=headers)

    def _is_noise_sentence(self, sentence):
        txt = str(sentence).strip()
        if txt == "":
            return True

        low = txt.lower()
        if "<" in txt or "{" in txt or "}" in txt:
            return True

        noise_markers = [
            "home tenders",
            "active tenders",
            "tenders history",
            "evaluation results",
            "contracts grievances",
            "blacklisted firms",
            "copyright",
            "no-js",
            "navbar",
            "position-sticky",
            "viewport",
            "public procurement regulatory authority",
        ]
        procurement_markers = [
            "tender",
            "bid",
            "security",
            "estimate",
            "submission",
            "technical",
            "financial",
            "qualification",
            "document",
            "emd",
            "cdr",
        ]

        if any(marker in low for marker in noise_markers) and (not any(marker in low for marker in procurement_markers)):
            return True

        if len(re.findall(r"[a-zA-Z]", txt)) < 8:
            return True
        return False

    def _response_suffix_hint(self, url, resp):
        known_exts = [".pdf", ".doc", ".docx", ".docm", ".rtf", ".txt", ".html", ".htm", ".xml"]

        url_ext = os.path.splitext(str(url).split("?")[0])[1].lower()
        if url_ext in known_exts:
            return url_ext

        disp = str(resp.headers.get("Content-Disposition", ""))
        if disp.strip() != "":
            filename_match = re.search(r"filename\*?=(?:UTF-8''|\")?([^\";]+)", disp, flags=re.IGNORECASE)
            if filename_match:
                file_name = unquote(filename_match.group(1)).strip().strip('"')
                file_ext = os.path.splitext(file_name)[1].lower()
                if file_ext in known_exts:
                    return file_ext

        content_type = str(resp.headers.get("Content-Type", "")).lower()
        if "application/pdf" in content_type:
            return ".pdf"
        if "officedocument.wordprocessingml.document" in content_type:
            return ".docx"
        if "msword" in content_type:
            return ".doc"
        if "text/html" in content_type:
            return ".html"
        if "application/rtf" in content_type or "text/rtf" in content_type:
            return ".rtf"
        if "text/plain" in content_type:
            return ".txt"

        magic = resp.content[:32]
        lower_magic = magic.lower()
        if magic.startswith(b"%PDF"):
            return ".pdf"
        if magic.startswith(b"PK\x03\x04"):
            return ".docx"
        if lower_magic.startswith(b"<!doctype html") or lower_magic.startswith(b"<html"):
            return ".html"
        return ".bin"

    def _extract_docx_text(self, file_path):
        chunks = []
        try:
            with zipfile.ZipFile(file_path, "r") as zf:
                xml_parts = [
                    name
                    for name in zf.namelist()
                    if name.startswith("word/") and name.endswith(".xml")
                ]

                preferred = [
                    "word/document.xml",
                    "word/header1.xml",
                    "word/header2.xml",
                    "word/header3.xml",
                    "word/footer1.xml",
                ]

                ordered = []
                for name in preferred:
                    if name in xml_parts:
                        ordered.append(name)
                for name in xml_parts:
                    if name not in ordered:
                        ordered.append(name)

                for name in ordered[:8]:
                    try:
                        xml_text = zf.read(name).decode("utf-8", errors="ignore")
                    except Exception:
                        continue
                    xml_text = xml_text.replace("</w:p>", "\n")
                    plain = re.sub(r"<[^>]+>", " ", xml_text)
                    plain = re.sub(r"\s+", " ", plain).strip()
                    if plain != "":
                        chunks.append(plain)
        except Exception:
            return ""

        return "\n".join(chunks)

    def _extract_html_text(self, file_path):
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                html_text = f.read(800000)
        except Exception:
            return ""

        try:
            from bs4 import BeautifulSoup

            soup = BeautifulSoup(html_text, "html.parser")
            for tag in soup(["script", "style", "noscript"]):
                tag.decompose()
            for tag_name in ["nav", "header", "footer", "aside"]:
                for node in soup.find_all(tag_name):
                    node.decompose()

            text = soup.get_text(separator=" ", strip=True)
            text = re.sub(r"\s+", " ", text).strip()
            return text
        except Exception:
            html_text = re.sub(r"<script[\s\S]*?</script>", " ", html_text, flags=re.IGNORECASE)
            html_text = re.sub(r"<style[\s\S]*?</style>", " ", html_text, flags=re.IGNORECASE)
            html_text = re.sub(r"<[^>]+>", " ", html_text)
            html_text = re.sub(r"\s+", " ", html_text).strip()
            return html_text

    def _sanitize_doc_text_for_summary(self, doc_text):
        text = re.sub(r"\s+", " ", str(doc_text)).strip()
        if text == "":
            return ""

        junk_phrases = [
            "home tenders active tenders",
            "tenders history",
            "evaluation results",
            "contracts grievances",
            "job advertisements",
            "blacklisted firms",
            "public procurement regulatory authority",
        ]
        for phrase in junk_phrases:
            text = re.sub(re.escape(phrase), " ", text, flags=re.IGNORECASE)

        sentences = [s.strip() for s in re.split(r"(?<=[.!?;])\s+", text) if s.strip() != ""]
        kept = []
        for sentence in sentences:
            if len(sentence) < 20:
                continue
            if self._is_noise_sentence(sentence):
                continue
            kept.append(sentence)

        if len(kept) == 0:
            return text[:7000]
        return " ".join(kept[:90])[:12000]

    def _enrich_insights_with_tender_meta(self, insights, tender_meta):
        merged = {
            "cdr_amount": insights.get("cdr_amount", "N/A"),
            "estimate_amount": insights.get("estimate_amount", "N/A"),
            "documents_required": list(insights.get("documents_required", [])),
            "evaluation_criteria": list(insights.get("evaluation_criteria", [])),
            "overall_points": list(insights.get("overall_points", [])),
            "text_length": insights.get("text_length", 0),
        }

        est_cost = tender_meta.get("estimated_cost")
        if str(merged.get("estimate_amount", "N/A")).strip().lower() == "n/a" and (not self._is_blankish(est_cost)):
            merged["estimate_amount"] = str(est_cost).strip()

        meta_points = []
        if not self._is_blankish(tender_meta.get("title")):
            meta_points.append(f"Tender: {str(tender_meta.get('title')).strip()}")
        if not self._is_blankish(tender_meta.get("department")):
            meta_points.append(f"Department: {str(tender_meta.get('department')).strip()}")
        if not self._is_blankish(tender_meta.get("city")):
            meta_points.append(f"Location: {str(tender_meta.get('city')).strip()}")
        if not self._is_blankish(tender_meta.get("category")) and str(tender_meta.get("category")).strip().lower() != "none":
            meta_points.append(f"Category: {str(tender_meta.get('category')).strip()}")
        if not self._is_blankish(tender_meta.get("date_opening")):
            meta_points.append(f"Bid Opening: {str(tender_meta.get('date_opening')).strip()}")
        if not self._is_blankish(tender_meta.get("date_published")):
            meta_points.append(f"Published: {str(tender_meta.get('date_published')).strip()}")

        seen = set([str(item).strip().lower() for item in merged["overall_points"]])
        for point in meta_points:
            key = point.lower()
            if key not in seen:
                merged["overall_points"].append(point)
                seen.add(key)

        merged["overall_points"] = merged["overall_points"][:6]
        return merged

    def _download_doc_for_summary(self, doc_ref, table):
        if table == "sindh_table":
            sindh_scrap = Sindh_Scrapper(self.security_utils)
            doc_resp = sindh_scrap.get_doc(doc_ref)
            if not doc_resp[0]:
                return [False, f"Sindh document fetch failed: {str(doc_resp[1])}", None, False]
            file_name = doc_resp[1]
            local_path = os.path.join("static", "documents", str(file_name))
            if not os.path.exists(local_path):
                return [False, "Sindh document downloaded but file not found locally", None, False]
            return [True, "", local_path, True]

        url = str(doc_ref).strip()
        if url == "" or (not url.lower().startswith("http")):
            return [False, "Invalid document URL", None, False]

        try:
            resp = self._http_get_for_docs(url, timeout=60)
        except Exception as e:
            return [False, f"Document download failed: {str(e)}", None, False]

        if resp.status_code != 200:
            return [False, f"Document URL returned status {resp.status_code}", None, False]

        final_url = url
        final_resp = resp
        for _ in range(2):
            suffix_guess = self._response_suffix_hint(final_url, final_resp)
            content_type = str(final_resp.headers.get("Content-Type", "")).lower()
            is_html = (suffix_guess in [".html", ".htm", ".xml"]) or ("text/html" in content_type)
            if not is_html:
                break

            try:
                html_text = final_resp.content.decode("utf-8", errors="ignore")
            except Exception:
                html_text = ""

            next_url = self._extract_download_link_from_html(final_url, html_text)
            if next_url is None or str(next_url).strip() == "" or str(next_url).strip() == str(final_url).strip():
                break

            try:
                next_resp = self._http_get_for_docs(next_url, timeout=60)
            except Exception:
                break

            if next_resp.status_code != 200:
                break

            final_url = next_url
            final_resp = next_resp

        suffix = self._response_suffix_hint(final_url, final_resp)
        tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
        tmp_file.write(final_resp.content)
        tmp_file.close()
        return [True, "", tmp_file.name, True]

    def _extract_doc_text(self, file_path):
        if not file_path or (not os.path.exists(file_path)):
            return ""

        ext = os.path.splitext(str(file_path))[1].lower()
        magic = b""
        try:
            with open(file_path, "rb") as sig_fp:
                magic = sig_fp.read(64)
        except Exception:
            magic = b""

        if ext in ["", ".bin", ".tmp"]:
            if magic.startswith(b"%PDF"):
                ext = ".pdf"
            elif magic.startswith(b"PK\x03\x04"):
                ext = ".docx"
            else:
                low = magic.lower()
                if low.startswith(b"<!doctype html") or low.startswith(b"<html"):
                    ext = ".html"

        text = ""
        if ext == ".pdf":
            reader_cls = None
            try:
                from pypdf import PdfReader as _PdfReader
                reader_cls = _PdfReader
            except Exception:
                try:
                    from PyPDF2 import PdfReader as _PdfReader
                    reader_cls = _PdfReader
                except Exception:
                    reader_cls = None

            if reader_cls is not None:
                try:
                    reader = reader_cls(file_path)
                    chunks = []
                    page_count = len(reader.pages)
                    max_pages = page_count
                    for i in range(max_pages):
                        page_text = reader.pages[i].extract_text() or ""
                        if page_text.strip() != "":
                            chunks.append(page_text.strip())
                    text = "\n".join(chunks)
                except Exception:
                    text = ""
        elif ext in [".docx", ".docm"]:
            text = self._extract_docx_text(file_path)
        elif ext in [".html", ".htm", ".xml"]:
            text = self._extract_html_text(file_path)
        else:
            try:
                with open(file_path, "rb") as f:
                    raw = f.read(450000)
                text = raw.decode("utf-8", errors="ignore")
            except Exception:
                text = ""

        clean = re.sub(r"\s+", " ", str(text)).strip()
        return clean[:120000]

    def _split_doc_sentences(self, doc_text):
        compact = re.sub(r"\s+", " ", str(doc_text)).strip()
        if compact == "":
            return []
        return [s.strip() for s in re.split(r"(?<=[.!?;])\s+", compact) if s.strip() != ""]

    def _pick_keyword_sentences(self, sentences, keywords, limit=4, min_len=25, max_len=220):
        results = []
        seen = set()
        for sentence in sentences:
            if self._is_noise_sentence(sentence):
                continue
            if len(sentence) < min_len:
                continue
            low = sentence.lower()
            if any(k in low for k in keywords):
                item = sentence[:max_len].strip()
                key = item.lower()
                if key not in seen:
                    seen.add(key)
                    results.append(item)
            if len(results) >= limit:
                break
        return results

    def _extract_amount_by_keywords(self, doc_text, keywords, fallback_label):
        text = re.sub(r"\s+", " ", str(doc_text)).strip()
        if text == "":
            return "N/A"

        amount_pattern = (
            r"(?:"
            r"(?:rs\.?|pkr|pak\s*rupees?)\s*[:\-]?\s*[0-9][0-9,]*(?:\.[0-9]{1,2})?(?:\s*(?:million|billion|crore|lakh|thousand|k))?"
            r"|"
            r"[0-9]{1,2}(?:\.[0-9]{1,2})?\s*%"
            r"|"
            r"[0-9]{1,3}(?:,[0-9]{3})+(?:\.[0-9]{1,2})?(?:\s*(?:million|billion|crore|lakh|thousand|k))?"
            r")"
        )
        joined_kw = "|".join([re.escape(k) for k in keywords])
        if joined_kw == "":
            return "N/A"

        near_pattern = rf"(?:{joined_kw}).{{0,130}}?({amount_pattern})"
        m = re.search(near_pattern, text, flags=re.IGNORECASE)
        if m:
            return m.group(1).strip()

        reverse_pattern = rf"({amount_pattern}).{{0,80}}?(?:{joined_kw})"
        m2 = re.search(reverse_pattern, text, flags=re.IGNORECASE)
        if m2:
            return m2.group(1).strip()

        # Sentence-level fallback for cases like "Bid Security shall be 2%".
        sentences = self._split_doc_sentences(text)
        for sentence in sentences[:120]:
            if self._is_noise_sentence(sentence):
                continue
            low = sentence.lower()
            if not any(k in low for k in keywords):
                continue
            m3 = re.search(amount_pattern, sentence, flags=re.IGNORECASE)
            if m3:
                return m3.group(1).strip() if m3.lastindex else m3.group(0).strip()
        return "N/A"

    def _extract_rule_based_doc_insights(self, doc_text):
        sentences = self._split_doc_sentences(doc_text)

        cdr_amount = self._extract_amount_by_keywords(
            doc_text,
            ["cdr", "call deposit", "bid security", "earnest money", "emd", "security deposit"],
            "Mentioned"
        )
        estimate_amount = self._extract_amount_by_keywords(
            doc_text,
            ["estimate", "estimated amount", "estimated cost", "engineer estimate", "estimated value"],
            "Mentioned"
        )

        docs_required = self._pick_keyword_sentences(
            sentences,
            [
                "documents required", "mandatory documents", "required documents",
                "submit", "submission", "attached", "annex", "certificate",
                "ntn", "strn", "pec", "registration", "affidavit", "bank statement",
                "experience", "undertaking", "bid form"
            ],
            limit=5,
            min_len=20,
            max_len=200
        )

        eval_criteria = self._pick_keyword_sentences(
            sentences,
            [
                "evaluation criteria", "technical evaluation", "financial evaluation", "evaluation",
                "responsive", "qualification criteria", "marks", "scoring", "weightage",
                "lowest evaluated", "most advantageous"
            ],
            limit=5,
            min_len=20,
            max_len=200
        )

        overall_points = self._pick_keyword_sentences(
            sentences,
            [
                "scope", "work", "service", "supply", "project", "contract",
                "timeline", "delivery", "completion", "objective", "procurement"
            ],
            limit=6,
            min_len=30,
            max_len=210
        )

        if len(overall_points) == 0 and len(sentences) > 0:
            overall_points = [
                s[:210]
                for s in sentences[:25]
                if len(s.strip()) > 20 and (not self._is_noise_sentence(s))
            ][:4]

        return {
            "cdr_amount": cdr_amount,
            "estimate_amount": estimate_amount,
            "documents_required": docs_required,
            "evaluation_criteria": eval_criteria,
            "overall_points": overall_points,
            "text_length": len(str(doc_text)),
        }

    def _extract_regex_doc_insights(self, doc_text):
        text = re.sub(r"\s+", " ", str(doc_text)).strip()
        if text == "":
            return {
                "cdr_amount": "N/A",
                "estimate_amount": "N/A",
                "documents_required": [],
                "evaluation_criteria": [],
            }

        amount_pat = r"(?:rs\.?|pkr)?\s*[0-9][0-9,]*(?:\.[0-9]{1,2})?(?:\s*(?:million|billion|crore|lakh|thousand|k))?|[0-9]{1,2}(?:\.[0-9]{1,2})?\s*%"

        def _find_near_amount(keywords, window=140):
            keys = "|".join([re.escape(k) for k in keywords])
            if keys == "":
                return "N/A"
            m = re.search(rf"(?:{keys}).{{0,{window}}}?({amount_pat})", text, flags=re.IGNORECASE)
            if m:
                return m.group(1).strip()
            m = re.search(rf"({amount_pat}).{{0,90}}?(?:{keys})", text, flags=re.IGNORECASE)
            if m:
                return m.group(1).strip()
            return "N/A"

        cdr_amount = _find_near_amount([
            "cdr", "call deposit", "bid security", "earnest money", "emd", "security deposit"
        ])
        estimate_amount = _find_near_amount([
            "estimate", "estimated amount", "estimated cost", "engineer estimate", "estimated value"
        ])

        doc_patterns = [
            r"documents? required[:\-]?\s*([^\.\n]{20,260})",
            r"mandatory documents?[:\-]?\s*([^\.\n]{20,260})",
            r"submit(?:ted|ting)?[:\-]?\s*([^\.\n]{20,260})",
        ]
        eval_patterns = [
            r"evaluation criteria[:\-]?\s*([^\.\n]{20,260})",
            r"technical evaluation[:\-]?\s*([^\.\n]{20,260})",
            r"financial evaluation[:\-]?\s*([^\.\n]{20,260})",
            r"qualification criteria[:\-]?\s*([^\.\n]{20,260})",
        ]

        def _collect(patterns, limit=4):
            out = []
            seen = set()
            for pat in patterns:
                for m in re.finditer(pat, text, flags=re.IGNORECASE):
                    val = re.sub(r"\s+", " ", str(m.group(1))).strip(" -:;,.\t")
                    if len(val) < 12:
                        continue
                    key = val.lower()
                    if key in seen:
                        continue
                    seen.add(key)
                    out.append(val)
                    if len(out) >= limit:
                        return out
            return out

        return {
            "cdr_amount": cdr_amount,
            "estimate_amount": estimate_amount,
            "documents_required": _collect(doc_patterns, 4),
            "evaluation_criteria": _collect(eval_patterns, 4),
        }

    def _merge_missing_with_regex(self, insights, doc_text):
        regex_insights = self._extract_regex_doc_insights(doc_text)
        merged = dict(insights)

        if self._na_or_empty(merged.get("cdr_amount")) and (not self._na_or_empty(regex_insights.get("cdr_amount"))):
            merged["cdr_amount"] = regex_insights.get("cdr_amount")
        if self._na_or_empty(merged.get("estimate_amount")) and (not self._na_or_empty(regex_insights.get("estimate_amount"))):
            merged["estimate_amount"] = regex_insights.get("estimate_amount")

        for key in ["documents_required", "evaluation_criteria"]:
            current = merged.get(key, [])
            if self._list_na_or_empty(current):
                candidate = regex_insights.get(key, [])
                if isinstance(candidate, list) and len(candidate) > 0:
                    merged[key] = candidate[:4]

        return merged

    def _na_or_empty(self, value):
        if value is None:
            return True
        text = str(value).strip().lower()
        return text in ["", "n/a", "none", "null"]

    def _list_na_or_empty(self, items):
        if not isinstance(items, list) or len(items) == 0:
            return True
        valid = [x for x in items if not self._na_or_empty(x)]
        return len(valid) == 0

    def _fill_na_insights_with_ai(self, insights, doc_text, tender_meta):
        openai_key, model = self._openai_config()
        if openai_key == "":
            return insights

        needs_fill = (
            self._na_or_empty(insights.get("cdr_amount"))
            or self._na_or_empty(insights.get("estimate_amount"))
            or self._list_na_or_empty(insights.get("documents_required", []))
            or self._list_na_or_empty(insights.get("evaluation_criteria", []))
        )
        if not needs_fill:
            return insights

        compact_doc = self._sanitize_doc_text_for_summary(doc_text)
        if len(compact_doc) < 600:
            compact_doc = re.sub(r"\s+", " ", str(doc_text)).strip()
        compact_doc = compact_doc[:50000]
        payload = {
            "model": model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You extract structured tender facts from procurement documents. "
                        "Return strict JSON only. Prefer concrete values from document text and metadata. "
                        "Use N/A only when a value is truly not present."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        "Return ONLY valid JSON with keys: "
                        "cdr_amount, estimate_amount, documents_required, evaluation_criteria, overall_points. "
                        "documents_required/evaluation_criteria/overall_points must be arrays of short strings. "
                        "If a field can be inferred from nearby wording, provide best value instead of N/A. "
                        f"Tender metadata: {json.dumps(tender_meta, ensure_ascii=False)}\n"
                        f"Current extracted hints: {json.dumps(insights, ensure_ascii=False)}\n"
                        f"Document text: {compact_doc}"
                    ),
                },
            ],
            "temperature": 0.1,
            "max_tokens": 420,
        }
        headers = {
            "Authorization": f"Bearer {openai_key}",
            "Content-Type": "application/json",
        }

        try:
            resp = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=60,
            )
            if resp.status_code != 200:
                return insights

            content = resp.json().get("choices", [{}])[0].get("message", {}).get("content", "").strip()
            if content == "":
                return insights

            start = content.find("{")
            end = content.rfind("}")
            if start == -1 or end == -1 or end <= start:
                return insights

            parsed = json.loads(content[start:end + 1])
            merged = dict(insights)

            if self._na_or_empty(merged.get("cdr_amount")) and (not self._na_or_empty(parsed.get("cdr_amount"))):
                merged["cdr_amount"] = str(parsed.get("cdr_amount")).strip()
            if self._na_or_empty(merged.get("estimate_amount")) and (not self._na_or_empty(parsed.get("estimate_amount"))):
                merged["estimate_amount"] = str(parsed.get("estimate_amount")).strip()

            for key in ["documents_required", "evaluation_criteria", "overall_points"]:
                current = merged.get(key, [])
                if not isinstance(current, list):
                    current = []
                if self._list_na_or_empty(current):
                    candidate = parsed.get(key, [])
                    if isinstance(candidate, list):
                        merged[key] = [str(x).strip() for x in candidate if str(x).strip() != ""][:5]

            return merged
        except Exception:
            return insights

    def _build_rule_based_summary(self, insights):
        docs = insights.get("documents_required", [])
        evals = insights.get("evaluation_criteria", [])
        overall = insights.get("overall_points", [])

        lines = [
            "AI Quick Tender Summary",
            f"1) CDR Amount: {insights.get('cdr_amount', 'N/A')}",
            f"2) Estimate Amount: {insights.get('estimate_amount', 'N/A')}",
            "3) Documents Required:",
        ]

        if len(docs) == 0:
            lines.append("- N/A")
        else:
            for item in docs[:4]:
                lines.append(f"- {item}")

        lines.append("4) Evaluation Criteria:")
        if len(evals) == 0:
            lines.append("- N/A")
        else:
            for item in evals[:4]:
                lines.append(f"- {item}")

        lines.append("5) Overall Summary:")
        if len(overall) == 0:
            lines.append("- N/A")
        else:
            for item in overall[:3]:
                lines.append(f"- {item}")

        return "\n".join(lines)

    def _build_ai_quick_summary(self, insights, doc_text="", tender_meta=None):
        openai_key, model = self._openai_config()
        if openai_key == "":
            return [False, "missing_openai_key", ""]
        if tender_meta is None:
            tender_meta = {}

        cleaned_doc_text = self._sanitize_doc_text_for_summary(doc_text)

        cdr_hint = insights.get("cdr_amount", "N/A")
        estimate_hint = insights.get("estimate_amount", "N/A")

        if str(cdr_hint).strip().lower() == "n/a":
            cdr_hint = self._extract_amount_by_keywords(
                cleaned_doc_text,
                ["cdr", "call deposit", "bid security", "earnest money", "emd", "security deposit"],
                "Mentioned"
            )

        if str(estimate_hint).strip().lower() == "n/a":
            estimate_hint = self._extract_amount_by_keywords(
                cleaned_doc_text,
                ["estimate", "estimated amount", "estimated cost", "engineer estimate", "estimated value", "estimated"],
                "Mentioned"
            )

        meta_estimated_cost = tender_meta.get("estimated_cost")
        if str(estimate_hint).strip().lower() == "n/a" and (not self._is_blankish(meta_estimated_cost)):
            estimate_hint = str(meta_estimated_cost).strip()

        compact_payload = {
            "cdr_amount": cdr_hint,
            "estimate_amount": estimate_hint,
            "documents_required": insights.get("documents_required", [])[:4],
            "evaluation_criteria": insights.get("evaluation_criteria", [])[:4],
            "overall_points": insights.get("overall_points", [])[:5],
        }
        meta_payload = {
            "title": tender_meta.get("title", "N/A"),
            "department": tender_meta.get("department", "N/A"),
            "city": tender_meta.get("city", "N/A"),
            "category": tender_meta.get("category", "N/A"),
            "date_opening": tender_meta.get("date_opening", "N/A"),
            "date_published": tender_meta.get("date_published", "N/A"),
            "estimated_cost": tender_meta.get("estimated_cost", "N/A"),
        }

        payload = {
            "model": model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are an expert procurement assistant for WhatsApp users. "
                        "Return strict JSON only with separated fields. "
                        "Use N/A only when the value is truly unavailable in both metadata and text."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        "Return ONLY JSON object with these keys exactly:\n"
                        "cdr_amount, estimate_amount, documents_required, evaluation_criteria, overall_summary\n"
                        "Rules:\n"
                        "- documents_required, evaluation_criteria, overall_summary must be arrays of short strings\n"
                        "- max 4 items per array\n"
                        "- derive cdr_amount and estimate_amount from document and metadata\n"
                        "- prefer concrete values over N/A when reasonable from context\n"
                        "- no markdown, no prose outside JSON\n"
                        f"Tender metadata JSON: {json.dumps(meta_payload, ensure_ascii=False)}\n"
                        f"Extracted hints JSON: {json.dumps(compact_payload, ensure_ascii=False)}\n"
                        f"Document text (cleaned): {cleaned_doc_text[:50000]}"
                    ),
                },
            ],
            "temperature": 0.2,
            "max_tokens": 700,
        }
        headers = {
            "Authorization": f"Bearer {openai_key}",
            "Content-Type": "application/json",
        }

        try:
            resp = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=75,
            )
            if resp.status_code != 200:
                return [False, f"openai_status_{resp.status_code}", ""]

            answer = resp.json().get("choices", [{}])[0].get("message", {}).get("content", "").strip()
            if answer == "":
                return [False, "openai_empty_response", ""]

            start = answer.find("{")
            end = answer.rfind("}")
            if start == -1 or end == -1 or end <= start:
                return [False, "openai_non_json_response", ""]

            parsed = json.loads(answer[start:end + 1])

            cdr_amount = str(parsed.get("cdr_amount", "N/A")).strip() or "N/A"
            estimate_amount = str(parsed.get("estimate_amount", "N/A")).strip() or "N/A"

            docs = parsed.get("documents_required", [])
            if not isinstance(docs, list):
                docs = []
            docs = [str(x).strip() for x in docs if str(x).strip() != ""][:4]

            evals = parsed.get("evaluation_criteria", [])
            if not isinstance(evals, list):
                evals = []
            evals = [str(x).strip() for x in evals if str(x).strip() != ""][:4]

            overall = parsed.get("overall_summary", [])
            if not isinstance(overall, list):
                overall = []
            overall = [str(x).strip() for x in overall if str(x).strip() != ""][:4]

            lines = [
                "AI Quick Tender Summary",
                f"1) CDR Amount: {cdr_amount if cdr_amount != '' else 'N/A'}",
                f"2) Estimate Amount: {estimate_amount if estimate_amount != '' else 'N/A'}",
                "3) Documents Required:",
            ]
            if len(docs) == 0:
                lines.append("- N/A")
            else:
                for item in docs:
                    lines.append(f"- {item}")

            lines.append("4) Evaluation Criteria:")
            if len(evals) == 0:
                lines.append("- N/A")
            else:
                for item in evals:
                    lines.append(f"- {item}")

            lines.append("5) Overall Summary:")
            if len(overall) == 0:
                lines.append("- N/A")
            else:
                for item in overall:
                    lines.append(f"- {item}")

            return [True, "", "\n".join(lines)]
        except Exception as e:
            return [False, f"openai_error: {str(e)}", ""]

    def ai_summary(self,tender_id,table):
        phone = str(self.api.sender).strip() if self.api.sender is not None else ""
        tender_no = str(tender_id).strip() if tender_id is not None else ""
        tender_table = str(table).strip() if table is not None else ""

        if phone == "" or tender_no == "" or tender_table == "":
            self.api.send_message("Unable to generate summary. Missing tender details.")
            return [False, "invalid_input"]

        usage_resp = self._get_ai_summary_usage(phone)
        usage_tracking = True
        if not usage_resp[0]:
            # Usage lookup failed; continue with a fresh counter and attempt to write later.
            used_count = 0
            row_id = None
        else:
            used_count = usage_resp[1]
            row_id = usage_resp[2]
            if used_count >= 50:
                self.api.send_message("Monthly AI Summary limit reached (50/50). Please try again next month.")
                return [False, "limit_reached"]

        tender_cols = [
            "document",
            "title",
            "department",
            "city",
            "category",
            "date_published",
            "date_opening",
        ]
        if tender_table == "sindh_table":
            tender_cols.append("estimated_cost")

        tender_payload = {
            "db": "tenderwala",
            "table": tender_table,
            "cols": tender_cols,
            "ops": "SELECT",
            "where": ["id"],
            "value": [tender_no]
        }
        tender_resp = db_execute(tender_payload)
        if not tender_resp.get("status"):
            self.api.send_message("Unable to fetch tender details for summary right now.")
            return [False, str(tender_resp)]

        rows = tender_resp.get("data", [])
        if len(rows) == 0:
            self.api.send_message("Tender not found for AI summary.")
            return [False, "tender_not_found"]

        row = rows[0]
        tender_map = {}
        for i in range(len(tender_cols)):
            tender_map[tender_cols[i]] = row[i] if len(row) > i else None

        doc_ref = tender_map.get("document")
        tender_meta = {
            "title": tender_map.get("title"),
            "department": tender_map.get("department"),
            "city": tender_map.get("city"),
            "category": tender_map.get("category"),
            "date_published": tender_map.get("date_published"),
            "date_opening": tender_map.get("date_opening"),
            "estimated_cost": tender_map.get("estimated_cost"),
        }

        if doc_ref is None or str(doc_ref).strip() == "" or str(doc_ref).lower() == "none":
            self.api.send_message("Document is not available for this tender. Cannot generate AI summary.")
            return [False, "doc_not_found"]

        self.api.send_message("Preparing AI summary. Please wait...")

        local_path = None
        cleanup_required = False
        try:
            dl_resp = self._download_doc_for_summary(doc_ref, tender_table)
            if not dl_resp[0]:
                self.api.send_message("Unable to download document for summary right now.")
                return [False, dl_resp[1]]

            local_path = dl_resp[2]
            cleanup_required = dl_resp[3]
            doc_text = self._extract_doc_text(local_path)
            insights = self._extract_rule_based_doc_insights(doc_text)
            insights = self._enrich_insights_with_tender_meta(insights, tender_meta)
            insights = self._merge_missing_with_regex(insights, doc_text)
            insights = self._fill_na_insights_with_ai(insights, doc_text, tender_meta)
            ai_resp = self._build_ai_quick_summary(insights, doc_text=doc_text, tender_meta=tender_meta)
            if ai_resp[0]:
                summary_text = ai_resp[2]
            else:
                summary_text = self._build_rule_based_summary(insights)

            next_count = used_count + 1
            remaining = 50 - next_count
            final_text = (
                summary_text
                + "\n\n"
                + f"AI Summary Usage This Month: {next_count}/50"
                + f"\nRemaining: {remaining}"
            )

            if len(final_text) > 3200:
                final_text = final_text[:3200] + "..."

            sent = self.api.send_message(final_text)
            if not sent:
                self.api.send_message("Unable to send AI summary right now. Please try again.")
                return [False, "send_failed"]

            count_updated = self._set_ai_summary_usage(phone, next_count, row_id=row_id)
            if not count_updated:
                self.api.send_message("Summary sent, but usage counter could not be updated.")

            return [True]
        finally:
            if cleanup_required and local_path and os.path.exists(local_path):
                try:
                    os.remove(local_path)
                except Exception:
                    pass
    def remind_me(self,tender_id,table):
        phone = str(self.api.sender).strip() if self.api.sender is not None else ""
        tender_no = str(tender_id).strip() if tender_id is not None else ""
        tender_table = str(table).strip() if table is not None else ""

        if phone == "" or tender_no == "" or tender_table == "":
            self.api.send_message("Unable to set reminder. Missing phone, tender number, or table.")
            return [False, "invalid_input"]

        # Keep original ask table name first, then fallback to reminder_me_table for compatibility.
        active_table = None
        for table_name in ["remind_table", "reminder_me_table"]:
            table_check = {
                "db": "tenderwala",
                "table": table_name,
                "cols": ["id"],
                "ops": "SELECT",
                "where": None,
                "value": None
            }
            check_resp = db_execute(table_check)
            if check_resp.get("status"):
                active_table = table_name
                break

        if active_table is None:
            self.api.send_message("Reminder service is not available right now. Please try again later.")
            return [False, "table_not_found"]

        exists_payload = {
            "db": "tenderwala",
            "table": active_table,
            "cols": ["id"],
            "ops": "SELECT",
            "where": ["phone", "tender_id", "tender_table"],
            "value": [phone, tender_no, tender_table]
        }
        exists_resp = db_execute(exists_payload)
        if exists_resp.get("status") and len(exists_resp.get("data", [])) > 0:
            self.api.send_message("Reminder already added for this tender.")
            return [True, "already_exists"]

        now_text = str(self.security_utils.get_datetime())

        generated_id = uuid4().hex
        insert_attempts = [
            {
                "cols": ["phone", "tender_id", "tender_table", "reminder_time", "status", "created_on"],
                "value": [phone, tender_no, tender_table, now_text, "PENDING", now_text]
            },
            {
                "cols": ["id", "phone", "tender_id", "tender_table", "reminder_time", "message", "status", "sent_on", "created_on"],
                "value": [generated_id, phone, tender_no, tender_table, now_text, "", "PENDING", "", now_text]
            },
            {
                "cols": ["id", "phone", "tender_id", "tender_table"],
                "value": [generated_id, phone, tender_no, tender_table]
            },
            {
                "cols": ["phone", "tender_id", "tender_table"],
                "value": [phone, tender_no, tender_table]
            }
        ]

        insert_resp = {"status": False, "message": "no_insert_attempted"}
        for attempt in insert_attempts:
            payload = {
                "db": "tenderwala",
                "table": active_table,
                "cols": attempt["cols"],
                "ops": "INSERT",
                "where": None,
                "value": attempt["value"]
            }
            insert_resp = db_execute(payload)
            if insert_resp.get("status"):
                break

        if insert_resp.get("status"):
            self.api.send_message("Reminder saved! I will notify you when reminder time is reached! :)")
            return [True]

        self.api.send_message("Unable to save reminder right now. Please try again.")
        return [False, str(insert_resp)]