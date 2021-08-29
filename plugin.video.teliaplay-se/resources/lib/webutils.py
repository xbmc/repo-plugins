import urllib.parse
import requests


class WebException(Exception):
    pass


class WebUtils():

    def __init__(self):
        self.session = requests.session()

    def make_request(self, request, headers=None, payload=None):
        url = self.extract_url(request)
        method = list(request.keys())[0]
        if method == "GET":
            response = self.session.get(url, headers=headers, json=payload)
        elif method == "POST":
            response = self.session.post(url, headers=headers, json=payload)
        elif method == "DELETE":
            response = self.session.delete(url, headers=headers, json=payload)
        else:
            raise WebException("Unknown method '{0}'".format(method))
        return response

    def extract_url(self, request):
        method = list(request.keys())[0]

        try:
            path = request[method]["filename"]
        except KeyError:
            path = ""

        try:
            params = request[method]["query"]
        except KeyError:
            params = ""

        url = "{0}://{1}".format(
            request[method]["scheme"], request[method]["host"])
        if path:
            url = urllib.parse.urljoin(url, path)
        if params:
            url = self.append_params(url, params)
        return url

    def append_params(self, url, params):
        return url + "?" + urllib.parse.urlencode(params).replace(
            "%27", "%22")
