import os
import requests,base64,re


class EPADPublicPortalScrapper:
    def __init__(self, utils, office_detail, origin, portal_office_id) -> None:
        self.ppra_data = []
        self.portal_office_id = int(portal_office_id)
        self.ppra_header = {
            "accept": "application/json, text/plain, */*",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "en-US,en;q=0.9,de;q=0.8",
            "access-control-allow-origin": "*",
            "authorization": "Basic YWRtaW46cHByYTEy",
            "connection": "keep-alive",
            "content-type": "application/json",
            "host": "apiprd.eprocure.gov.pk",
            "officedetail": office_detail,
            "origin": origin,
            "referer": f"{origin}/",
            "sec-ch-ua": '"Not:A-Brand";v="99", "Google Chrome";v="145", "Chromium";v="145"',
            "sec-ch-ua-mobile": "?1",
            "sec-ch-ua-platform": "Android",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-site",
            "user-agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Mobile Safari/537.36"
        }
        self.util = utils
    def normalize_doc_id(self,doc_id):
        if doc_id is None:
            return None
        if isinstance(doc_id, int):
            return doc_id if doc_id > 0 else None
        text = str(doc_id).strip()
        if text == "" or text.lower() in ["none","null","nan"]:
            return None
        try:
            value = int(float(text))
            return value if value > 0 else None
        except Exception:
            match = re.search(r"\d+", text)
            if not match:
                return None
            value = int(match.group(0))
            return value if value > 0 else None
    def get_fileGUID(self,doc_id):
        details = self.get_file_details(doc_id)
        if details is None:
            return None
        return details["file_guid"]
    def get_file_details(self,doc_id):
        normalized_id = self.normalize_doc_id(doc_id)
        if normalized_id is None:
            return None
        url = "https://apiprd.eprocure.gov.pk/websiteportal/publicportal/1.0.0/api/v1/publicportal/getallpublisheddocumentdetailbypdid"
        payload = {
            "Id": normalized_id,
            "loggedInUserID": 1,
            "loggedInUserOfficeID": self.portal_office_id
        }
        resp = requests.post(url,headers=self.ppra_header,json=payload,timeout=30)
        if resp.status_code == 200:
            try:
                doc_detail = resp.json()["data"][0]
                file_guid = doc_detail.get("dmS_FileGUID")
                file_id = doc_detail.get("dmS_FileID")
                if file_guid is None or file_id is None:
                    return None
                return {
                    "file_guid": str(file_guid),
                    "file_id": int(file_id)
                }
            except Exception:
                return None
        else:
            print("Request Error: ",resp.status_code)
            return None
    def get_doc(self,doc_id):
        normalized_id = self.normalize_doc_id(doc_id)
        if normalized_id is None:
            return [False,"Invalid or missing document id"]
        file_details = self.get_file_details(doc_id)
        if file_details is None:
            return [False,f"File GUID not found for document id {normalized_id}"]
        url = "https://apiprd.eprocure.gov.pk/documentmanagementsystem/dmspublicapi/1.0.0/api/v1/dmspublicapi/downloadportalfilebyguid"
        payload = {
            "loggedInUserOfficeID": self.portal_office_id,
            "loggedInUserID": 1,
            "ID": file_details["file_id"],
            "idsList": file_details["file_guid"]
        }
        resp = requests.post(url,headers=self.ppra_header,json=payload,timeout=30)
        if resp.status_code == 200:
            try:
                body = resp.json()
            except Exception:
                return [False,"Invalid JSON response from Sindh documents API"]

            try:
               file_data = body["data"]
               file_name = file_data["fileName"]
               file_bytes = file_data["bytes"]
            except Exception:
               return [False,"Documents are not available"]
            
            pdf_bytes = base64.b64decode(file_bytes)

            os.makedirs("static/documents", exist_ok=True)
            with open(os.path.join("static","documents",file_name), "wb") as f:
                f.write(pdf_bytes)
            return [True,file_name]
        else:
            return [False,f"Document API request failed with status {resp.status_code}"]
    def initiate_scraper(self):
        c = 1
        self.ppra_data = []
        while True:
            resp = self.scrape_public_tenders(c)
            if resp[0]:
                c += 1
            else:
                return resp

    def build_tender_row(self, row, opening_date, doc_id):
        raise NotImplementedError

    def scrape_public_tenders(self,page_no):
        tenders_url = "https://apiprd.eprocure.gov.pk/websiteportal/publicportal/1.0.0/api/v1/publicportal/getallpublictenders"

        payload = {
                "pagination": {
                    "pageNumber": str(page_no),
                    "pageSize": "1000",
                    "orderBy": "",
                    "orderByColumnName": "",
                    "approvalStatusID": 0,
                    "refTypeID": 0
                },
                "filter": {
                    "sortOrder": "",
                    "activityStatus": None,
                    "keywords": "",
                    "tenderNo": "",
                    "departmentName": None,
                    "dateOfAdvertisement": None,
                    "closingDate": None,
                    "selectedWorth": None
                },
                "loggedInUserID": 1,
                "loggedInUserOfficeID": self.portal_office_id
            }
       
        try:
            resp = requests.post(tenders_url, headers=self.ppra_header,json=payload,timeout=30)
        except requests.ConnectTimeout:
            return [False,f"{self.__class__.__name__}: Timeout Error!"]
        except requests.ConnectionError as e:
            return [False, f"{self.__class__.__name__}: Connection Error: {e}"]
        except Exception as e:
            return [False,f"{self.__class__.__name__}: Error {e}"]
        print(resp.status_code)
        if resp.status_code == 200:
            
            data = resp.json()["data"]["records"]
            if len(data) > 0:

                for i in range(len(data)):
                    try:
                        opening_date = self.util.convert_iso_datetime(str(data[i]["bidOpeningDate"]))
                        if not self.util.check_expiry(opening_date):
                            doc_id = self.normalize_doc_id(data[i].get("publishedDocumentID"))
                            self.ppra_data.append(self.build_tender_row(data[i], opening_date, doc_id))
                    except Exception as e:
                        pass   
                return [True]
            else:
                return [False]
        else:      
            return [False,f"{self.__class__.__name__}: Invalid Response {str(resp.status_code)}\n Message: {resp.content}"]


