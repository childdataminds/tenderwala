import requests,json
from bs4 import BeautifulSoup
from urllib.parse import urljoin
class Gilgit_Scraper:
    def __init__(self,utils):
        
        
       
        self.ppra_url = "https://www.gbppra.gov.pk/procurements/1?page="
        self.base_url = "https://www.gbppra.gov.pk/"
    

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
        c = 1
        while True:
            print("Page: ",str(c))
            resp = self.inner_ppra(str(c))
            if resp[0]:
                c += 1
            else:
                return resp

    def inner_ppra(self,page_no):
    
        ppra_url = self.ppra_url+page_no 
     
        try:
            resp = requests.get(ppra_url, headers=self.ppra_header)
        except requests.ConnectTimeout:
            return [False,"gilgit_table: Timeout Error!"]
        except requests.ConnectionError as e:
            return [False, f"gilgit_table: Connection Error: {e}"]
        except Exception as e:
            return [False,f"gilgit_table: Error {e}"]
        # print("resp: ",resp.status_code)
        if resp.status_code == 200:
            # print(resp.text)
            soup = BeautifulSoup(resp.text, 'html.parser')
            # Prettify the HTML content
            
            table = soup.find("table", class_="table-striped")
            # Get the main tenders table (first table on page)
            if table:
                main_table = table
                tbody = main_table.find("tbody")
                
                if not tbody:
                    return [False,"gilgit_table: Request body does not exist!"]

                rows = tbody.find_all("tr")
                # print("Total Rows:", len(rows))
                if len(rows) == 0:
                    return [False]
                for row in rows:
                    try:
                        cols = row.find_all("td")

                        if len(cols) < 8:
                            continue

                        # Since Gilgit table has no tender number column,
                        # you can generate one using index or detail link id

                        sr_no = cols[0].get_text(strip=True)
                        title = cols[1].get_text(strip=True)
                        tender_type = cols[2].get_text(strip=True)
                        department = cols[3].get_text(strip=True)
                        opening_date = cols[4].get_text(strip=True)
                        closing_date = cols[5].get_text(strip=True)
                        if self.utils.check_expiry(closing_date,table="gilgit_table"):
                            continue
                        # Tender Document Link
                        doc_link_tag = cols[6].find("a")
                        document_link = urljoin(self.base_url, doc_link_tag["href"]) if doc_link_tag else ""

                        # View Details Link
                        view_link_tag = cols[7].find("a")
                        view_link = urljoin(self.base_url, view_link_tag["href"]) if view_link_tag else ""

                        # You can extract tender id from view link
                        # Example: https://www.gbppra.gov.pk/procurementdetails/2383
                        tender_no = view_link.split("/")[-1] if view_link else sr_no

                        self.ppra_data.append({
                            "id": tender_no,
                            "title": title,
                            "department": department,
                            "document": document_link,
                            "date published": opening_date,   # No separate publish date available
                            "date opening": closing_date,
                            "city": "Gilgit Baltistan",
                            "category": tender_type,
                            "type":"None"

                        })
                        
                    except Exception as e:
                        print("Row parsing error:", e)
                return [True]
            else:
                return [False]
                    
        return [True]

                

        
if __name__ == "__main__":
    from utils import ScrapingUtils
    utils = ScrapingUtils()
    scrap = Gilgit_Scraper(utils)
    scrap.initiate_scraper()
