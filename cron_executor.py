from main import app
from server_utilities import Utilities
from ajk_ppra import AJK_Scraper
from gilgit_ppra import Gilgit_Scraper
from ppra_scraping import Faderal_Scraper
from punjab_ppra import punjab_ppra
from main_class import TenderWala,Sindh_Scrapper,KPK_Scrapper
from msg_templates import Urdu, English
from backend import db_execute
import asyncio,sys,threading
import random
from datetime import datetime, timedelta
from train_tenders import main
ADMIN_PHONE = "923056842507"


class CronMessageDispatcher:
    def __init__(self) -> None:
        self.window_cache = {}
        self.template_names = None

    def _parse_datetime(self, raw_value):
        if raw_value is None:
            return None
        value = str(raw_value).strip()
        if value == "" or value.lower() == "none":
            return None

        normalized = value.replace("T", " ").replace("Z", "")
        try:
            return datetime.fromisoformat(normalized)
        except Exception:
            pass

        formats = [
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d %H:%M",
            "%Y-%m-%d",
            "%Y, %m, %d, %H:%M:%S",
            "%Y, %m, %d, %H, %M, %S",
            "%d-%m-%Y %H:%M:%S",
            "%d-%m-%Y"
        ]
        for fmt in formats:
            try:
                return datetime.strptime(normalized, fmt)
            except Exception:
                continue
        return None

    def is_within_24h_window(self, phone):
        phone_key = str(phone).strip()
        if phone_key in self.window_cache:
            return self.window_cache[phone_key]

        payload = {
            "db": "tenderwala",
            "table": "users_table",
            "cols": ["last_texted_on"],
            "ops": "SELECT",
            "where": ["phone"],
            "value": [phone_key]
        }
        resp = db_execute(payload)
        if not resp.get("status") or len(resp.get("data", [])) == 0:
            self.window_cache[phone_key] = False
            return False

        raw_last = resp["data"][0][0] if len(resp["data"][0]) > 0 else None
        last_dt = self._parse_datetime(raw_last)
        if last_dt is None:
            self.window_cache[phone_key] = False
            return False

        within = (datetime.now() - last_dt) <= timedelta(hours=24)
        self.window_cache[phone_key] = within
        return within

    def _fetch_templates(self, api):
        if self.template_names is not None:
            return self.template_names

        names = []
        try:
            resp = api.get_whatsapp_templates()
            if isinstance(resp, dict):
                for row in resp.get("data", []):
                    if isinstance(row, dict) and row.get("name"):
                        names.append(str(row["name"]))
        except Exception:
            names = []

        self.template_names = names
        return self.template_names

    def _resolve_template(self, api, preferred_template):
        preferred = str(preferred_template) if preferred_template else "welcome_msg"
        names = self._fetch_templates(api)
        if len(names) == 0 or preferred in names:
            return preferred
        return names[0]

    def send(self, api, phone, text, preferred_template="welcome_msg"):
        # Ensure text is a clean str (decode bytes if necessary)
        if isinstance(text, bytes):
            try:
                text = text.decode("utf-8", "replace")
            except Exception:
                text = str(text)
        api.sender = str(phone)
        if self.is_within_24h_window(phone):
            sent = api.send_message(str(text))
            return [sent, "message"]

        template_name = self._resolve_template(api, preferred_template)
        sent = api.send_template_msg(template_name)
        return [sent, f"template:{template_name}"]

class ScrapingCron:
    def __init__(self) -> None:
        self.dispatcher = CronMessageDispatcher()
    def start(self,target):
        server_utils = Utilities()
        tenderwala = TenderWala()
        utils = tenderwala.security_utils
        tenderwala.api.sender = ADMIN_PHONE
        
        if target == "sindh_table":     # Running
            ss = Sindh_Scrapper(utils)
        elif target == "kpk_table":     # Running
            ss = KPK_Scrapper(utils)
        elif target == "punjab_table":   # Running
            ss = punjab_ppra(utils)
        elif target == "ajk_table":      # Running
            ss = AJK_Scraper(utils)
        elif target == "gilgit_table":   # Running
            ss = Gilgit_Scraper(utils)
        elif target == "federal_table":   # Running
            ss = Faderal_Scraper(utils)
        else:
            self.dispatcher.send(tenderwala.api, ADMIN_PHONE, f"{target}: Invalid Argument Passed in cron job (example sindh_ppra)")
            return "Invalid Argument"
        
        resp = ss.initiate_scraper()
        if len(resp) > 1:
            self.dispatcher.send(tenderwala.api, ADMIN_PHONE, resp[1])
        else:
            success = True
            data = server_utils.get_tenders(target,col=["id"])
            if data[0]:
                try:
                    data = [i[0] for i in data[1]]
                except Exception as e:
                    self.dispatcher.send(tenderwala.api, ADMIN_PHONE, f"Error in data list: {e}\ndata: {str(data)}")
                    return "Data Failed"
            tender_count = 0
            for row in ss.ppra_data:
                append = True
                
                if row["id"] in data:
                    append  = False
                if append:
                    value = [str(row[i]) for i in row.keys()]
                    value = [*value,"None"]
                    resp = server_utils.insert_into_tenders(target,value=value)
                    if resp["status"]:
                        tender_count += 1
                    else:
                        self.dispatcher.send(tenderwala.api, ADMIN_PHONE, f"{target} [Db Insertion Error]: "+resp["message"]+"\n\n"+str(value))
                        success = False
                        break
            if success:
                self.dispatcher.send(tenderwala.api, ADMIN_PHONE, f"{target}: *Found {str(len(ss.ppra_data))} tenders* & *inserted {str(tender_count)} unique tenders*")
            return "Scraping Complete"

