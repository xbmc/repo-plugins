from threading import Thread
from http.server import SimpleHTTPRequestHandler
from socketserver import TCPServer
from urllib.parse import parse_qsl
from xbmcaddon import Addon

from lib.dash import generate_dash

class HttpRequestHandler(SimpleHTTPRequestHandler):
	def gen_headers(self, content_length: int = 0):
		if self.path.startswith('/watch?v='):
			self.send_response(200, 'OK')
			if content_length > 0: self.send_header('Content-Length', str(content_length))
			self.send_header('Content-Type', 'application/dash+xml; charset=utf-8')
			self.send_header("Connection", "close")
			self.end_headers()
		else:
			self.send_error(404, "File not Found")
		
	def do_GET(self):
		content = generate_dash(parse_qsl(self.path)[0][1]).encode('utf-8')
		self.gen_headers(len(content))
		self.wfile.write(content)

	def do_HEAD(self):
		self.gen_headers()

class HttpService(Thread):
	def __init__(self):
		super(HttpService, self).__init__()
		self.httpd = None

	def run(self):
		http_port: int = 0 if Addon().getSettingBool('http_port_random') else Addon().getSettingInt('http_port')
		with TCPServer(('127.0.0.1', http_port), HttpRequestHandler) as self.httpd:
			Addon().setSettingInt('http_port', self.httpd.socket.getsockname()[1])
			self.httpd.serve_forever()

	def stop(self, timeout=1):
		if self.httpd is not None: self.httpd.shutdown()
		self.join(timeout)
