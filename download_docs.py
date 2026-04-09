import requests
url = "https://eproc.punjab.gov.pk/Tenders/50485052/4854/2406202411393433530153214673.pdf"
resp = requests.get(url)
print(resp.status_code)
if resp.status_code == 200:
    file_name = url.split("/")[-1]
    # Save the content of the response to a file
    with open(file_name, "wb") as file:
        file.write(resp.content)
    print("File downloaded successfully.")
else:
    print(f"Failed to download file. Status code: {resp.status_code}")