class DeleteTenders:
    def __init__(self) -> None:
        self.tables = ["federal_table","sindh_table","kpk_table","gilgit_table","ajk_table","punjab_table"]
        self.server_utils = Utilities()
        self.tenderwala = TenderWala()
        self.dispatcher = CronMessageDispatcher()
        self.utils = self.tenderwala.security_utils
    def start(self,target):
        txt = ""
        for table in self.tables:
            data = self.server_utils.get_tenders(table,col=["id","date_opening"])
            if data[0]:
                del_count = 0
                for row in data[1]:
                    if self.utils.check_expiry(row[1],table=table):
                        resp = self.server_utils.delete_tender(table,row[0])
                        del_count += 1
                txt += f"{table}: *{str(del_count)}* / {str(len(data[1]))}\n"
        txt += "\n Above Tenders *DELETED*!"
        self.dispatcher.send(self.tenderwala.api, ADMIN_PHONE, txt)
        return "Delete Query Completed"


class SendTendersCron:
    def __init__(self) -> None:
        self.server_utils = Utilities()
        self.notify = TenderWala()
        self.notify.api.sender = ADMIN_PHONE
        self.dispatcher = CronMessageDispatcher()

    def _send_more_tenders_prompt(self, tenderwala):
        return tenderwala.api.send_btn_msg(
            "If you want to receive more tenders, press on Send Tenders button",
            ["Send Tenders"],
            ["send_more_tenders"]
        )

    def get_target_users(self):
        payload = {
            "db": "tenderwala",
            "table": "users_table",
            "cols": ["phone", "status", "lang", "name"],
            "ops": "SELECT",
            "where": None,
            "value": None
        }
        resp = db_execute(payload)
        if not resp.get("status"):
            return [False, f"Users query failed: {str(resp)}"]

        users = []
        for row in resp.get("data", []):
            phone = str(row[0]) if len(row) > 0 else ""
            status = str(row[1]).strip().upper() if len(row) > 1 else ""
            lang = str(row[2]).strip().lower() if len(row) > 2 else "en"
            name = str(row[3]).strip() if len(row) > 3 else "Customer"

            if status in ["UNPAID", "VISITOR", "VISITORS"]:
                continue
            if phone == "":
                continue

            users.append({
                "phone": phone,
                "status": status,
                "lang": lang,
                "name": name if name else "Customer"
            })

        return [True, users]

    def start(self, target):
        users_resp = self.get_target_users()
        if not users_resp[0]:
            self.dispatcher.send(self.notify.api, ADMIN_PHONE, users_resp[1])
            return "Send Tenders Failed"

        users = users_resp[1]
        total = len(users)
        queued = 0
        skipped = 0
        total_tenders_sent = 0
        overflow_prompt_sent = 0

        for user in users:
            within_window = self.dispatcher.is_within_24h_window(user["phone"])

            tenderwala = TenderWala()
            tenderwala.api.sender = user["phone"]
            tenderwala.api.sender_name = user["name"]
            tenderwala.api.user_type = user["status"]

            if user["lang"] == "ur":
                tenderwala.lang = Urdu()
            else:
                tenderwala.lang = English()
            tenderwala.lang.sender = tenderwala.api.sender
            tenderwala.lang.user = tenderwala.api.sender_name
            tenderwala.lang.messages()

            resp = tenderwala.send_tenders(cron=True, run_async=False)
            if resp[0]:
                result = resp[1] if len(resp) > 1 and isinstance(resp[1], dict) else {}
                if int(result.get("sent", 0)) > 0:
                    queued += 1
                    total_tenders_sent += int(result.get("sent", 0))
                    tenderwala.api.utils.update_texted_on(
                        tenderwala.api.sender,
                        str(tenderwala.security_utils.get_datetime())
                    )
                    if result.get("has_more") and within_window and self._send_more_tenders_prompt(tenderwala):
                        overflow_prompt_sent += 1
                else:
                    skipped += 1
            else:
                skipped += 1

        summary = (
            "send_tenders cron *completed*\n"
            + f"*Eligible users*: {total}\n"
            + f"*Users sent*: {queued}\n"
            + f"*Tender templates sent*: {total_tenders_sent}\n"
            + f"*Overflow prompts sent*: {overflow_prompt_sent}\n"
            + f"*Skipped*: {skipped}"
        )
        self.dispatcher.send(self.notify.api, ADMIN_PHONE, summary)
        return "Send Tenders Completed"


