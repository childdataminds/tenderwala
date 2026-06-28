import datetime
import hashlib
import re
import sys
import requests
import cloudscraper
from bs4 import BeautifulSoup
from urllib.parse import parse_qs, urljoin, urlparse


class punjab_ppra:
    def __init__(self,archive=False) -> None:
        self.archive = archive
        self.scraper = cloudscraper.create_scraper()
        self.push_url = "https://tenderwala.thedataminds.us/push_punjab_tenders"
     
        self.data_index = 11
        self.url = "https://eproc.punjab.gov.pk/ActiveTenders.aspx"
        if archive:
            self.url = "https://eproc.punjab.gov.pk/ArchiveTenders.aspx"
            self.data_index = 12
    
    def check_expiry(self,expiry_text):
        format_ = "%d %b %Y"
        try:
            expiry_date = datetime.datetime.strptime(expiry_text, format_)
        except Exception:
            return False
        return datetime.datetime.now() > expiry_date

    def build_tender_id(self, tender, source_key=""):
        # Use a deterministic hash of the key tender fields plus source links so
        # distinct tenders do not collide.
        id_parts = [
            str(tender.get("title", "")).strip().lower(),
            str(tender.get("department", "")).strip().lower(),
            str(tender.get("category", "")).strip().lower(),
            str(tender.get("type", "")).strip().lower(),
            str(tender.get("date published", "")).strip().lower(),
            str(tender.get("date opening", "")).strip().lower(),
            str(tender.get("city", "")).strip().lower(),
            str(tender.get("document", "")).strip().lower(),
            str(source_key).strip().lower(),
        ]
        raw_key = "||".join(id_parts)
        return "punjab-" + hashlib.sha1(raw_key.encode("utf-8")).hexdigest()[:24]

    def _extract_hidden_fields(self, soup):
        payload = {}
        for input_tag in soup.select("form input"):
            name = input_tag.get("name")
            if not name:
                continue
            input_type = str(input_tag.get("type", "")).lower()
            if input_type in ["hidden", "text"]:
                payload[name] = input_tag.get("value", "")
        return payload

    def _get_total_pages(self, soup):
        page_text = soup.get_text(" ", strip=True)
        match = re.search(r"(\d+)\s+items\s+in\s+(\d+)\s+pages", page_text, re.IGNORECASE)
        if match:
            return int(match.group(2))
        return 1

    def _extract_pager_controls(self, soup):
        numeric_targets = {}
        ellipsis_targets = []
        for link in soup.find_all("a", href=True):
            label = link.get_text(" ", strip=True)
            href = link.get("href", "")
            match = re.search(r"__doPostBack\('([^']+)'", href)
            if not match:
                continue
            event_target = match.group(1)
            if label.isdigit():
                numeric_targets[int(label)] = event_target
            elif label == "...":
                ellipsis_targets.append(event_target)

        numeric_pages = sorted(numeric_targets.keys())
        backward_ellipsis = None
        forward_ellipsis = None
        if len(ellipsis_targets) == 1:
            if len(numeric_pages) > 0 and numeric_pages[0] > 1:
                backward_ellipsis = ellipsis_targets[0]
            else:
                forward_ellipsis = ellipsis_targets[0]
        elif len(ellipsis_targets) >= 2:
            backward_ellipsis = ellipsis_targets[0]
            forward_ellipsis = ellipsis_targets[-1]

        return {
            "numeric_targets": numeric_targets,
            "numeric_pages": numeric_pages,
            "backward_ellipsis": backward_ellipsis,
            "forward_ellipsis": forward_ellipsis,
        }

    def _navigate_to_page(self, soup, page_number):
        pager_windows_seen = set()

        while True:
            pager_controls = self._extract_pager_controls(soup)
            if page_number in pager_controls["numeric_targets"]:
                return self._fetch_page_soup(
                    event_target=pager_controls["numeric_targets"][page_number],
                    current_soup=soup
                )

            numeric_pages = pager_controls["numeric_pages"]
            if len(numeric_pages) == 0:
                return [False, f"Punjab pager controls not found for page {page_number}"]

            pager_window_key = tuple(numeric_pages)
            if pager_window_key in pager_windows_seen:
                return [False, f"Punjab pager loop detected while navigating to page {page_number}"]
            pager_windows_seen.add(pager_window_key)

            event_target = None
            if page_number > numeric_pages[-1]:
                event_target = pager_controls["forward_ellipsis"]
            elif page_number < numeric_pages[0]:
                event_target = pager_controls["backward_ellipsis"]

            if event_target is None:
                return [False, f"Punjab page {page_number} is not reachable from pager window {numeric_pages}"]

            next_page_resp = self._fetch_page_soup(event_target=event_target, current_soup=soup)
            if not next_page_resp[0]:
                return next_page_resp
            soup = next_page_resp[1]

    def _fetch_page_soup(self, event_target=None, current_soup=None):
        if event_target is None or current_soup is None:
            resp = self.scraper.get(self.url, timeout=30)
        else:
            payload = self._extract_hidden_fields(current_soup)
            payload["__EVENTTARGET"] = event_target
            payload["__EVENTARGUMENT"] = ""
            resp = self.scraper.post(self.url, data=payload, timeout=30)

        if resp.status_code != 200:
            return [False, f"punjab_table: Failed to retrieve data. Status code: {resp.status_code}"]
        return [True, BeautifulSoup(resp.text, 'html.parser')]

    def _extract_detail_id(self, detail_href):
        href = str(detail_href).strip()
        if href == "":
            return ""
        parsed = urlparse(href)
        query = parse_qs(parsed.query)
        detail_id = query.get("id", [""])[0]
        return str(detail_id).strip()

    def _format_date_text(self, date_text):
        raw_date = str(date_text).strip()
        try:
            date = datetime.datetime.strptime(raw_date, "%d %b %Y")
        except Exception:
            return raw_date
        return date.strftime("%-d/%-m/%Y %I:%M:%S %p")

    def _build_page_signature(self, page_rows):
        if len(page_rows) == 0:
            return "empty-page"
        signature_parts = []
        for tender in page_rows:
            signature_parts.append(
                "||".join(
                    [
                        str(tender.get("id", "")).strip().lower(),
                        str(tender.get("title", "")).strip().lower(),
                        str(tender.get("document", "")).strip().lower(),
                    ]
                )
            )
        return hashlib.sha1("\n".join(signature_parts).encode("utf-8")).hexdigest()

    def _extract_rows_from_soup(self, soup):
        page_rows = []
        for tr in soup.find_all("tr"):
            cells = tr.find_all("td", recursive=False)
            if len(cells) != 9:
                continue

            title_text = cells[1].get_text(" ", strip=True)
            if title_text in ["", "Work Name (Desc.)", "Procurement Title"]:
                continue

            title_anchor = cells[1].find("a", href=True)
            notice_anchor = cells[7].find("a", href=True)
            bid_anchor = cells[8].find("a", href=True)
            if title_anchor is None and notice_anchor is None and bid_anchor is None:
                continue

            closing_date = cells[4].get_text(" ", strip=True)
            if closing_date in ["", "Close Date"]:
                continue
            if not self.archive and self.check_expiry(closing_date):
                continue

            detail_href = ""
            if title_anchor is not None:
                detail_href = urljoin(self.url, title_anchor.get("href"))

            notice_href = ""
            if notice_anchor is not None:
                notice_href = urljoin(self.url, notice_anchor.get("href"))

            bid_href = ""
            if bid_anchor is not None:
                bid_href = urljoin(self.url, bid_anchor.get("href"))

            document_urls = [doc_url for doc_url in [notice_href, bid_href] if str(doc_url).strip() != ""]
            if detail_href == "" and len(document_urls) == 0:
                continue

            tender = {
                "id": "",
                "category": cells[0].get_text(" ", strip=True),
                "title": title_text,
                "type": cells[2].get_text(" ", strip=True),
                "date published": cells[3].get_text(" ", strip=True),
                "date opening": closing_date,
                "department": cells[5].get_text(" ", strip=True),
                "city": cells[5].get_text(" ", strip=True),
                "document": " , ".join(document_urls)
            }

            tender["date opening"] = self._format_date_text(tender["date opening"])

            detail_id = self._extract_detail_id(detail_href)
            if detail_id != "":
                tender["id"] = f"punjab-{detail_id}"
            else:
                tender["id"] = self.build_tender_id(
                    tender,
                    source_key="||".join([detail_href] + document_urls)
                )
            page_rows.append(tender)
        return page_rows

    def scrape(self):
        print("Url: ",self.url)
        self.ppra_data = []
        self.seen_tender_ids = set()
        self.duplicate_rows = 0
        self.page_count = 0
        first_page_resp = self._fetch_page_soup()
        if not first_page_resp[0]:
            print(first_page_resp[1])
            return first_page_resp

        soup = first_page_resp[1]
        self.all_tenders = 0
        self.total_rough = 0
        total_pages = self._get_total_pages(soup)
        current_page = 1
        page_signatures_seen = set()

        while True:
            self.page_count += 1
            page_rows = self._extract_rows_from_soup(soup)
            page_signature = self._build_page_signature(page_rows)
            if page_signature in page_signatures_seen:
                return [False, f"Punjab pagination loop detected on page {current_page}"]
            page_signatures_seen.add(page_signature)
            self.total_rough += len(page_rows)

            for tender in page_rows:
                self.all_tenders += 1
                if tender["id"] in self.seen_tender_ids:
                    self.duplicate_rows += 1
                    continue
                self.seen_tender_ids.add(tender["id"])
                self.ppra_data.append(tender)

            if current_page >= total_pages:
                break

            next_page = current_page + 1
            next_page_resp = self._navigate_to_page(soup, next_page)
            if not next_page_resp[0]:
                return next_page_resp
            soup = next_page_resp[1]
            current_page = next_page

        self.tenders = len(self.ppra_data)
        return [True]

    def initiate_scraper(self):
        return self.scrape()

    def push_to_endpoint(self, endpoint_url=None):
        target_url = endpoint_url or self.push_url
        payload = {
            "tenders": self.ppra_data
        }
        try:
            resp = requests.post(target_url, json=payload, timeout=120)
        except Exception as e:
            return [False, f"Punjab push failed: {str(e)}"]

        try:
            response_json = resp.json()
        except Exception:
            response_json = {"raw_text": resp.text[:2000]}

        if resp.status_code != 200:
            return [False, response_json]
        return [True, response_json]

if __name__ == "__main__":
    # archive_mode = any(str(arg).strip().lower() == "archive" for arg in sys.argv[1:])
    archive_mode = False
    ppra = punjab_ppra(archive=archive_mode)
    scrape_resp = ppra.scrape()
    if scrape_resp[0]:
        push_resp = ppra.push_to_endpoint()
        print("Push Response: ", push_resp)
    else:
        print("Push skipped because scrape failed: ", scrape_resp)
    print("Total Tenders: ",ppra.all_tenders)
    print("Total Selected Tenders: ",ppra.tenders)
    print("Duplicate Rows Skipped: ", getattr(ppra, "duplicate_rows", 0))
    print("total rough data: ",ppra.total_rough)
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
    
     
            
        
            
        
