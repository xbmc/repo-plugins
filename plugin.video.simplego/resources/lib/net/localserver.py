"""The small HTTP servers the add-on runs itself: the stream proxy, the play service, the phone login.

Each serves one app: a callable taking a Request and returning a Response. Threaded, silent,
and tolerant of clients hanging up before the answer.
"""

import collections
import threading
from http.server import BaseHTTPRequestHandler
from http.server import HTTPServer
from socketserver import ThreadingMixIn
from urllib.parse import parse_qs
from urllib.parse import urlsplit

# query: the first value of each parameter; body: the POST body as bytes (b"" for a GET).
Request = collections.namedtuple("Request", "method path query body")


class Response(collections.namedtuple("Response", "status content content_type headers")):
    """An answer: status, body (bytes), content type and any (name, value) headers."""

    def __new__(cls, status, content, content_type, headers=()):
        """Make an answer; most have no extra headers."""
        return super().__new__(cls, status, content, content_type, headers)


class _Handler(BaseHTTPRequestHandler):
    def setup(self):
        # Per server: a browser's idle or speculative connection must not hold up the real one.
        self.timeout = self.server.request_timeout
        super().setup()

    def do_GET(self):
        self._answer(b"")

    def do_POST(self):
        self._answer(self.rfile.read(int(self.headers.get("Content-Length") or 0)))

    def _answer(self, body):
        url = urlsplit(self.path)
        query = {name: values[0] for name, values in parse_qs(url.query).items()}
        response = self.server.app(Request(self.command, url.path, query, body))
        try:
            self.send_response(response.status)
            self.send_header("Content-Type", response.content_type)
            self.send_header("Content-Length", str(len(response.content)))
            for name, value in response.headers:
                self.send_header(name, value)
            self.end_headers()
            self.wfile.write(response.content)
        except (BrokenPipeError, ConnectionResetError):
            pass  # the client is gone

    def log_message(self, *args):
        """Log nothing: Kodi's log has no use for each request."""


class _Server(ThreadingMixIn, HTTPServer):
    daemon_threads = True

    def __init__(self, address, app, request_timeout):
        self.app = app
        self.request_timeout = request_timeout
        super().__init__(address, _Handler)


def start(app, host="127.0.0.1", port=0, request_timeout=None):
    """Serve app(Request) -> Response on its own daemon thread; return the server (see stop).

    :param request_timeout: seconds a connection may stay silent; None: no limit
    :raises OSError: the address is taken
    """
    server = _Server((host, port), app, request_timeout)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server


def port(server):
    """Return the port a server listens on (the one picked for port=0)."""
    return server.server_address[1]


def stop(server):
    """Stop serving and free the address."""
    server.shutdown()
    server.server_close()