class MembershipCron:
    def __init__(self) -> None:
        self.notify = TenderWala()
        self.notify.api.sender = ADMIN_PHONE
        self.dispatcher = CronMessageDispatcher()
        self.default_plan_name = "TenderWala Subscription"

    def _parse_subs_date(self, raw_value):
        if raw_value is None:
            return None
        value = str(raw_value).strip()
        if value == "" or value.lower() == "none":
            return None

        normalized = value.replace("T", " ").replace("Z", "")
        try:
            return datetime.fromisoformat(normalized)
        except Exception:
            pass

        formats = [
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d %H:%M",
            "%Y-%m-%d",
            "%Y, %m, %d, %H:%M:%S",
            "%Y, %m, %d, %H, %M, %S",
            "%d-%m-%Y %H:%M:%S",
            "%d-%m-%Y"
        ]
        for fmt in formats:
            try:
                return datetime.strptime(normalized, fmt)
            except Exception:
                continue
        return None

    def _reminder_message(self, lang, name, days_left):
        if lang == "ur":
            return (
                f"{name}, aap ki *TenderWala* Subscription *{days_left}* din mein EXPIRE ho rahi hai. "
                "Apni service continue rakhne ke liye *RENEWAL Complete* kar dein. "
                "Madad ke liye *Contact Us* par reply karein."
            )
        return (
            f"{name}, your *TenderWala* Subscription will EXPIRE in *{days_left}* day(s). "
            "Please *RENEW* your plan to continue uninterrupted service. "
            "Reply with *Contact Us* if you need help."
        )

    def _expired_message(self, lang, name):
        if lang == "ur":
            return (
                f"{name}, aap ki *TenderWala* Subscription EXPIRE ho chuki hai. "
                "Service dubara start karne ke liye *rejoin/renew* kar dein. "
                "Madad ke liye *Contact Us* par reply karein."
            )
        return (
            f"{name}, your *TenderWala* Subscription has *EXPIRED*. "
            "Please *rejoin/renew* to start receiving tenders again. "
            "Reply with *Contact Us* if you need help."
        )

    def start(self, target):
        payload = {
            "db": "tenderwala",
            "table": "users_table",
            "cols": ["phone", "status", "lang", "name", "subs_date"],
            "ops": "SELECT",
            "where": None,
            "value": None
        }
        resp = db_execute(payload)
        if not resp.get("status"):
            self.dispatcher.send(self.notify.api, ADMIN_PHONE, f"membership cron failed: {str(resp)}")
            return "Membership Cron Failed"

        now = datetime.now()
        reminder_limit = now + timedelta(days=7)

        reminder_sent = 0
        expired_sent = 0
        skipped_status = 0
        skipped_no_date = 0
        skipped_future = 0
        send_failed = 0

        for row in resp.get("data", []):
            phone = str(row[0]).strip() if len(row) > 0 and row[0] is not None else ""
            status = str(row[1]).strip().upper() if len(row) > 1 and row[1] is not None else ""
            lang = str(row[2]).strip().lower() if len(row) > 2 and row[2] is not None else "en"
            name = str(row[3]).strip() if len(row) > 3 and row[3] is not None else "Customer"
            subs_date = row[4] if len(row) > 4 else None

            if phone == "":
                skipped_status += 1
                continue
            if status in ["UNPAID", "VISITOR", "VISITORS", "REGISTERING"]:
                skipped_status += 1
                continue

            expiry_dt = self._parse_subs_date(subs_date)
            if expiry_dt is None:
                skipped_no_date += 1
                continue

            self.notify.api.sender = phone
            if expiry_dt < now:
                # Build expired subscription message and send with plan buttons
                msg = (
                    f"{name}, your subscription has expired. Please resubscribe to one of our plans to continue using TenderWala"
                )
                # Ensure api sender is set
                self.notify.api.sender = phone
                try:
                    # Attempt to send interactive buttons (labels and ids)
                    sent_btn = self.notify.api.send_btn_msg(
                        msg,
                        ["1 Month Plan", "3 Month Plan", "1 Year Plan"],
                        ["plan_1m", "plan_3m", "plan_1y"],
                    )
                    # If send_btn_msg returns truthy/success, count as sent; otherwise fall back
                    if sent_btn:
                        expired_sent += 1
                    else:
                        send_resp = self.dispatcher.send(self.notify.api, phone, msg, "renewal_reminder")
                        if send_resp[0]:
                            expired_sent += 1
                        else:
                            send_failed += 1
                except Exception:
                    # Fallback to template send via dispatcher on error
                    send_resp = self.dispatcher.send(self.notify.api, phone, self._expired_message(lang, name), "renewal_reminder")
                    if send_resp[0]:
                        expired_sent += 1
                    else:
                        send_failed += 1
            elif expiry_dt <= reminder_limit:
                reminder_date = expiry_dt.strftime("%Y-%m-%d")
                sent_template = self.notify.api.send_template_msg(
                    "renewal_reminder",
                    body_params=[self.default_plan_name, reminder_date]
                )
                if sent_template:
                    reminder_sent += 1
                else:
                    send_failed += 1
            else:
                skipped_future += 1

        self.notify.api.sender = ADMIN_PHONE
        summary = (
            "membership cron completed\n"
            + f"*Reminder Sent* (<=7 days): {reminder_sent}\n"
            + f"*Expired Rejoin Sent*: {expired_sent}\n"
            + f"*Skipped Status*: {skipped_status}\n"
            + f"*Skipped no subs_date*: {skipped_no_date}\n"
            + f"*Skipped not-near-expiry*: {skipped_future}\n"
            + f"*Send Failed*: {send_failed}"
        )
        self.dispatcher.send(self.notify.api, ADMIN_PHONE, summary)
        return "Membership Cron Completed"


