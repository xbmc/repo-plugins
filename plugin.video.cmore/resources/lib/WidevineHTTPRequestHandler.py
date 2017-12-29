import BaseHTTPServer
import urlparse
import urllib

from Widevine import Widevine

wv = Widevine()


class WidevineHTTPRequestHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    def do_HEAD(self):
        self.send_response(200)

    def do_POST(self):
        length = int(self.headers['content-length'])
        wv_challenge = self.rfile.read(length)
        query = dict(urlparse.parse_qsl(urlparse.urlsplit(self.path).query))
        mpd_url = query['mpd_url']
        token = query['license_url'].split('token=')[1]

        try:
            wv_license = wv.get_license(mpd_url, wv_challenge, token)
            self.send_response(200)
            self.end_headers()
            self.wfile.write(wv_license)
            self.finish()
        except Exception as ex:
            self.send_response(400)
            self.wfile.write(ex.value)

    def log_message(self, format, *args):
        """Disable the BaseHTTPServer log."""
        return
