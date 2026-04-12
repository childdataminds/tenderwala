import datetime,json,urllib.parse,base64,time,re
class ScrapingUtils:
    def __init__(self) -> None:
        pass
    
    def convert_iso_datetime(self,iso_date):
        dt = datetime.datetime.fromisoformat(iso_date)
        try:
           dt = str(dt.strftime("%Y-%m-%d %H:%M:%S"))
        except:
            dt = str(dt.strftime("%Y-%m-%dT%H:%M:%S.%f"))
    def get_datetime(self):
        date_str = datetime.datetime.now()
        return date_str.strftime('%Y, %m, %d, %H:%M:%S')
    def convert_datetime(self,date_str):
        date = datetime.datetime.strptime(date_str, '%Y, %m, %d, %H, %M, %S')
        return str(int((date - datetime.datetime(1970, 1, 1)).total_seconds() * 1000))
    def convert_date(self,date_str):
        date_obj = datetime.datetime.fromisoformat(date_str)
        # Convert to UTC
        date_obj_utc = date_obj.astimezone(datetime.timezone.utc)
        # Convert to UNIX timestamp
        return int(date_obj_utc.timestamp())
    def parce_json(self,data):
        json_str = json.dumps(data)
        return str(urllib.parse.quote(json_str))
    def datetime_secs_normal(self,value):
        timestamp = value / 1000  # Convert milliseconds to seconds
        expiry_date = datetime.datetime.utcfromtimestamp(timestamp)
        print(expiry_date)
    def date_secs_to_normal(self,value):
        issued_at = datetime.datetime.utcfromtimestamp(value)
        # Convert to local timezone
        issued_at_local = issued_at.replace(tzinfo=datetime.timezone.utc).astimezone(tz=None)
        print(issued_at_local)
    def current_datetime_in_secs(self):
        date = datetime.datetime.now()
        return self.convert_datetime(date.strftime('%Y, %m, %d, %H, %M, %S'))
    def current_date_in_secs(self):
        date = datetime.datetime.now()
        return str(self.convert_date(date.strftime("%Y-%m-%d %H:%M:%S%z")))
    def encode_token(self,data):
        return base64.urlsafe_b64encode(json.dumps(data).encode('utf-8')).decode('utf-8')
    def decode_token(self,token):
        # header, payload, sign = token.split(".")
        payload = token

        # Decode and parse the JSON payload
        # decoded_payload = base64.urlsafe_b64decode(payload + "==").decode("utf-8")
        
        decoded_payload = base64.urlsafe_b64decode(payload+"==")
        decoded_payload = decoded_payload.decode("utf-8")
        return decoded_payload
        
    def new_date(self,value,hours=False,days=False,minutes=False,after=True,datetime_=False):

        date = datetime.datetime.now()
        if after:
            if hours:
                new = date + datetime.timedelta(hours=value)
            elif days:
                new = date + datetime.timedelta(days=value)
            else:
                new = date + datetime.timedelta(minutes=value)
        else:
            if hours:
                new = date - datetime.timedelta(hours=value)
            elif days:
                new = date - datetime.timedelta(days=value)
            else:
                new = date - datetime.timedelta(minutes=value)
        
        if datetime_:
            return self.convert_datetime(new.strftime('%Y, %m, %d, %H, %M, %S'))
        else:
            return str(self.convert_date(new.strftime("%Y-%m-%d %H:%M:%S%z")))
    def days_to_open(self,table,opening_date):
        if table == "gilgit_cities" or table == "ajk_cities":
            format_ = "%d-%m-%Y"
        elif table == "federal_cities":
            format_ = "%b %d, %Y %I:%M %p"
        elif table == "punjab_cities":
                format_ = "%d %b %Y"
        else:
            format_ = "%Y-%m-%d %H:%M:%S"
        opening_date = datetime.datetime.strptime(opening_date, format_)
        difference = opening_date - datetime.datetime.now()
        return difference.days
    def check_expiry(self,expiry_text,table=""):
         # Convert string to date object
        if table == "gilgit_table" or table == "ajk_table":
            format_ = "%d-%m-%Y"
        elif table == "federal_table":
            format_ = "%b %d, %Y %I:%M %p"
        elif table == "punjab_cities":
                format_ = "%d %b %Y"
        else:
            format_ = "%Y-%m-%d %H:%M:%S"
        expiry_date = datetime.datetime.strptime(expiry_text, format_)
    
         # Compare with today's date
        return datetime.datetime.now() > expiry_date
    def get_expiry_date(self,days_):
         return str(datetime.datetime.now() + datetime.timedelta(days=days_))
    def get_numbers_list(self,text,items_list):
            raw = str(text).strip()
            if raw.lower() == "all":
                return [True,"all"]

            normalized = raw.replace("،", ",")
            extracted = []

            for part in normalized.split(","):
                chunk = str(part).strip()
                if chunk == "":
                     continue

                # Accept WhatsApp keycap inputs like 5️⃣ and mixed formats like "1 3".
                nums = re.findall(r"\d+", chunk)
                if len(nums) == 0:
                     return [False,chunk]
                extracted.extend(nums)

            if len(extracted) == 0:
                return [False,None]

            # Keep order while removing duplicates.
            list_ = []
            for token in extracted:
                if token not in list_:
                     list_.append(token)

            for i in list_:
                try:
                     x = int(i)
                except:
                     return [False,i]

                if x < 1 or x > len(items_list):
                     return [False,i]

            return True,list_
    def map_list(self,text,items_list):
         if type(text) == str:
            if text == "all":
                list_ = [str(i) for i in range(len(items_list))] 
            else:
                list_ = str(text).replace(" ","").split(",")
         else:
             list_ = text
        
         return [items_list[int(i)-1] for i in list_ ]

    def all_to_list(self,items_list,total):
       if str(items_list).lower() == "all":
            return [i for i in range(1,total)]
       else:
            return str(items_list).split(",")
    def cities_selection_logic(self,filter_data,province,filters_list):
          # Keep mapping aligned with ask_prov numbering:
          # 1=Punjab, 2=Sindh, 3=Balochistan, 4=KPK, 5=AJK, 6=Gilgit, 7=Federal.
          choice_map = {
              "1": {"col": "punjab_cities", "name": "Punjab", "idx": 3},
              "2": {"col": "sindh_cities", "name": "Sindh", "idx": 4},
              "3": {"col": "balochistan_cities", "name": "Balochistan", "idx": 7},
              "4": {"col": "kpk_cities", "name": "KPK", "idx": 5},
              "5": {"col": "ajk_cities", "name": "AJK", "idx": 6},
              "6": {"col": "gilgit_cities", "name": "Gilgit", "idx": 8},
          }

          selected_raw = str(filter_data[1]).strip().lower() if len(filter_data) > 1 else ""
          if selected_raw == "all":
              # "all" means all regions with city-level filters (federal excluded by design).
              selected = ["1", "2", "3", "4", "5", "6"]
          else:
              selected = [x.strip() for x in str(filter_data[1]).split(",") if x.strip() != ""]

          # Keep order and remove duplicates from user input.
          ordered_selected = []
          for item in selected:
              if item not in ordered_selected:
                 ordered_selected.append(item)

          pending_cols = []
          pending_names = []
          for choice in ordered_selected:
              # Federal has no city-level step.
              if choice == "7":
                 continue
              meta = choice_map.get(choice)
              if meta is None:
                 continue

              city_value = filter_data[meta["idx"]] if len(filter_data) > meta["idx"] else None
              city_text = "" if city_value is None else str(city_value).strip().lower()
              if city_text in ["", "empty", "none", "null"]:
                 pending_cols.append(meta["col"])
                 pending_names.append(meta["name"])

          if len(pending_cols) == 0:
              return None,None,None,None

          # Always prompt the first pending city step; subsequent calls will move to next.
          next_step = pending_names[0]
          next_col = pending_cols[0]
          return pending_names,pending_cols,next_step,next_col

# x = ScrapingUtils()
# print(x.days_to_open("gilgit_table","03-04-2026"))
# print(x.check_expiry(x.convert_iso_datetime("16-03-2026T00:00:00")))