class EngageCron:
    def __init__(self) -> None:
        self.notify = TenderWala()
        self.notify.api.sender = ADMIN_PHONE
        self.inactive_hours = 12
        self.dispatcher = CronMessageDispatcher()

    def _parse_last_texted_on(self, raw_value):
        if raw_value is None:
            return None
        value = str(raw_value).strip()
        if value == "" or value.lower() == "none":
            return None

        normalized = value.replace("T", " ").replace("Z", "")
        try:
            return datetime.fromisoformat(normalized)
        except Exception:
            pass

        formats = [
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d %H:%M",
            "%Y-%m-%d",
            "%Y, %m, %d, %H:%M:%S",
            "%Y, %m, %d, %H, %M, %S",
            "%d-%m-%Y %H:%M:%S",
            "%d-%m-%Y"
        ]
        for fmt in formats:
            try:
                return datetime.strptime(normalized, fmt)
            except Exception:
                continue
        return None

    def _engage_message(self, lang, name):
        if lang == "ur":
            prompts = [
                f"{name}, main aap ka *AI Tender Assistant* hoon. Kya aap abhi fresh *tenders* dekhna chahtay hain?",
                f"{name}, aaj ke latest tender updates bhej doon?",
                f"{name}, kya main aap ki setting ke mutabiq new tenders abhi bhej doon?"
            ]
        else:
            prompts = [
                f"{name}, I am your AI Tender Assistant. Do you want fresh tenders right now?",
                f"{name}, should I send today’s latest tenders now?",
                f"{name}, want me to fetch new tenders based on your preferences?"
            ]
        return random.choice(prompts)

    def start(self, target):
        payload = {
            "db": "tenderwala",
            "table": "users_table",
            "cols": ["phone", "status", "lang", "name", "last_texted_on"],
            "ops": "SELECT",
            "where": None,
            "value": None
        }
        resp = db_execute(payload)
        if not resp.get("status"):
            self.dispatcher.send(self.notify.api, ADMIN_PHONE, f"engage cron failed: {str(resp)}")
            return "Engage Cron Failed"

        now = datetime.now()
        threshold = timedelta(hours=self.inactive_hours)

        eligible = 0
        engaged_sent = 0
        skipped_no_phone = 0
        skipped_no_last_texted = 0
        skipped_recent = 0
        send_failed = 0

        for row in resp.get("data", []):
            phone = str(row[0]).strip() if len(row) > 0 and row[0] is not None else ""
            lang = str(row[2]).strip().lower() if len(row) > 2 and row[2] is not None else "en"
            name = str(row[3]).strip() if len(row) > 3 and row[3] is not None else "Customer"
            last_texted_on = row[4] if len(row) > 4 else None

            if phone == "":
                skipped_no_phone += 1
                continue

            last_dt = self._parse_last_texted_on(last_texted_on)
            if last_dt is None:
                skipped_no_last_texted += 1
                continue

            if (now - last_dt) < threshold:
                skipped_recent += 1
                continue

            eligible += 1
            txt = self._engage_message(lang, name) + " Reply YES or NO."
            send_resp = self.dispatcher.send(self.notify.api, phone, txt, "welcome_msg")
            sent = send_resp[0]
            if sent:
                engaged_sent += 1
                self.notify.api.utils.update_texted_on(
                    phone,
                    str(self.notify.security_utils.get_datetime())
                )
            else:
                send_failed += 1

        self.notify.api.sender = ADMIN_PHONE
        summary = (
            "engage cron completed\n"
            + f"Threshold hours: {self.inactive_hours}\n"
            + f"Eligible inactive users: {eligible}\n"
            + f"Engagement prompts sent: {engaged_sent}\n"
            + f"Skipped no phone: {skipped_no_phone}\n"
            + f"Skipped no last_texted_on: {skipped_no_last_texted}\n"
            + f"Skipped recent activity: {skipped_recent}\n"
            + f"Send failed: {send_failed}"
        )
        self.dispatcher.send(self.notify.api, ADMIN_PHONE, summary)
        return "Engage Cron Completed"

