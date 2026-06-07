import base64
import requests
from requests.auth import HTTPBasicAuth

from resources.lib.errors import ApiError
from resources.lib.log import log

USERNAME = base64.b64decode("c2l0ZXdlYg==").decode()
PASSWORD = base64.b64decode("Nk1oOFBjMm5L").decode()
BASE_API_URL = "https://api.radioplayer.fr/v2"

class RadioplayerAPI:

    def __init__(self, session=None):
        self.session = session or requests.Session()
        self.session.auth = HTTPBasicAuth(USERNAME, PASSWORD)

    def _build_url(self, path: str) -> str:
        return BASE_API_URL + path

    def get_stream_url(self, stream_id: int):
        r = self.session.get(self._build_url(f"/radios/{stream_id}/streams"))
        if r.status_code != 200:
            log.error(f"Unexpected status code {r.status_code}")
            raise ApiError("Failed to get stream ID")
        j = r.json()

        url = None
        for stream in j["streams"]:
            quality = stream["quality"]
            url = stream["url"]
            if quality == "hls":
                return url
        if url is None:
            raise ApiError("Failed to found a valid stream url")
        return url

    def get_categories(self) -> list:
        r = self.session.get(self._build_url("/categories/radios"))
        if r.status_code != 200:
            log.error(f"Unexpected status code {r.status_code}")
            raise ApiError("Failed to fetch categories")
        j = r.json()
        categories = []
        for category in j["categories"]:
            categories.append({
                "name": category["name"],
                "id": category["id"],
            })
        return categories

    def _get_stations_from_services(self, services: list) -> list:
        stations = []
        for service in services:
            stations.append({
                "name": service["nom"],
                "description": service["description"],
                "image_url": service["image"]["url"],
                "id": service["rpID"],
            })
        return stations

    def get_radios(self, category_id: int) -> list:
        r = self.session.get(self._build_url(f"/radios?cat={category_id}"))
        if r.status_code != 200:
            log.error(f"Unexpected status code {r.status_code}")
            raise ApiError("Failed to fetch radios")
        j = r.json()
        return self._get_stations_from_services(j["services"])

    def get_recommended_stations(self) -> list:
        r = self.session.get(self._build_url("/medias/website/recommendations"))
        if r.status_code != 200:
            log.error(f"Unexpected status code {r.status_code}")
            raise ApiError("Failed to fetch recommended stations")
        j = r.json()
        return self._get_stations_from_services(j["services"])