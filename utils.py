import datetime,json,urllib.parse,base64,time
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
         if str(text).lower() == "all":
            return [True,text]
         list_ = list(set(str(text).replace(" ","").split(",")))
         for i in list_:
            try:
                 x = int(i)
            except:
                return [False,None]
            try:
               x = items_list[x-1]
            except:
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
       cities_col = filter_data[3:-1]
       completed_steps = []
       c = 1
       for city in cities_col:
            if city is None:
                c += 1
                continue
            city_text = str(city).strip().lower()
            if city_text != "" and city_text != "empty":
                completed_steps.append(c)
            c += 1
       remaining_steps = []
     
       for city in self.all_to_list(filter_data[1],7):
            if int(city) != 7:
               if int(city) not in completed_steps:
                   remaining_steps.append(int(city))
       if len(remaining_steps) > 0:
              name = self.map_list(remaining_steps,province)
              col = self.map_list(remaining_steps,filters_list)
              if len(name) > 1:
                 next_step = name[1]
                 next_col = col[1]
              else:
                 next_step = "Categories"
                 next_col = "categories"
              return name,col,next_step,next_col
       else:
             return None,None,None,None

# x = ScrapingUtils()
# print(x.days_to_open("gilgit_table","03-04-2026"))
# print(x.check_expiry(x.convert_iso_datetime("16-03-2026T00:00:00")))


