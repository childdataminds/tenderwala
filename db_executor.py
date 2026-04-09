import requests,json

def get_cities_cats(filters):
    filters = json.loads(filters)
    cats = json.loads(filters['categories'])

    cities = json.loads(filters['cities'])
    new = {
        "categories":cats,
        "cities": cities,
        "institutes": []
    }
    return new
def update_filters():
    payload =  {
                    "db":"tenderwala",
                    "table":"users_table",
                    "cols":None,
                    "ops":"SELECT",
                    "where":None,
                    "value":None
    }
    resp = requests.post("http://pacificproduction.pk/tenderwala/databases",json=payload)

    if resp.status_code == 200 and resp.json()['status']:
        data = resp.json()['data']
        for user in data:
            value = json.loads(user[2])
            print(value['institutes'])
            # filter_dict = get_cities_cats(user[2])
            # print(filter_dict)
            break
            # payload['cols'] = ["filters"]
            # payload['ops'] = "UPDATE"
            # payload['where'] = ["phone"]
            # payload['value'] = [json.dumps(filter_dict),user[0]]
            # resp = requests.post("http://pacificproduction.pk/tenderwala/databases",json=payload)
            # if resp.status_code == 200:
            #     print("Record Updated!")
            # else:
            #     print("Unable to update")
            




    else:
        print(f"Unable to fetch")
def delete_registered_visitor():
    payload =  {
                    "db":"tenderwala",
                    "table":"users_table",
                    "cols":None,
                    "ops":"SELECT",
                    "where":None,
                    "value":None
    }
    resp = requests.post("http://pacificproduction.pk/tenderwala/databases",json=payload)

    if resp.status_code == 200 and resp.json()['status']:
        for user in resp.json()['data']:
            payload =  {
                    "db":"tenderwala",
                    "table":"visitors_table",
                    "cols":None,
                    "ops":"DELETE",
                    "where":["phone"],
                    "value":[user[0]]
    }
            resp = requests.post("http://pacificproduction.pk/tenderwala/databases",json=payload)
            if resp.status_code == 200 and resp.json()['status']:
                print(f"Deleted {user[0]}, {user[1]}")
def update_visitors_status():
    payload =  {
                    "db":"tenderwala",
                    "table":"visitors_table",
                    "cols":['status'],
                    "ops":"UPDATE",
                    "where":["status"],
                    "value":["active",""]
    }
    resp = requests.post("http://pacificproduction.pk/tenderwala/databases",json=payload)
    if resp.status_code == 200 and resp.json()['status']:
        print(f"Updated ")
update_visitors_status()
