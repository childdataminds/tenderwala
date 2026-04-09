import mysql.connector
from mysql.connector import pooling

# accessdb_connection = mysql.connector.connect(
#     host='localhost',
#     user='root',
#     password='Mr@03056842507',
#     database='tenderwala_db'
# )
class DBClass:
    conn = pooling.MySQLConnectionPool(
    pool_name="mypool",
    pool_size=10,
    host='localhost',
    user='root',
    password='Mr@03056842507',
    database='tenderwala_db')
    
 
    databases_ = {
    "tenderwala": {
       
       "users_table": {
        "database": conn,
        "table":"users_table",
        "columns":["phone","email","status","joitn_date","subs_date","name","lang","last_texted_on"]
       },    
       "manage_images": {
        "database": conn,
        "table":"manage_images",
        "columns":["title","img_id","expiry_date"]
       },    
       "federal_table": {
        "database": conn,
        "table":"federal_table",
        "columns":["id","title","department","document","date_published","date_opening","city","category","type","sent_to"]
       },
       "punjab_table": {
        "database": conn,
        "table":"punjab_table",
        "columns":["id","title","department","document","date_published","date_opening","city","category","type","sent_to"]
       },
       "sindh_table": {
        "database": conn,
        "table":"sindh_table",
        "columns":["id","title","department","document","date_published","date_opening","city","category","estimated_cost","sent_to"]
       },
       "kpk_table": {
        "database": conn,
        "table":"kpk_table",
        "columns":["id","title","department","document","date_published","date_opening","city","category","type","sent_to"]
       },
       "ajk_table": {
        "database": conn,
        "table":"ajk_table",
        "columns":["id","title","department","document","date_published","date_opening","city","category","type","sent_to"]
       },
       "gilgit_table": {
        "database": conn,
        "table":"gilgit_table",
        "columns":["id","title","department","document","date_published","date_opening","city","category","type","sent_to"]
       },
       "balochistan_table": {
        "database": conn,
        "table":"balochistan_table",
        "columns":["id","title","department","document","date_published","date_opening","city","category","type","sent_to"]
       },
       "filters_table": {
        "database": conn,
        "table":"filters_table",
        "columns":["phone","provinces","types","punjab_cities","sindh_cities","kpk_cities","ajk_cities","balochistan_cities","gilgit_cities","categories"]
       },
       "all_tenders_table": {
           "database": conn,
           "table": "all_tenders_table",
           "columns": ["id","title","city","category","publish_date","opening_datetime","details","doc_link","department"]
       },
       "user_tenders_table": {
        "database": conn,
        "table":"user_tenders_table",
        "columns":["user_phone","tender_ids"]
       },
       "visitors_table": {
        "database": conn,
        "table":"visitors_table",
        "columns":["name","phone","date"]
    },
    "remind_table": {
     "database": conn,
     "table":"remind_table",
     "columns":["id","phone","tender_id","tender_table","reminder_time","message","status","sent_on","created_on"]
       },
             "ai_summary_usage_table": {
                "database": conn,
                "table":"ai_summary_usage_table",
                "columns":["id","phone","month_key","used_count","updated_on"]
             },
       "reminder_me_table": {
        "database": conn,
        "table":"reminder_me_table",
        "columns":["id","phone","tender_id","tender_table","reminder_time","message","status","sent_on","created_on"]
       }
   }
    }
    def __init__(self):
        pass

                
    
