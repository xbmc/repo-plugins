"""The same HTTP contract as :mod:`kofin.core.http`, over the standard library.

Importing ``requests`` costs about a second inside Kodi's Python, and the
plugin process pays it on every cold click that talks to the server — a
browse listing, the play resolve, a context action. Invoker reuse cannot be
relied on to keep a click warm: Kodi keeps one reusable invoker, the last
add-on's, so another add-on's reusable script between two clicks discards
ours.

So the plugin process asks over the standard library, and the service keeps
``requests``: a long-lived process pays the import once.

What this is not: a general HTTP client. It implements exactly the surface
:class:`kofin.core.api.Api` uses, with the same error taxonomy and the same
per-method retry budget. Anything subtler than that — redirects, streamed
bodies, content decoding — is either unused on kofin's API paths or
deliberately out of scope (see the note on ``Accept-Encoding`` below).
"""

from __future__ import annotations

import http.client
import json
import ssl
import threading
from typing import TYPE_CHECKING, Any
from urllib.parse import quote, urlencode, urlsplit

from kofin.core.http import (
    DEFAULT_TIMEOUT,
    METHOD_RETRIES,
    Http,
    StreamedResponse,
    run_ladder,
)
from kofin.core.log import Logger

if TYPE_CHECKING:  # the requests path is never imported here
    import requests

LOG = Logger(__name__)

# Errors that mean "the exchange failed", as opposed to "the server answered
# something we dislike". OSError covers socket timeouts, refusals and resets;
# HTTPException covers the protocol-level failures http.client raises.
_TRANSPORT_ERRORS = (http.client.HTTPException, OSError)


class Response:
    """The three things ``Api`` reads off a response.

    Deliberately not a requests.Response lookalike beyond that: pretending to
    be one would invite code to depend on the rest of that surface, which this
    module has no intention of providing.
    """

    def __init__(
        self,
        status_code: int,
        content: bytes,
        url: str,
        headers: dict[str, str] | None = None,
    ) -> None:
        self.status_code = status_code
        self.content = content
        self.url = url
        # Only ``Location`` is read (run_ladder's redirect refusal); kept as
        # a plain dict so the requests transport and this one look alike there.
        self.headers: dict[str, str] = dict(headers or {})

    def json(self) -> Any:
        return json.loads(self.content)


