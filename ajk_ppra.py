import requests,json
from bs4 import BeautifulSoup

from urllib.parse import urljoin

class AJK_Scraper:
    def __init__(self,utils):
        
        
       
        self.ppra_url = "https://www.ajkppra.gov.pk/advertisements.php"
        self.base_url = "https://www.ajkppra.gov.pk/"

        self.ppra_header = {
            "Cookie":"ASPSESSIONIDAGTABTAQ=LGLJLFPBEKMMCHOMLGEELCOA; ASPSESSIONIDCGTACSAQ=KGDCKBMCDGGHBGHKGIIMFOPL",
            "Accept-Encoding":"gzip, deflate, br",
            "Sec-Ch-Ua-Mobile":"?1",
             "Sec-Ch-Ua-Platform":"Android",
        "Sec-Fetch-Dest":"document"
        }
     
        self.utils = utils
    
    def initiate_scraper(self):
        self.ppra_data = []
        ppra_url = self.ppra_url 
        try:
            resp = requests.get(ppra_url, headers=self.ppra_header)
        except requests.ConnectTimeout:
            return [False,"AJK: Timeout Error!"]
        except requests.ConnectionError as e:
            return [False, f"AJK: Connection Error: {e}"]
        except Exception as e:
            return [False,f"AJK: Error {e}"]
        print("resp: ",resp.status_code)
        if resp.status_code == 200:
            # print(resp.text)
            soup = BeautifulSoup(resp.text, 'html.parser')
            # Prettify the HTML content
            
            table = soup.find("table", class_="table")
            # Get the main tenders table (first table on page)
            if table:
                main_table = table
                

                rows = main_table.find_all("tr")
                print("Total Rows:", len(rows))
                if len(rows) == 0:
                    return False
                for row in rows:
                    try:
                        cols = row.find_all("td")

                        if len(cols) < 7:
                            continue

                        # Since Gilgit table has no tender number column,
                        # you can generate one using index or detail link id

                        procurement_text = cols[0].get_text(strip=True)
                        procurement_no = procurement_text.split()[-1]  # gets 6326
                        
                        title = cols[1].get_text(strip=True)
                        publish_date = cols[2].get_text(strip=True)
                        closing_date = cols[3].get_text(strip=True)
                        department = cols[4].get_text(strip=True)
                        agency = cols[5].get_text(strip=True)
                        if self.utils.check_expiry(closing_date,table="ajk_table"):
                            continue
                        download_tag = cols[6].find("a")
                        download_link = urljoin(self.base_url, download_tag["href"]) if download_tag else None
                        
                        self.ppra_data.append({
                            "id": procurement_no,
                            "title": title,
                            "department": department,
                            "document": download_link,
                            "date published": publish_date,
                            "date opening": closing_date,
                            "city": agency,
                            "category": "None",
                            "type":"None"
                        })
                        
                        

                    except Exception as e:
                        print("Row parsing error:", e)
                # print(self.ppra_data)
                return [True]
            else:
                return [False]
                    
        return [True]

                
from utils import ScrapingUtils
utils = ScrapingUtils()   
        

scrap = AJK_Scraper(utils)
print(scrap.initiate_scraper())

print(scrap.ppra_data)

