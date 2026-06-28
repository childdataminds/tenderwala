from ApplyQuery import Query
from databases import *

dbClass = DBClass()

# ppra_url = "https://www.ppra.org.pk/dad_city.asp"
ppra_url = "https://www.ppra.org.pk/dad_sec.asp?"
ppra_pdf_url = "https://www.ppra.org.pk/"
ppra_header = {
    "Cookie":"ASPSESSIONIDAGTABTAQ=LGLJLFPBEKMMCHOMLGEELCOA; ASPSESSIONIDCGTACSAQ=KGDCKBMCDGGHBGHKGIIMFOPL",
    "Accept-Encoding":"gzip, deflate, br",
    "Sec-Ch-Ua-Mobile":"?1",
     "Sec-Ch-Ua-Platform":"Android",
"Sec-Fetch-Dest":"document"
}

ppra_city_codes = {
    "85": "bahawalpur",
    "190": "bahawalnagar",
    "7": "multan",
    "208": "lodhran",
    "2": "lahore",
    "83": "rahim yar khan"
}
selected_cities = [ppra_city_codes[key] for key in list(ppra_city_codes.keys())]
types = ["goods"]
category = ["tender notice"]
ppra_sec_codes = {
    "25": "Stationary",
    "23": "Chemical Items",
    "42": "Clothing/Uniform",
    "27": "Electrical Items",
    "37": "Equipments",
    "33": "Research & Development"
}


def db_execute(payload_dict):
    ops = ["SELECT","DELETE","INSERT","UPDATE"]
    # print("table: ",payload_dict["table"])
    try:
       if payload_dict["ops"] in ops:
            try:
               db = dbClass.databases_[payload_dict["db"]]
            except KeyError as e:
                return {"status":False,"message":"Database not found. Please provide correct database name in db"}
            try:
               table = db[payload_dict["table"]]
            except KeyError as e:
                return {"status":False,"message":f"Table Not found in database {db}. Please provide correct table name " }
           
            if payload_dict["where"] != None:
               if type(payload_dict["where"]) == list and len(payload_dict["where"]) > 0:
                   for col in payload_dict["where"]:
                      if col not in table["columns"]:
                          return {"status":False,"message":f"{col} column does not exist in {payload_dict['table']} table" }
               else:
                   return {"status":False,"message":"Please provide correct where value. Value should be a list of column names."}
            if payload_dict["ops"] == "INSERT" and payload_dict["value"] == None:
                return {"status":False,"message":"Please provide values in value key to be inserted in table"}
            
            if payload_dict["cols"] != None:
                if type(payload_dict["cols"]) == list and len(payload_dict["cols"]) > 0:
                   resp = Query(table,col=payload_dict["cols"],value=payload_dict["value"],query=payload_dict["ops"],where=payload_dict["where"])
                else:
                    return {"status":False,"message":"invalid columns supplied. please provide correct list of columns"}
            else:
                resp = Query(table,col=table["columns"],value=payload_dict["value"],query=payload_dict["ops"],where=payload_dict["where"])
            return resp
       else:
           return {"status":False,"message":"Please provide correct operation in ops key. valid values are SELECT,DELETE,INSERT,UPDATE"}
    except KeyError as e:
        return {"status":False,"message":f"Keyerror: {e}"}
def cities():
    file = open('files/pk_cities.txt','r',encoding='utf-8')
    city = str(file.readline()).split(',')
    file.close()
    return city
province = [
'Punjab',
'Sindh',
'KPK',
'AJK',
'Balochistan',
'Gilgit',
'Federal'
]
types = [
'goods',
'works',
'services'
]
categories = [
    "construction & civil work",
"it & technology",
"general store & stationary",
"medical & healthcare & medicine",
"electrical & mechanical",
"vehical & transport",
"food & catering",
"cleaning & maintance",
"education & training",
"security services",
"concultancy & professional services",
"telecom & communication",
"energy & peteroleum",
"agriculture & livestock",
"miscellaneous supplies",
"tender notice",
"services"
]
punjab_cities = [
"bahawalpur",
"bahawalnagar",
"bhakkar",
"dg khan & dera ghazi khan",
"faisalabad",
"gujrawala",
"gujrat",
"hasil pur",
"khanewal",
"kasur",
"lahore",
"lodhran",
"multan",
"miawali",
"okara",
"rawalpindi",
"rahim yar khan",
"sialkot",
"sargodha",
"sheikhupura",
"vehari"
]
sindh_cities = [
"badin",
"ghotki",
"hyderabad",
'jacobabad',
'karachi',
'khairpur',
'larkana',
'mirpurkhas',
'sukkur',
'shaheed benazirabad',
'thatta'
]
kpk_cities = [
'abbotabad',
'bannu',
'charsadda',
'dera ismail khan & di khan',
'kohat',
'mardan',
'mingora',
'majsehra',
'pehsawar',
'swabi'
]
ajk_cities = [
'bagh',
'hattian bala',
'haveli',
'kotli',
'mirpur',
'muzaffarabad',
'rawalakot'
]
gilgit_cities = [
'chillas',
'hunza',
'gilgit',
'ghizer',
'ghanche',
'skardu'
]
balochistan_cities = [
'chaman',
'gwadar',
'hub',
'khuzdar',
'quetta',
'sibi',
'turbat',
'zhob'
]
prov_cities = {"punjab_cities":{"list":punjab_cities,"col_index":3,"name":"Punjab"},
               "sindh_cities":{"list":sindh_cities,"col_index":4,"name":"Sindh"},
               "kpk_cities":{"list":kpk_cities,"col_index":5,"name":"KPK"},
               "ajk_cities":{"list":ajk_cities,"col_index":6,"name":"AJK"},
               "gilgit_cities":{"list":gilgit_cities,"col_index":7,"name":"Gilgit"},
               "balochistan_cities":{"list":balochistan_cities,"col_index":8,"name":"Balochistan"},
              "categories":{"list":categories,"col_index":9,"name":"Categories"}}

prov_indexes = {
    "1":["punjab_table"],
    "2":["sindh_table"],
    "3":["balochistan_table"],
    "4":["kpk_table"],
    "5":["ajk_table"],
    "6":["gilgit_table"],
    "7":["federal_table"],
    "all":["punjab_table","sindh_table","balochistan_table","kpk_table","ajk_table","gilgit_table","federal_table"]
}
