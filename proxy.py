

class ProxyManagement:
    def __init__(self) -> None:
        self.proxy_host = 'www.proxymesh.com'
    def set_proxy(self):
      
        proxy_port = 12345  # Specify the port used by the proxy server
        proxy_location = 'US'  # Specify the desired location

        # Make a request using the proxy
        self.proxies = {
            'http': f'http://{self.proxy_host}:{proxy_port}',
            'https': f'https://{self.proxy_host}:{proxy_port}'
        }
# url = 'https://example.com'
# response = requests.get(url, proxies=proxies)

# # Process the response
# print(response.text)