class StdlibHttp(Http):
    """A kept-alive connection to one origin, over ``http.client``.

    Subclasses :class:`Http` so it can be handed to ``Api`` unchanged.
    ``request`` and ``close`` are this transport's; ``session`` and ``stream``
    are the requests path and raise here, so a caller that reaches them fails
    at once instead of paying the import this class exists to avoid.

    One connection per thread, reused across that thread's calls: the play
    route makes three or four, and paying a TLS handshake for each would give
    back a good part of what the cheap import saves.

    Per *thread*, not per instance: callers share one transport across
    threads — the play route's media-segments prefetch runs beside the
    resolve, and the sidecar subtitle fetches run four at a time — and two
    threads writing requests onto one ``http.client`` connection interleave,
    so the reply one reads is not its own.
    """

    def __init__(self, user_agent: str = "") -> None:
        super().__init__(user_agent=user_agent)
        self._local = threading.local()
        # Every connection this transport has opened, so close() can release
        # the ones belonging to threads that have since finished.
        self._all: list[http.client.HTTPConnection] = []
        self._all_lock = threading.Lock()

    # -- lifecycle -------------------------------------------------------------

    def close(self) -> None:
        """Release every connection this transport opened, on any thread.

        End-of-life only. A failure mid-exchange drops just the calling
        thread's connection (:meth:`_drop`) — closing another thread's socket
        from under it is the very race this class exists to avoid.
        """
        with self._all_lock:
            connections, self._all = list(self._all), []
        for connection in connections:
            try:
                connection.close()
            except Exception as error:  # pragma: no cover - defensive
                LOG.debug("connection close failed: %s", error)
        self._local = threading.local()

    def session(self) -> requests.Session:
        raise RuntimeError("StdlibHttp has no requests session")

    def stream(
        self,
        url: str,
        headers: dict[str, str] | None = None,
        start: int = 0,
        timeout: tuple[float, float] | None = None,
        if_range: str = "",
    ) -> StreamedResponse:
        raise RuntimeError("StdlibHttp does not stream; downloads run on the service")

    def _drop(self) -> None:
        """Close and forget the calling thread's connection."""
        connection = getattr(self._local, "conn", None)
        if connection is None:
            return
        try:
            connection.close()
        except Exception as error:  # pragma: no cover - defensive
            LOG.debug("connection close failed: %s", error)
        with self._all_lock:
            if connection in self._all:
                self._all.remove(connection)
        self._local.conn = None
        self._local.origin = None

    def _connection(
        self, origin: tuple[str, str, int], connect_timeout: float, read_timeout: float
    ) -> tuple[http.client.HTTPConnection, bool]:
        """The pooled connection for ``origin``, and whether it is brand new.

        Freshness is what makes the stale-socket retry in :meth:`request` safe:
        a reused connection can be dead before the request is written, and then
        the server never saw it.
        """
        existing = getattr(self._local, "conn", None)
        if existing is not None and getattr(self._local, "origin", None) == origin:
            # The read budget is this call's, not the one the socket was
            # opened with.
            if existing.sock is not None:
                existing.sock.settimeout(read_timeout)
            return existing, False

        self._drop()
        scheme, host, port = origin
        connection: http.client.HTTPConnection
        if scheme == "https":
            connection = http.client.HTTPSConnection(
                host,
                port,
                timeout=connect_timeout,
                context=ssl.create_default_context(),
            )
        else:
            connection = http.client.HTTPConnection(host, port, timeout=connect_timeout)
        # Connect explicitly so the connect budget is the connect budget, and
        # the (longer) read budget applies only once a socket exists — the
        # split requests gives as a (connect, read) tuple.
        connection.connect()
        if connection.sock is not None:
            connection.sock.settimeout(read_timeout)
        self._local.conn = connection
        self._local.origin = origin
        with self._all_lock:
            self._all.append(connection)
        return connection, True

    # -- the request -----------------------------------------------------------

    def request(
        self,
        method: str,
        url: str,
        headers: dict[str, str] | None = None,
        params: dict[str, Any] | None = None,
        json_body: dict[str, Any] | None = None,
        timeout: tuple[float, float] | None = None,
        retries: int | None = None,
    ) -> Any:
        if retries is None:
            retries = METHOD_RETRIES.get(method.upper(), 0)
        connect_timeout, read_timeout = timeout or DEFAULT_TIMEOUT
        origin, target = _split(url, params)
        body, send_headers = _body(json_body, headers)
        if self._user_agent:
            send_headers.setdefault("User-Agent", self._user_agent)

        def attempt() -> Response:
            return self._exchange(
                origin,
                method,
                target,
                body,
                send_headers,
                connect_timeout,
                read_timeout,
                url,
            )

        # The abort check is None in the plugin process: nothing wires one in.
        result: Response = run_ladder(
            method, url, retries, attempt, _TRANSPORT_ERRORS, abort=self._abort
        )
        return result

    def _exchange(
        self,
        origin: tuple[str, str, int],
        method: str,
        target: str,
        body: bytes | None,
        headers: dict[str, str],
        connect_timeout: float,
        read_timeout: float,
        url: str,
    ) -> Response:
        """One request/response, with one free retry on a dead pooled socket.

        A connection taken from the pool can have been closed by the server
        while it sat idle; the failure then happens before the request reaches
        anyone, so replaying it is safe for *any* method and must not spend the
        caller's retry budget (which for POST is zero, deliberately). A timeout
        is a different thing — the server may have the request and be slow
        with it — and so is a failure while reading the body, where the server
        did act: both propagate.
        """
        connection, fresh = self._connection(origin, connect_timeout, read_timeout)
        try:
            connection.request(method, target, body=body, headers=headers)
            raw = connection.getresponse()
        except _TRANSPORT_ERRORS as error:
            self._drop()
            if fresh or isinstance(error, TimeoutError):
                raise
            LOG.debug("pooled connection was dead; reconnecting for %s", url)
            connection, _ = self._connection(origin, connect_timeout, read_timeout)
            connection.request(method, target, body=body, headers=headers)
            raw = connection.getresponse()

        try:
            payload = raw.read()
        except _TRANSPORT_ERRORS:
            self._drop()
            raise
        if raw.will_close:
            # The server is done with this socket; do not offer it to the next
            # call as though it were alive.
            self._drop()
        return Response(raw.status, payload, url, dict(raw.getheaders()))


def _split(url: str, params: dict[str, Any] | None) -> tuple[tuple[str, str, int], str]:
    """((scheme, host, port), request target) with ``params`` folded in."""
    parts = urlsplit(url)
    scheme = parts.scheme or "http"
    port = parts.port or (443 if scheme == "https" else 80)
    target = parts.path or "/"
    query = parts.query
    if params:
        # quote_via=quote to match what requests sends: a space becomes %20,
        # not '+'. Values are str()'d the same way, so booleans stay "True".
        extra = urlencode(
            {key: value for key, value in params.items() if value is not None},
            quote_via=quote,
        )
        query = "%s&%s" % (query, extra) if query else extra
    if query:
        target = "%s?%s" % (target, query)
    return (scheme, parts.hostname or "", port), target


def _body(
    json_body: dict[str, Any] | None, headers: dict[str, str] | None
) -> tuple[bytes | None, dict[str, str]]:
    send_headers = dict(headers or {})
    body: bytes | None = None
    if json_body is not None:
        body = json.dumps(json_body).encode("utf-8")
        send_headers["Content-Type"] = "application/json"
        send_headers["Content-Length"] = str(len(body))
    # Identity, and stated rather than left to chance: http.client does not
    # decode content, and Jellyfin does not compress these responses, so
    # nothing is being given up.
    send_headers.setdefault("Accept-Encoding", "identity")
    return body, send_headers
