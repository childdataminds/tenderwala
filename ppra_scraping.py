import requests,json,html
from bs4 import BeautifulSoup
from urllib.parse import urljoin

class Faderal_Scraper:
    def __init__(self,utils):
        
        # PPRA Variables
        
        self.ppra_sec_codes = {
            "25": "Stationary",
            "23": "Chemical Items",
            "42": "Clothing/Uniform",
            "27": "Electrical Items",
            "37": "Equipments",
            "33": "Research & Development"
        }
        self.ppra_url = "https://epms.ppra.gov.pk/public/tenders/active-tenders?page="
    
        self.pdf_url = "https://epms.ppra.gov.pk"
        self.ppra_header = {
            "Cookie":"ASPSESSIONIDAGTABTAQ=LGLJLFPBEKMMCHOMLGEELCOA; ASPSESSIONIDCGTACSAQ=KGDCKBMCDGGHBGHKGIIMFOPL",
            "Accept-Encoding":"gzip, deflate, br",
            "Sec-Ch-Ua-Mobile":"?1",
             "Sec-Ch-Ua-Platform":"Android",
        "Sec-Fetch-Dest":"document"
        }
        self.utils = utils
    def get_tender_doc_link(self,detail_link):
        try:
            detail_resp = requests.get(detail_link, headers=self.ppra_header, timeout=30)
        except Exception:
            return detail_link

        if detail_resp.status_code != 200:
            return detail_link

        detail_soup = BeautifulSoup(detail_resp.text, 'html.parser')
        anchors = detail_soup.find_all("a")
        fallback_link = None

        for anchor in anchors:
            href = (anchor.get("href") or "").strip()
            if href == "":
                continue
            full_link = urljoin(self.pdf_url, href)
            label = anchor.get_text(" ", strip=True).lower()

            if "download tender document" in label:
                return full_link

            if fallback_link is None and ("/pdf?file=" in full_link or "download" in label):
                fallback_link = full_link

        if fallback_link is not None:
            return fallback_link
        return detail_link
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
            return [False,"Federal: Timeout Error!"]
        except requests.ConnectionError as e:
            return [False, f"Federal: Connection Error: {e}"]
        except Exception as e:
            return [False,f"Federal: Error {e}"]
        print("resp: ",resp.status_code)
        if resp.status_code == 200:
            decoded_html = html.unescape(resp.text)
            soup = BeautifulSoup(decoded_html, 'html.parser')
          
            table = soup.find_all('table')
            # Get the main tenders table (first table on page)
            if table:
                main_table = table[0]
                tbody = main_table.find("tbody")
                
                if not tbody:
                    return [False,"Table Body not found"]

                rows = tbody.find_all("tr")
                # print("Total Rows:", len(rows))
                if len(rows) == 0:
                    return [False]
                for row in rows:
                    # try:
                        cols = row.find_all("td")

                        # Opening Date
                        opening_date = cols[6].find("strong").get_text(strip=True)
                        opening_time_tag = cols[6].find("small")
                        if opening_time_tag:
                            opening_date += " " + opening_time_tag.get_text(strip=True)
                        if self.utils.check_expiry(opening_date,table="federal_table"):
                            continue

                        # Tender No
                        tender_no = row.select_one(".tender-no strong").get_text(strip=True)

                        # Title
                        title = cols[2].find("strong").get_text(strip=True)

                        # Category (first badge inside tender details column)
                        category_tag = cols[2].select_one(".badge")
                        category = category_tag.get_text(strip=True) if category_tag else ""

                        # Department (Organization name)
                        department_tag = row.select_one(".tender-org")
                        department = department_tag.get_text(strip=True) if department_tag else ""

                        # City
                        city_tag = cols[3].select("small")[-1]
                        city = city_tag.get_text(strip=True).split("-")[0].strip()

                        # Date Published
                        date_published = cols[5].get_text(strip=True)

                        
                        # Document Link
                        link_tag = row.select_one("a[href*='tender-details']")
                        detail_link = self.pdf_url + link_tag["href"] if link_tag else ""
                        document_link = self.get_tender_doc_link(detail_link) if detail_link else ""

                        # Append to list
                        self.ppra_data.append({
                            "id": tender_no,
                            "title": title,
                            "department": department,
                            "document": document_link,
                            "date published": date_published,
                            "date opening": opening_date,
                            "city": city,
                            "category": category,
                            "type":"None"
                        })
                      
                    # except Exception as e:
                    #     print("Error in getting row data: ",str(e))
                return [True]
            else:
                return [False,f"Table Not found!\n{str(soup.contents)}"]
                    
        return [True]

                
from utils import ScrapingUtils

if __name__ == "__main__":
    utils = ScrapingUtils()
    scrap = Faderal_Scraper(utils=utils)
    print(scrap.initiate_scraper())
    print(len(scrap.ppra_data))

"""
1: Tender No
2: Heading + sub-heading
3: Download Icon
4: Advertised Date
5: Tender Date + Time
"""