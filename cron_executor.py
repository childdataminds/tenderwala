from main import app
from server_utilities import Utilities
from ajk_ppra import AJK_Scraper
from gilgit_ppra import Gilgit_Scraper
from ppra_scraping import Faderal_Scraper
from main_class import TenderWala,Sindh_Scrapper
from msg_templates import Urdu, English
from backend import db_execute
import asyncio,sys,threading
import random
from datetime import datetime, timedelta

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
        
        if target == "sindh_table":
            ss = Sindh_Scrapper(utils)
        elif target == "ajk_table":
            ss = AJK_Scraper(utils)
        elif target == "gilgit_table":
            ss = Gilgit_Scraper(utils)
        elif target == "federal_table":
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
        self.tables = ["federal_table","sindh_table","gilgit_table","ajk_table","punjab_table"]
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
        txt += "\n Above Tenders deleted!"
        self.dispatcher.send(self.tenderwala.api, ADMIN_PHONE, txt)
        return "Delete Query Completed"


class SendTendersCron:
    def __init__(self) -> None:
        self.server_utils = Utilities()
        self.notify = TenderWala()
        self.notify.api.sender = ADMIN_PHONE
        self.dispatcher = CronMessageDispatcher()

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
        templated = 0

        for user in users:
            if not self.dispatcher.is_within_24h_window(user["phone"]):
                send_resp = self.dispatcher.send(
                    self.notify.api,
                    user["phone"],
                    "We have new tenders for you. Please reply to continue.",
                    "welcome_msg"
                )
                if send_resp[0]:
                    templated += 1
                else:
                    skipped += 1
                continue

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

            resp = tenderwala.send_tenders()
            if resp[0]:
                queued += 1
                tenderwala.api.utils.update_texted_on(
                    tenderwala.api.sender,
                    str(tenderwala.security_utils.get_datetime())
                )
            else:
                skipped += 1

        summary = (
            "send_tenders cron completed\n"
            + f"Eligible users: {total}\n"
            + f"Queued sends: {queued}\n"
            + f"Template-only sent (window crossed): {templated}\n"
            + f"Skipped: {skipped}"
        )
        self.dispatcher.send(self.notify.api, ADMIN_PHONE, summary)
        return "Send Tenders Completed"


class MembershipCron:
    def __init__(self) -> None:
        self.notify = TenderWala()
        self.notify.api.sender = ADMIN_PHONE
        self.dispatcher = CronMessageDispatcher()

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
                f"{name}, aap ki TenderWala subscription {days_left} din mein expire ho rahi hai. "
                "Apni service continue rakhne ke liye renewal complete kar dein. "
                "Madad ke liye Contact Us par reply karein."
            )
        return (
            f"{name}, your TenderWala subscription will expire in {days_left} day(s). "
            "Please renew your plan to continue uninterrupted service. "
            "Reply with Contact Us if you need help."
        )

    def _expired_message(self, lang, name):
        if lang == "ur":
            return (
                f"{name}, aap ki TenderWala subscription expire ho chuki hai. "
                "Service dubara start karne ke liye rejoin/renew kar dein. "
                "Madad ke liye Contact Us par reply karein."
            )
        return (
            f"{name}, your TenderWala subscription has expired. "
            "Please rejoin/renew to start receiving tenders again. "
            "Reply with Contact Us if you need help."
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
                txt = self._expired_message(lang, name)
                send_resp = self.dispatcher.send(self.notify.api, phone, txt, "renewal_reminder")
                if send_resp[0]:
                    expired_sent += 1
                else:
                    send_failed += 1
            elif expiry_dt <= reminder_limit:
                days_left = max((expiry_dt.date() - now.date()).days, 0)
                txt = self._reminder_message(lang, name, days_left)
                send_resp = self.dispatcher.send(self.notify.api, phone, txt, "renewal_reminder")
                if send_resp[0]:
                    reminder_sent += 1
                else:
                    send_failed += 1
            else:
                skipped_future += 1

        self.notify.api.sender = ADMIN_PHONE
        summary = (
            "membership cron completed\n"
            + f"Reminder sent (<=7 days): {reminder_sent}\n"
            + f"Expired rejoin sent: {expired_sent}\n"
            + f"Skipped status: {skipped_status}\n"
            + f"Skipped no subs_date: {skipped_no_date}\n"
            + f"Skipped not-near-expiry: {skipped_future}\n"
            + f"Send failed: {send_failed}"
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
                f"{name}, main aap ka AI Tender Assistant hoon. Kya aap abhi fresh tenders dekhna chahtay hain?",
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
                    



def thread_func(target):
    if target == "delete":
        cron = DeleteTenders()
    elif target == "send_tenders":
        cron = SendTendersCron()
    elif target == "membership":
        cron = MembershipCron()
    elif target == "engage":
        cron = EngageCron()
    elif target == "reminder":
        cron = ReminderCron()
    else:
        cron = ScrapingCron()
    thread = threading.Thread(target=cron.start, args=(target,))
    thread.start()
    return True
async def cron_func():
    with app.app_context():
       
        target = sys.argv[1]
        resp = thread_func(target)
        return "cron executed"
        
if __name__ == "__main__":
    asyncio.run(cron_func())

# punjab_table, sindh_table, federal_table, gilgit_table, ajk_table, delete, send_tenders, membership, engage, reminder