class AdminWindowReminderCron:
    def __init__(self) -> None:
        self.notify = TenderWala()
        self.notify.api.sender = ADMIN_PHONE
        self.threshold_hours = 20
        self.dispatcher = CronMessageDispatcher()

    def _parse_admin_datetime(self, raw_value):
        return self.dispatcher._parse_datetime(raw_value)

    def _fetch_admin_row(self):
        payload = {
            "db": "tenderwala",
            "table": "users_table",
            "cols": ["phone", "name", "last_texted_on", "window_reminder_sent_on"],
            "ops": "SELECT",
            "where": ["phone"],
            "value": [ADMIN_PHONE]
        }
        return db_execute(payload)

    def start(self, target=None):
        resp = self._fetch_admin_row()
        if not resp.get("status"):
            self.dispatcher.send(
                self.notify.api,
                ADMIN_PHONE,
                f"admin_window cron failed: {str(resp)}"
            )
            return "Admin Window Cron Failed"

        if len(resp.get("data", [])) == 0:
            return "Admin Window Cron Skipped"

        row = resp["data"][0]
        last_texted_on = row[2] if len(row) > 2 else None
        reminder_sent_on = row[3] if len(row) > 3 else None

        last_dt = self._parse_admin_datetime(last_texted_on)
        reminder_dt = self._parse_admin_datetime(reminder_sent_on)
        if last_dt is None:
            return "Admin Window Cron Skipped: invalid last_texted_on"

        now = datetime.now()
        elapsed = now - last_dt
        if elapsed < timedelta(hours=self.threshold_hours):
            return "Admin Window Cron Not Due"

        # Do not resend the reminder until admin interacts again and last_texted_on moves forward.
        if reminder_dt is not None and reminder_dt >= last_dt:
            return "Admin Window Cron Already Reminded"

        reminder_text = (
            "Your WhatsApp chat window is close to expiring. "
            "Tap Extend and send any reply so the 24-hour window stays active."
        )

        sent = self.notify.api.send_btn_msg(
            reminder_text,
            ["Extend"],
            ["admin_extend_window"]
        )
        if not sent:
            sent = self.notify.api.send_message(
                reminder_text + " Reply with any message to renew the window."
            )

        if sent:
            self.notify.api.utils.update_window_reminder_sent_on(
                ADMIN_PHONE,
                str(self.notify.security_utils.get_datetime())
            )
            return "Admin Window Cron Reminder Sent"

        return "Admin Window Cron Send Failed"

