import json
import urllib3
import requests
from urllib.parse import quote, urljoin
from datetime import datetime


class Balochistan_Scraper:
    def __init__(self, utils, tender_type="tenders"):
        self.utils = utils
        self.tender_type = tender_type
        self.server_path = "https://bppdev.vdc.services:5446"
        self.base_site = "http://bppqa.vdc.services"
        self.ppra_data = []
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    def _build_filters_model(self):
        return {
            "AgenciesArray": [],
            "ObjectArray": [],
            "ProcMethodArray": [],
            "DistrictArray": [],
            "DepartmentArray": [],
            "PSDPArray": [],
            "MinCost": 0,
            "MaxCost": 0,
            "YearId": 0,
            "From": "",
            "To": ""
        }

    def _api_url(self, page_no, page_size):
        model = quote(json.dumps(self._build_filters_model(), separators=(",", ":")))
        path = (
            f"/api/LatestTenders/Get_AllTenderDNN/{page_no}/{page_size}/"
            f"{self.tender_type}/null/null//0//0//0//null/null/"
        )
        return f"{self.server_path}{path}?model={model}"

    def _to_datetime(self, value):
        if value is None:
            return None
        value = str(value).strip()
        if value == "":
            return None
        fmts = [
            "%m/%d/%Y %I:%M:%S %p",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d"
        ]
        for fmt in fmts:
            try:
                return datetime.strptime(value, fmt)
            except ValueError:
                continue
        return None

    def _is_expired(self, close_date):
        close_dt = self._to_datetime(close_date)
        if close_dt is None:
            return False
        return datetime.now() > close_dt

    def _build_nit_link(self, tender):
        tender_id = tender.get("Id")
        planning_id = tender.get("PlanningId")
        ptype = str(tender.get("PType") or "").lower()

        if ptype == "rfp":
            return f"{self.server_path}/Reports/GoodsProcurement/RFPNITDocument.html?id={tender_id}"
        if ptype == "anrpc":
            return f"{self.server_path}/Reports/PQN/NITDocumentANRPC.html?id={planning_id}"
        if ptype == "eoics":
            return f"{self.server_path}/Reports/GoodsProcurement/NITDocumentCSEOI.html?id={tender_id}"
        return f"{self.server_path}/Reports/GoodsProcurement/NITDocument.html?id={tender_id}"

    def _build_manual_bid_link(self, tender):
        tender_id = tender.get("Id")
        procurement_category_id = tender.get("ProcurementCategoryID")
        works_category_id = tender.get("WorksCategoryID")

        report_path = None
        if procurement_category_id in [1, 2]:
            report_path = "GetProc_BiddingDocumentCR"
        elif procurement_category_id == 3 and works_category_id == 2:
            report_path = "GetProc_BiddingDocumentWorksLargeCR"
        elif procurement_category_id == 3:
            report_path = "GetProc_BiddingDocumentWorksCR"

        if report_path is None:
            return self._build_nit_link(tender)

        try:
            url = f"{self.server_path}/api/BiddingDocument/{report_path}?BIDID={tender_id}"
            resp = requests.get(url, timeout=40, verify=False)
            if resp.status_code != 200:
                return self._build_nit_link(tender)
            path = resp.json()
            if path and isinstance(path, str):
                return urljoin(self.server_path + "/", path)
        except Exception:
            return self._build_nit_link(tender)
        return self._build_nit_link(tender)

    def build_document_link(self, tender):
        is_manual = bool(tender.get("IsManual"))
        is_e_submission_allowed = bool(tender.get("IsESubmissionAllowed"))
        ptype = str(tender.get("PType") or "").lower()

        if self.tender_type.lower() in ["pq", "eoi"]:
            if is_e_submission_allowed and not is_manual:
                return f"{self.server_path}/Reports/PQN/PQNDocumentReport.html?id={tender.get('PlanningId')}"
            notice_doc = tender.get("tenderNoticeDoc")
            if notice_doc:
                return f"{self.server_path}/Images/GoodsServicesProcurement/{notice_doc}"
            return self._build_nit_link(tender)

        if is_manual and (not is_e_submission_allowed) and ptype == "reg":
            return self._build_manual_bid_link(tender)

        if ptype == "eoics":
            return f"{self.server_path}/Api/CSDocument/GetProc_EOIReportWord?EOI_ID={tender.get('Id')}&format=Word"

        return self._build_nit_link(tender)

    def initiate_scraper(self, page_no=1, page_size=100):
        self.ppra_data = []
        url = self._api_url(page_no, page_size)
        try:
            resp = requests.get(url, timeout=60, verify=False)
        except requests.ConnectTimeout:
            return [False, "Balochistan: Timeout Error!"]
        except requests.ConnectionError as e:
            return [False, f"Balochistan: Connection Error: {e}"]
        except Exception as e:
            return [False, f"Balochistan: Error {e}"]

        if resp.status_code != 200:
            return [False, f"Balochistan: Invalid Response {resp.status_code}"]

        try:
            payload = resp.json()
        except Exception:
            return [False, "Balochistan: Invalid JSON response"]

        tenders = payload.get("tenders") or []
        if len(tenders) == 0:
            return [False]

        for tender in tenders:
            close_date = tender.get("CloseDate")
            if self._is_expired(close_date):
                continue

            tender_id = tender.get("Id")
            if tender_id is None:
                continue

            title = tender.get("TenderTitle") or tender.get("Category") or "Untitled"
            department = tender.get("Department") or "Unknown"
            city = tender.get("Agency") or "Balochistan"
            category = tender.get("Category") or "None"
            date_published = tender.get("PublishedDate") or ""
            date_opening = close_date or ""
            document_link = self.build_document_link(tender)

            self.ppra_data.append({
                "id": str(tender_id),
                "title": str(title),
                "department": str(department),
                "document": str(document_link),
                "date published": str(date_published),
                "date opening": str(date_opening),
                "city": str(city),
                "category": str(category),
                "type": "None"
            })

        if len(self.ppra_data) == 0:
            return [False]
        return [True]


if __name__ == "__main__":
    from utils import ScrapingUtils

    scraper = Balochistan_Scraper(ScrapingUtils())
    result = scraper.initiate_scraper(page_no=1, page_size=25)
    print(result)
    print(len(scraper.ppra_data))
    for row in scraper.ppra_data[:5]:
        print(row["id"], row["document"])
