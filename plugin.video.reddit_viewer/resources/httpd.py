#file httpd.py
#http://forum.kodi.tv/showthread.php?tid=204064

import threading
import thread
import sys
from cgi import parse_qs
from wsgiref.simple_server import make_server
if sys.version_info >=  (2, 7):
    import json as json
else:
    import simplejson as json


import xbmc


def log(message, level=xbmc.LOGNOTICE):
    xbmc.log("reddit_viewer HTTPD:"+message, level=level)


class TinyWebServer(object):
    def __init__(self, app):
        self.app = app

    def simple_app(self, environ, start_response):
        status = '200 OK'
        headers = [('Content-Type', 'application/json')]
        start_response(status, headers)
        if environ['REQUEST_METHOD'] == 'POST':
            request_body_size = int(environ.get('CONTENT_LENGTH', 0))
            request_body = environ['wsgi.input'].read(request_body_size)
            d = parse_qs(request_body)  # turns the qs to a dict
            return 'From POST: %s' % ''.join('%s: %s' % (k, v) for k, v in d.iteritems())
        else:  # GET
            d = parse_qs(environ['QUERY_STRING'])  # turns the qs to a dict
            #return 'From GET: %s' % ''.join('%s: %s' % (k, v) for k, v in d.iteritems())
            log( str(d) )
            try:
                track_id = str(d['track'])
                #url = self.app.api.get_playable_url(track_id[2:-2])
                url="aaa"
                response = json.dumps([{"track": track_id, "url": url}], indent=4, separators=(',', ': '))
                return response
            except:
                return "Hi"


    def create(self, ip_addr, port):
        self.httpd = make_server(ip_addr, port, self.simple_app)

    def start(self):
        """
        start the web server on a new thread
        """
        self._webserver_died = threading.Event()
        self._webserver_thread = threading.Thread(
                target=self._run_webserver_thread)
        self._webserver_thread.start()

    def _run_webserver_thread(self):
        self.httpd.serve_forever()
        self._webserver_died.set()

    def stop(self):
        if not self._webserver_thread:
            return

        thread.start_new_thread(self.httpd.shutdown, () )
        #self.httpd.server_close()

        # wait for thread to die for a bit, then give up raising an exception.
        #if not self._webserver_died.wait(5):
            #raise ValueError("couldn't kill webserver")
        print "Shutting down internal webserver"