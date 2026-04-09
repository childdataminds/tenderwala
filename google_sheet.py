import gspread
from oauth2client.service_account import ServiceAccountCredentials

email = "tender-project@tenders-project-444210.iam.gserviceaccount.com"
api_key = "AIzaSyCJ-T7xBWFgkjck1w4LZSTW39CSJuWM3Wo"

client_id = "801689135111-r4j5t4049kqr85eoapnpvnpvod2ht1l5.apps.googleusercontent.com"
client_secret = "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"

def dump_data(tender):
    # Set up Google Sheets API
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    credentials = ServiceAccountCredentials.from_json_keyfile_name("tenders-project-444210-12c7a0ecc9ad.json", scope)

    # Authorize and open the Google Sheet
    client = gspread.authorize(credentials)
    spreadsheet = client.open("Tenders-Update")  # Replace with your Google Sheet name
    worksheet = spreadsheet.sheet1  # Use the first sheet or specify by name

    existing_records = worksheet.get_all_records()  # Returns a list of dictionaries (one dict per row)
    print("existing:---")
    print(existing_records)
    # Check if the data already exists in the sheet
    data_exists = any(all(str(record.get(key, "")).strip() == str(value).strip() for key, value in tender.items()) for record in existing_records)
    # for record in existing_records:
    #     for key, value in tender.items():
    #         print(record.get(key))
    #         print(record.get(key) == value)

    print(data_exists)
    if not data_exists:
        headers = worksheet.row_values(1)  # Assumes the first row has column names
        row = [tender.get(header, "") for header in headers]  # Map JSON data to column order
        worksheet.append_row(row)
        print("Data added successfully!")
    else:
        print("Row exists!")


tender = {
    "Category": "Construction",
    "Title": "Building Bridge",
    "Publish Date": "2024-12-09",
    "Opening Date": "2024-12-15",
    "Depart Name": "Public Works Department",
    "City": "Lahore",
    "Tender Docs": "http://example.com/docs"
}
dump_data(tender)