#STATUS HANDLER
class StatusHandlerCron:
    def __init__(self) -> None:
        self.utilities = Utilities()
        self.notify = TenderWala()
        self.notify.api.sender = ADMIN_PHONE
        self.dispatcher = CronMessageDispatcher()

    def _parse_subs_date(self, raw_value):
        return self.dispatcher._parse_datetime(raw_value)

    def _trial_membership_message(self, lang, name, days_left):
        if lang == "ur":
            if days_left <= 0:
                return (
                    f"{name}, aap ka 3 din ka trial khatam ho gaya hai. "
                    "Paid member ban kar exclusive services hasil karein aur tenders receive karna jari rakhein."
                )
            return (
                f"{name}, aap ka 3 din ka trial {days_left} din mein khatam ho raha hai. "
                "Paid member ban kar exclusive services hasil karein aur service bina rukawat jari rakhein."
            )
        if days_left <= 0:
            return (
                f"{name}, your 3-day trial has ended. "
                "Join as a paid member to continue receiving tenders and unlock exclusive services."
            )
        return (
            f"{name}, your 3-day trial will end in {days_left} day(s). "
            "Join as a paid member to continue receiving tenders and unlock exclusive services."
        )

    def _unpaid_membership_message(self, lang, name):
        if lang == "ur":
            return (
                f"{name}, aap ki membership active nahi hai. "
                "Paid member ban kar exclusive services aur daily tenders dobara hasil karein."
            )
        return (
            f"{name}, your membership is inactive. "
            "Rejoin as a paid member to resume daily tenders and access exclusive services."
        )

    def _send_membership_invite(self, phone, name, lang, message_text):
        self.notify.api.sender = phone
        self.notify.api.sender_name = name
        self.notify._set_runtime_language(lang)

        within_window = self.dispatcher.is_within_24h_window(phone)
        if within_window:
            sent = self.notify.api.send_btn_msg(
                message_text,
                ["1 Month Plan", "3 Month Plan", "1 Year Plan"],
                ["plan_1m", "plan_3m", "plan_1y"]
            )
            mode = "button"
        else:
            send_resp = self.dispatcher.send(self.notify.api, phone, message_text, "renewal_reminder")
            sent = send_resp[0]
            mode = send_resp[1] if len(send_resp) > 1 else "template"

        if sent:
            try:
                self.notify.api.utils.update_texted_on(
                    phone,
                    str(self.notify.security_utils.get_datetime())
                )
            except Exception:
                pass
        return [bool(sent), mode]
    
    # TO TRIGGER REGISTRATION FOR UNREGISTERED
    def reminders_for_registration(self):
        users_resp = self.utilities.get_unregistered_users()
        if not users_resp[0]:
            return [False, users_resp[1] if len(users_resp) > 1 else "registration query failed"]

        sent = 0
        failed = 0
        tenderwala = TenderWala()
        for row in users_resp[1]:
            phone = str(row[0]).strip() if len(row) > 0 and row[0] is not None else ""
            status = str(row[1]).strip().upper() if len(row) > 1 and row[1] is not None else ""
            lang = str(row[2]).strip().lower() if len(row) > 2 and row[2] is not None else "en"
            name = str(row[3]).strip() if len(row) > 3 and row[3] is not None else "Customer"

            if phone == "":
                failed += 1
                continue

            tenderwala.api.sender = phone
            tenderwala.api.sender_name = name
            tenderwala.api.user_type = status if status != "" else "REGISTERING"
            tenderwala._set_runtime_language(lang)
            try:
                tenderwala.registering_user("Hi")
                sent += 1
            except Exception:
                failed += 1
        
        return [True, {"sent": sent, "failed": failed}]
        
    # TO TRIGGER SUBSCRIPTION FOR TRIAL ENDED OR UNPAID
    def send_subscription_menu(self):
        payload = {
            "db": "tenderwala",
            "table": "users_table",
            "cols": ["phone", "status", "lang", "name", "subs_date"],
            "ops": "SELECT",
            "where": None,
            "value": None
        }
        resp = db_execute(payload)
        if not resp.get("status"):
            return [False, str(resp)]

        now = datetime.now()
        trial_invites_sent = 0
        unpaid_invites_sent = 0
        trial_to_unpaid = 0
        skipped = 0
        failed = 0

        for row in resp.get("data", []):
            phone = str(row[0]).strip() if len(row) > 0 and row[0] is not None else ""
            status = str(row[1]).strip().upper() if len(row) > 1 and row[1] is not None else ""
            lang = str(row[2]).strip().lower() if len(row) > 2 and row[2] is not None else "en"
            name = str(row[3]).strip() if len(row) > 3 and row[3] is not None else "Customer"
            subs_date = row[4] if len(row) > 4 else None

            if phone == "":
                skipped += 1
                continue

            if status == "TRIAL":
                expiry_dt = self._parse_subs_date(subs_date)
                if expiry_dt is None:
                    skipped += 1
                    continue

                if expiry_dt <= now:
                    status_resp = self.utilities.update_user_status(phone, "UNPAID")
                    if not status_resp[0]:
                        failed += 1
                        continue
                    status = "UNPAID"
                    trial_to_unpaid += 1
                    invite_msg = self._unpaid_membership_message(lang, name)
                else:
                    seconds_left = max(0, (expiry_dt - now).total_seconds())
                    days_left = max(1, int((seconds_left + 86399) // 86400))
                    invite_msg = self._trial_membership_message(lang, name, days_left)
                    send_resp = self._send_membership_invite(phone, name, lang, invite_msg)
                    if send_resp[0]:
                        trial_invites_sent += 1
                    else:
                        failed += 1
                    continue

            if status == "UNPAID":
                invite_msg = self._unpaid_membership_message(lang, name)
                send_resp = self._send_membership_invite(phone, name, lang, invite_msg)
                if send_resp[0]:
                    unpaid_invites_sent += 1
                else:
                    failed += 1
                continue

            skipped += 1

        return [True, {
            "trial_invites_sent": trial_invites_sent,
            "unpaid_invites_sent": unpaid_invites_sent,
            "trial_to_unpaid": trial_to_unpaid,
            "skipped": skipped,
            "failed": failed
        }]

class RegistrationCron:
    def __init__(self) -> None:
        self.handler = StatusHandlerCron()
        self.notify = TenderWala()
        self.notify.api.sender = ADMIN_PHONE
        self.dispatcher = CronMessageDispatcher()

    def start(self, target=None):
        registration_resp = self.handler.reminders_for_registration()
        membership_resp = self.handler.send_subscription_menu()

        if not registration_resp[0]:
            self.dispatcher.send(
                self.notify.api,
                ADMIN_PHONE,
                f"registration cron registration-reminder failed: {registration_resp[1]}"
            )
        if not membership_resp[0]:
            self.dispatcher.send(
                self.notify.api,
                ADMIN_PHONE,
                f"registration cron membership-reminder failed: {membership_resp[1]}"
            )

        registration_stats = registration_resp[1] if registration_resp[0] and len(registration_resp) > 1 else {}
        membership_stats = membership_resp[1] if membership_resp[0] and len(membership_resp) > 1 else {}
        summary = (
            "registration cron completed\n"
            + f"*Registration reminders sent*: {int(registration_stats.get('sent', 0))}\n"
            + f"*Registration reminder failed*: {int(registration_stats.get('failed', 0))}\n"
            + f"*Trial invites sent*: {int(membership_stats.get('trial_invites_sent', 0))}\n"
            + f"*UNPAID rejoin invites sent*: {int(membership_stats.get('unpaid_invites_sent', 0))}\n"
            + f"*Trial converted to UNPAID*: {int(membership_stats.get('trial_to_unpaid', 0))}\n"
            + f"*Skipped*: {int(membership_stats.get('skipped', 0))}\n"
            + f"*Membership send failed*: {int(membership_stats.get('failed', 0))}"
        )
        self.dispatcher.send(self.notify.api, ADMIN_PHONE, summary)
        return "Registration Cron Completed"

class ReminderCron:
    def __init__(self) -> None:
        self.notify = TenderWala()
        self.notify.api.sender = ADMIN_PHONE
        self.dispatcher = CronMessageDispatcher()

    def _parse_reminder_time(self, raw_value):
        if raw_value is None:
            return None
        value = str(raw_value).strip()
        if value == "" or value.lower() == "none":
            return None

        normalized = value.replace("T", " ").replace("Z", "")
        try:
            return datetime.fromisoformat(normalized)
        except Exception:
            pass

        formats = [
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d %H:%M",
            "%Y-%m-%d",
            "%Y, %m, %d, %H:%M:%S",
            "%Y, %m, %d, %H, %M, %S",
            "%d-%m-%Y %H:%M:%S",
            "%d-%m-%Y"
        ]
        for fmt in formats:
            try:
                return datetime.strptime(normalized, fmt)
            except Exception:
                continue
        return None

    def _is_already_sent(self, raw_status):
        if raw_status is None:
            return False
        status = str(raw_status).strip().lower()
        return status in ["sent", "done", "completed", "1", "true", "yes"]

    def _build_default_msg(self, tender_id, tender_table):
        tender = str(tender_id).strip() if tender_id is not None else ""
        table = str(tender_table).strip() if tender_table is not None else ""
        if tender != "" and table != "":
            return f"Reminder: Tender {tender} from {table} is due for your follow-up."
        return "Reminder: Your saved tender follow-up time is reached."

    def _mark_sent_in_table(self, reminder_id, table_name):
        now_text = str(self.notify.security_utils.get_datetime())
        payload = {
            "db": "tenderwala",
            "table": table_name,
            "cols": ["status", "sent_on"],
            "ops": "UPDATE",
            "where": ["id"],
            "value": ["SENT", now_text, reminder_id]
        }
        resp = db_execute(payload)
        if resp.get("status"):
            return True

        fallback_payload = {
            "db": "tenderwala",
            "table": table_name,
            "cols": ["status"],
            "ops": "UPDATE",
            "where": ["id"],
            "value": ["SENT", reminder_id]
        }
        fallback_resp = db_execute(fallback_payload)
        return bool(fallback_resp.get("status"))

    def _active_reminder_tables(self):
        active = []
        for table_name in ["reminder_me_table", "remind_table"]:
            check_payload = {
                "db": "tenderwala",
                "table": table_name,
                "cols": ["id"],
                "ops": "SELECT",
                "where": None,
                "value": None
            }
            check_resp = db_execute(check_payload)
            if check_resp.get("status"):
                active.append(table_name)
        return active

    def start(self, target):
        active_tables = self._active_reminder_tables()
        if len(active_tables) == 0:
            self.dispatcher.send(self.notify.api, ADMIN_PHONE, "reminder cron failed: no reminder table found")
            return "Reminder Cron Failed"

        rows_with_source = []
        for table_name in active_tables:
            payload = {
                "db": "tenderwala",
                "table": table_name,
                "cols": ["id", "phone", "tender_id", "tender_table", "reminder_time", "message", "status"],
                "ops": "SELECT",
                "where": None,
                "value": None
            }
            resp = db_execute(payload)
            if not resp.get("status"):
                continue
            for row in resp.get("data", []):
                rows_with_source.append((table_name, row))

        now = datetime.now()
        total_rows = 0
        due_rows = 0
        sent_rows = 0
        skipped_not_due = 0
        skipped_sent = 0
        skipped_invalid = 0
        send_failed = 0
        update_failed = 0

        for source_table, row in rows_with_source:
            total_rows += 1
            reminder_id = row[0] if len(row) > 0 else None
            phone = str(row[1]).strip() if len(row) > 1 and row[1] is not None else ""
            tender_id = row[2] if len(row) > 2 else None
            tender_table = row[3] if len(row) > 3 else None
            reminder_time = row[4] if len(row) > 4 else None
            reminder_message = str(row[5]).strip() if len(row) > 5 and row[5] is not None else ""
            status = row[6] if len(row) > 6 else None

            if reminder_id is None or phone == "":
                skipped_invalid += 1
                continue

            if self._is_already_sent(status):
                skipped_sent += 1
                continue

            due_at = self._parse_reminder_time(reminder_time)
            if due_at is None:
                skipped_invalid += 1
                continue

            if due_at > now:
                skipped_not_due += 1
                continue

            due_rows += 1
            txt = reminder_message if reminder_message != "" else self._build_default_msg(tender_id, tender_table)
            send_resp = self.dispatcher.send(self.notify.api, phone, txt, "renewal_reminder")
            sent = send_resp[0]
            if sent:
                sent_rows += 1
                updated = self._mark_sent_in_table(reminder_id, source_table)
                if not updated:
                    update_failed += 1
                self.notify.api.utils.update_texted_on(
                    phone,
                    str(self.notify.security_utils.get_datetime())
                )
            else:
                send_failed += 1

        self.notify.api.sender = ADMIN_PHONE
        summary = (
            "reminder cron completed\n"
            + f"Source tables: {', '.join(active_tables)}\n"
            + f"Rows checked: {total_rows}\n"
            + f"Due reminders: {due_rows}\n"
            + f"Reminders sent: {sent_rows}\n"
            + f"Skipped already sent: {skipped_sent}\n"
            + f"Skipped not due: {skipped_not_due}\n"
            + f"Skipped invalid: {skipped_invalid}\n"
            + f"Send failed: {send_failed}\n"
            + f"Mark-sent update failed: {update_failed}"
        )
        self.dispatcher.send(self.notify.api, ADMIN_PHONE, summary)
        return "Reminder Cron Completed"
                    
class TrainingCron:
    def __init__(self) -> None:
        pass
    def start(self, target=None):
        tenderwala = TenderWala()
        tenderwala.api.sender = ADMIN_PHONE
        resp = main()
        tenderwala.api.send_message(f"Training Cron Completed: {resp}")
        return "Training Cron Completed"



def thread_func(target):
    if target == "delete":    # Running
        cron = DeleteTenders()
    elif target == "send_tenders":
        cron = SendTendersCron()
    elif target == "membership":   # Running
        cron = MembershipCron()
    elif target == "engage":
        cron = EngageCron()
    elif target == "admin_window":   # Running
        cron = AdminWindowReminderCron()
    elif target == "reminder":     # Running
        cron = ReminderCron()
    elif target == "registration":  
        cron = RegistrationCron()
    elif target == "train":
        cron = TrainingCron()
    else:
        cron = ScrapingCron()
    # run cron in a wrapper to capture exceptions and produce clean logs/messages
    def _run_wrapper():
        try:
            cron.start(target)
        except Exception as e:
            import traceback, os
            try:
                tb = traceback.format_exc()
            except Exception:
                tb = str(e)
            # sanitize traceback to UTF-8
            try:
                tb_clean = tb.encode("utf-8", "replace").decode("utf-8", "replace")
            except Exception:
                tb_clean = str(tb)
            log_line = f"{datetime.now().isoformat()} - Cron '{target}' raised exception:\n{tb_clean}\n"
            try:
                with open("cron_error.log", "a", encoding="utf-8") as f:
                    f.write(log_line)
            except Exception:
                pass
            # attempt to notify admin with a trimmed, safe message
            try:
                admin_api = TenderWala().api
                admin_api.sender = ADMIN_PHONE
                summary = f"Cron {target} failed: {str(e)[:1000]}"
                CronMessageDispatcher().send(admin_api, ADMIN_PHONE, summary)
            except Exception:
                pass

    thread = threading.Thread(target=_run_wrapper)
    thread.start()
    return True
async def cron_func():
    with app.app_context():
       
        target = sys.argv[1]
        resp = thread_func(target)
        return "cron executed"
        
if __name__ == "__main__":
    asyncio.run(cron_func())

# punjab_table, sindh_table, federal_table, gilgit_table, ajk_table, delete, send_tenders, membership, engage, admin_window, reminder
