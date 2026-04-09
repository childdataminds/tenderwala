import requests,json

payload = {
    "SupplierBidder": False,
    "IsContractAwarded": False,
    "isPQEOIBid": True,
    "pagination": {
        "pageNumber": "1",
        "pageSize": "10",
        "orderBy": "",
        "orderByColumnName": "",
        "approvalStatusID": 0,
        "refTypeID": 0,
        "EntityID": 0,
        "RegistrationNumber": None
    },
    "SupplierID": 314229,
    "tenderSearch": None,
    "departmentName": None,
    "loggedInUserID": 314229,
    "loggedInUserOfficeID": "1227",
    "officeID": "1227"
}
header = {
    "Aaa Log": "dXNlcj1tdWF6emFtLmVudGVycHJpc2VzfCB0aW1lPTE3OjUyOjI1IEdNVCswNTAwIChQYWtpc3RhbiBTdGFuZGFyZCBUaW1lKQ==",
    "Accept": "application/json, text/plain, */*",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Accept-Language": "en-US,en;q=0.9,de;q=0.8",
    "authorization": "Bearer eyJ4NXQiOiJNREpsTmpJeE4yRTFPR1psT0dWbU1HUXhPVEZsTXpCbU5tRmpaalEwWTJZd09HWTBOMkkwWXpFNFl6WmpOalJoWW1SbU1tUTBPRGRpTkRoak1HRXdNQSIsImtpZCI6Ik1ESmxOakl4TjJFMU9HWmxPR1ZtTUdReE9URmxNekJtTm1GalpqUTBZMll3T0dZME4ySTBZekU0WXpaak5qUmhZbVJtTW1RME9EZGlORGhqTUdFd01BX1JTMjU2IiwidHlwIjoiYXQrand0IiwiYWxnIjoiUlMyNTYifQ.eyJzdWIiOiIyYWJlZDVmZi00Yzc0LTQ1Y2YtYTE4OC1kOTkxODg1MDQwMTYiLCJhdXQiOiJBUFBMSUNBVElPTl9VU0VSIiwiYXVkIjoiT25BTEozWG1PZXFJamZuMzJQeXlJOVZVRjZnYSIsIm5iZiI6MTczNDk1ODM0NiwiYXpwIjoiT25BTEozWG1PZXFJamZuMzJQeXlJOVZVRjZnYSIsInNjb3BlIjoiZGVmYXVsdCIsImlzcyI6Imh0dHBzOlwvXC9pcy5lcHJvY3VyZS5nb3YucGtcL29hdXRoMlwvdG9rZW4iLCJleHAiOjE3MzQ5NjE5NDYsImlhdCI6MTczNDk1ODM0NiwianRpIjoiYmEwZGNlN2YtYjY2Mi00YmRhLWI5YmQtNzA3ZGMxNzhhODJhIiwiY2xpZW50X2lkIjoiT25BTEozWG1PZXFJamZuMzJQeXlJOVZVRjZnYSJ9.AW0-ABshziFoMLl-7D5IbC6KTdbXvcVUixL-K4jVjrxHGHKJBCvfWSqtdIroD0w8mRhWnKv-yZ84FwKLWWT5D-kEFvLvWvDGN7FeTvVSLrneVaYMU2iZh8iWjKfhvId0Hij4IDSYvQbsQAbMdi5QkFKhbyrmr4x2wu-YvuitVze8QP-oyB3P6qZnVMv3LtlLKBjw6wo5hqcOgd8ewMBA3jMWjirigzjC8RwwpCAdgaJFzUelMCHKYhDn3kS_Rfa7P96XndkjFGnmpU-roUsBIkSA9Xh0WVgj6IKyesgGCDptbqVA2jMviZOgj4-FQiXQX9G2iCBTJL92R8FdY8VxCw",
    "Connection": "keep-alive",
    "Content-Type": "application/json",
    "fui": "DAAAABU4NM9gojKjy4r6WRAAAABrn9pDJQFs6/iMvMFr277ml6ifc2L9TC3BuuOFp8NXqIlbARYrGaw/1/cEOcXIVaA+3CzJxVJW8MXDUaDGzPVqpra7fUG5rcM+0dVxNklY6CjpfMX3",
    "host": "apiprd.eprocure.gov.pk",
    "officedetail": "Punjab-PPRA-Dev",
    "origin": "https://eprocure.gov.pk",
    "referer":  "https://eprocure.gov.pk/",
    "roleid":  "DAAAAEoQsj0O1uI3c9EjgBAAAAD6rP1QIlbNXcKO3IWzXWLuz7eGBaRkWo5UONGLSMvWoSZmBq4=",
    "sec-ch-ua":  '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform":  "macOS",
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-site",
    "sid":  "dXNlcj1tdWF6emFtLmVudGVycHJpc2VzfCB0aW1lPTE3OjUyOjI1IEdNVCswNTAwIChQYWtpc3RhbiBTdGFuZGFyZCBUaW1lKQ==",
    "tid": "MjAyNDEyMjMuMTgyMjU3LjU2Ng==",
    "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "userid": "2abed5ff-4c74-45cf-a188-d99188504016"
}
url = "https://apiprd.eprocure.gov.pk/documentcreation/documenttemplatecreation/1.0.0/api/v1/documenttemplatecreation/getpublisheddocumentinfo"

resp = requests.post(url,data=json.dumps(payload),headers=header)
print(resp.status_code)
print(resp.content)