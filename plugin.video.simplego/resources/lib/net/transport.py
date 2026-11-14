"""HTTP for the client on the standard library alone (see Session).

The plugin starts a fresh interpreter for every list, and importing requests
cost about a second of each on a Chromecast (measured 2026-10-28: http.client
and ssl 0.17 s, requests 0.99 s on top), for the little the client needs.
"""

import gzip
import http.client
import json as jsonlib
import select
import ssl
import threading
from urllib.parse import urlencode
from urllib.parse import urljoin
from urllib.parse import urlsplit

REDIRECTS = (301, 302, 303, 307, 308)
MAX_REDIRECTS = 10
# A caller that names none must not wait forever.
TIMEOUT = 20
# Sent again on a fresh connection when a kept one fails: the server may have handled the
# first try already, and a repeated POST (a stream session, a saved position) is not harmless.
IDEMPOTENT = ("GET", "HEAD", "OPTIONS")
# TLS contexts by CA bundle, one per process: loading a bundle is costly (most of a
# second on a PC for certifi's) and every stream's proxy has a session of its own.
_CONTEXTS = {}
_CONTEXTS_LOCK = threading.Lock()
# Not sent on to another host when a redirect leads there, as requests and urllib3 do.
PRIVATE_HEADERS = ("authorization", "cookie")


class Error(OSError):
    """A request that failed: no connection, a timeout, a broken body, or (raise_for_status) an error status."""


class Response:
    """What a request got back: status_code, ok, headers (any case), cookies, content, text, json()."""

    def __init__(self, status, headers, content, url, error=Error):
        self.status_code = status
        self._error = error
        self.ok = status < 400
        self.headers = headers
        self.content = content
        self.url = url
        self.cookies = _Cookies(headers.get_all("Set-Cookie") or [])

    @property
    def text(self):
        """Return the body as text, in the charset the server named (UTF-8 if none)."""
        return self.content.decode(self.headers.get_content_charset() or "utf-8", "replace")

    def json(self):
        """Return the body parsed as JSON; ValueError if it is not."""
        return jsonlib.loads(self.content.decode("utf-8"))

    def raise_for_status(self):
        """Raise the session's error for an error status (4xx, 5xx)."""
        if not self.ok:
            # Without the query: it may carry a token, and errors end up in the log.
            parts = urlsplit(self.url)
            raise self._error("HTTP %s for %s://%s%s" % (self.status_code, parts.scheme, parts.netloc, parts.path))


class _Cookies:
    def __init__(self, set_cookies):
        self._values = {}
        for line in set_cookies:
            name, _, value = line.split(";", 1)[0].partition("=")
            if name.strip():
                self._values[name.strip()] = value.strip()

    def get_dict(self):
        """Return the cookies the response set, by name."""
        return dict(self._values)


class Session:
    """Requests over kept connections, one pool per host, safe from several threads at once.

    :param error: the exception class failures are raised as (see Error)
    """

    def __init__(self, error=Error):
        self.headers = {}
        self.verify = True  # or the path of a CA bundle
        self._error = error
        self._idle = {}  # (scheme, host, port) -> connections not in use
        self._lock = threading.Lock()
        self._context = None

    def get(self, url, **kwargs):
        """Send a GET to url (see request)."""
        return self.request("GET", url, **kwargs)

    def post(self, url, **kwargs):
        """Send a POST to url (see request)."""
        return self.request("POST", url, **kwargs)

    def request(self, method, url, params=None, data=None, json=None, headers=None, timeout=TIMEOUT, allow_redirects=True):
        """Send a request and return its Response, following redirects unless told not to.

        :param data: the body as bytes or text
        :param json: a body to send as JSON instead
        """
        body = data.encode("utf-8") if isinstance(data, str) else data
        sent = dict(self.headers, **{"Accept-Encoding": "gzip"})
        if json is not None:
            body = jsonlib.dumps(json).encode("utf-8")
            sent["Content-Type"] = "application/json"
        sent.update(headers or {})
        if params:
            url += ("&" if urlsplit(url).query else "?") + urlencode(params)
        for _ in range(MAX_REDIRECTS + 1):
            response = self._send(method, url, body, sent, timeout)
            location = response.headers.get("Location")
            if not allow_redirects or response.status_code not in REDIRECTS or not location:
                return response
            target = urljoin(url, location)
            if urlsplit(target).netloc != urlsplit(url).netloc:
                sent = {k: v for k, v in sent.items() if k.lower() not in PRIVATE_HEADERS}
            url = target
            if response.status_code == 303 or (response.status_code in (301, 302) and method == "POST"):
                method, body = "GET", None
        return response

    def close(self):
        """Close the kept connections."""
        with self._lock:
            idle, self._idle = self._idle, {}
        for connections in idle.values():
            for connection in connections:
                connection.close()

    def _send(self, method, url, body, headers, timeout):
        parts = urlsplit(url)
        key = (parts.scheme, parts.hostname, parts.port)
        path = (parts.path or "/") + ("?" + parts.query if parts.query else "")
        # A kept connection the server has closed meanwhile is left out before use (see _connection);
        # one it closes just then fails at once, and an idempotent request tries again on a new one.
        for reuse in (True, False):
            connection, kept = self._connection(key, timeout, reuse)
            try:
                connection.request(method, path, body=body, headers=headers)
                raw = connection.getresponse()
                content = raw.read()
            except (OSError, http.client.HTTPException) as e:
                connection.close()
                if kept and method in IDEMPOTENT and not isinstance(e, TimeoutError):
                    continue
                raise self._error("network: %s" % e) from e
            if raw.will_close:
                connection.close()
            else:
                with self._lock:
                    self._idle.setdefault(key, []).append(connection)
            if raw.headers.get("Content-Encoding") == "gzip":
                try:
                    content = gzip.decompress(content)
                except (OSError, EOFError) as e:
                    raise self._error("network: broken gzip body from %s: %s" % (url, e)) from e
            return Response(raw.status, raw.headers, content, url, self._error)
        raise self._error("network: no connection")  # not reached: the second try raises

    def _connection(self, key, timeout, reuse):
        """Return (a connection to the host, whether it is a kept one)."""
        while reuse:
            with self._lock:
                idle = self._idle.get(key)
                connection = idle.pop() if idle else None
            if connection is None:
                break
            if _dropped(connection):
                connection.close()
                continue
            connection.timeout = timeout
            connection.sock.settimeout(timeout)
            return connection, True
        scheme, host, port = key
        if scheme == "https":
            return http.client.HTTPSConnection(host, port, timeout=timeout, context=self._ssl()), False
        return http.client.HTTPConnection(host, port, timeout=timeout), False

    def _ssl(self):
        if self._context is None:
            self._context = _context(self.verify)
        return self._context


def _dropped(connection):
    """Return whether an idle kept connection is unusable: no socket, or the server closed it.

    An idle connection has nothing to read; readable means the server's close (or stray bytes).
    """
    sock = connection.sock
    if sock is None:
        return True
    try:
        return bool(select.select([sock], [], [], 0)[0])
    except (OSError, ValueError):
        return True


def _context(verify):
    """Return the process's TLS context for `verify` (a CA bundle path, or True: the default roots)."""
    with _CONTEXTS_LOCK:
        context = _CONTEXTS.get(verify)
        if context is None:
            context = ssl.create_default_context(cafile=verify if isinstance(verify, str) else None)
            _CONTEXTS[verify] = context
        return context