class Sindh_Scrapper(EPADPublicPortalScrapper):
    def __init__(self,utils) -> None:
        super().__init__(
            utils=utils,
            office_detail="Sindh-PPRA-Dev",
            origin="https://portalsindh.eprocure.gov.pk",
            portal_office_id=31640
        )

    def build_tender_row(self, row, opening_date, doc_id):
        return {
            "id": str(row["tenderNumber"]),
            "title": str(row["name"]),
            "department": str(row["departmentName"]),
            "document": str(doc_id) if doc_id is not None else "None",
            "date published": str(self.util.convert_iso_datetime(str(row["publishDate"]))),
            "date opening": str(opening_date),
            "city": str(row["location"]),
            "category": "None",
            "estimated cost": str(row["estimatedCost"])
        }


class KPK_Scrapper(EPADPublicPortalScrapper):
    def __init__(self,utils) -> None:
        super().__init__(
            utils=utils,
            office_detail="KPK-PPRA-Dev",
            origin="https://portalkp.eprocure.gov.pk",
            portal_office_id=31603
        )

    def build_tender_row(self, row, opening_date, doc_id):
        return {
            "id": str(row["tenderNumber"]),
            "title": str(row["name"]),
            "department": str(row["departmentName"]),
            "document": str(doc_id) if doc_id is not None else "None",
            "date published": str(self.util.convert_iso_datetime(str(row["publishDate"]))),
            "date opening": str(opening_date),
            "city": str(row["location"]),
            "category": str(row.get("procurementCategory") or "None"),
            "type": "None"
        }

if __name__ == "__main__":
    from utils import ScrapingUtils
    utils = ScrapingUtils()
    sindh = Sindh_Scrapper(utils)
    li = sindh.initiate_scraper()
    print(len(sindh.ppra_data))
    for row in sindh.ppra_data:
        print(row["document"])
        id_ = sindh.get_doc(row["document"])
