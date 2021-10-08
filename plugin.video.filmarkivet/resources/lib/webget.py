import requests
import requests_cache


class GetException(Exception):
    pass


class WebGet(object):
    API_URL = "https://www.filmarkivet.se"

    def __init__(self, cache_file):
        self.session = requests.Session()
        self.session.headers["User-Agent"] = "kodi.tv"
        requests_cache.install_cache(cache_file, backend="sqlite", expire_after=604800)

    def get_url(self, url="/"):
        try:
            if not (url.startswith("http://") or url.startswith("https://")):
                url = self.API_URL + url

            request = self.session.get(url)
            request.raise_for_status()
            return request.text
        except Exception as ex:
            raise GetException(ex)
