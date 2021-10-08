import requests
from bs4 import BeautifulSoup


class WebScraper():

    def __init__(self):
        self.session = requests.Session()
        self.session.headers = {
            "User-Agent": "kodi.tv",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip",
            "DNT": "1", # Do Not Track Request Header
            "Connection": "close"
        }

    def get_html(self, url):
        page_response = self.session.get(url)
        html = BeautifulSoup(page_response.text, "html.parser")
        return html

    def get_json(self, url):
        page_response = self.session.get(url)
        return page_response.json()
