

import cloudscraper,datetime
from bs4 import BeautifulSoup


class punjab_ppra:
    def __init__(self,utils,archive=False) -> None:
     
        self.scraper = cloudscraper.create_scraper()
        self.utils = utils
        self.data_index = 11
        self.url = "https://eproc.punjab.gov.pk/ActiveTenders.aspx"
        if archive:
            self.url = "https://eproc.punjab.gov.pk/ArchiveTenders.aspx"
            self.data_index = 12
    

    def scrape(self):
        print("Url: ",self.url)
        self.ppra_data = []
        resp = self.scraper.get(self.url)
        if resp.status_code != 200:
            print("Failed to retrieve data. Status code: ",resp.status_code)
            return [False,f"punjab_table: Failed to retrieve data. Status code: {resp.status_code}"]
        print("status code: ",resp.status_code)
        pdf_url = "https://eproc.punjab.gov.pk/"
        soup = BeautifulSoup(resp.text, 'html.parser')
            # Prettify the HTML content
       
        tables = soup.find_all('table')
        self.c = 0
        self.tenders = 0
        self.all_tenders = 0
        self.total_rough = 0
   
        if tables:
            for table in tables:
                tr_elements = table.find_all('tr')
                for tr_element in tr_elements:
                    tds = tr_element.find_all("td")
                    for td in tds:
                        trs = td.find_all("td")
                        if len(trs)>0:
                            for tr in trs:
                                td = tr.find_all("tr")
                                if len(td) > 0: 
                                    for t in td:
                                        # print(t.text.strip())
                                        # print(len(t))
                                        if len(t) == self.data_index:
                                            t = list(t)
                                            if t[5].text.strip() == "Close Date" or t[5].text.strip() == "":
                                                # print(t[5].text.strip())
                                                print("Invalid date opening")
                                                continue
                                            try:
                                                link = pdf_url+t[8].find('a').get('href')+" , "+pdf_url+t[9].find('a').get('href')
                                            except:
                                                print("Links Not Found!")
                                                continue
                                        
                                            # city = self.find_city(str(t[6].text.strip()))
                                            closing_date = t[5].text.strip()
                                            if self.utils.check_expiry(closing_date,"punjab_cities"):
                                                continue
                                            city = str(t[6].text.strip())
                                            tender = {
                                                "id":"",
                                                "category": t[1].text.strip(),
                                            "title": t[2].text.strip(),
                                            "type": t[3].text.strip(),
                                            "date published": t[4].text.strip(),
                                            "date opening": closing_date,
                                            "department": t[6].text.strip(),
                                            "city": city,
                                            "document": link
                                            }
                                            
                                            date = datetime.datetime.strptime(tender['date opening'],"%d %b %Y")
                                            date = date.strftime("%-d/%-m/%Y %I:%M:%S %p")
                                            tender['date opening'] = date
                                            id_ = "".join(tender['date opening'].split(" "))+"-"+str(pdf_url+t[8].find('a').get('href')).split("/")[-1].split(".")[0]
                                            tender["id"] = id_
                                            self.ppra_data.append(tender)
                                            self.tenders += 1


                                        else:
                                            print("Not Greater")
                                            self.all_tenders += 1
                                            # except:
                                            #     c += 1
                                        # print("-----------------------------")
                                        self.total_rough += 1
            return [True]
        return [False]

# from utils import ScrapingUtils
# utils = ScrapingUtils()  
# ppra = punjab_ppra(utils,archive=True)
# ppra.scrape()
# print("Total Tenders: ",ppra.all_tenders)
# print("Total Selected Tenders: ",ppra.tenders)
# print("total rough data: ",ppra.total_rough)
# print(ppra.ppra_data[0])

# import requests

# payload =  {
#             "db":"tenderwala",
#             "table":"punjab_table",
#             "cols":None,
#             "ops":"INSERT",
#             "where":None,
#             "value":["123124"]
#         }
# url = "https://ai.thedataminds.us/databases"
# for row in ppra.ppra_data:
#     payload["value"] = [row["id"],row[""]]
#     resp = requests.post(url,json=payload)
#     print(resp.status_code)
#     print(resp.json())
"""
1: None
2: Tender Notice
3: Work Name (Desc.)
4: Type (Goods etc.)
5: Publish Date
6: date opening
7: Depart Name
8: None
9: Tender Notice pdf
10: Bidding Doc pdf
11: None
"""
    
     
            
        
            
        