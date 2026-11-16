"""HTTP transport: one persistent session per process, retries, error taxonomy.

Pure python (no Kodi imports) so the whole network stack is unit-testable.

``requests`` is imported inside the methods that use it, not at module load,
so importing this module stays cheap: routes that never talk to the server —
a node menu, a settings button — import it through the Api plumbing all the
same.
"""

from __future__ import annotations

import random
import time
from typing import TYPE_CHECKING, Any, Callable
from collections.abc import Iterator

from kofin.core.log import Logger

if TYPE_CHECKING:  # runtime import is deferred; see module docstring
    import requests

LOG = Logger(__name__)

DEFAULT_TIMEOUT = (6.0, 30.0)
RETRIES = 3
BACKOFF_BASE_SECONDS = 0.5

# One read per chunk of a streamed body. Large enough that the per-chunk
# abort check costs nothing against a media download, small enough that a
# stop request is heard within a fraction of a second on any real link.
STREAM_CHUNK_BYTES = 262_144

# Default retry budget per method, applied when the caller passes none. GETs
# replay safely. A DELETE states an absolute fact and gets one replay. POST
# gets none: the transport cannot tell "never arrived" from "response lost
# after the server acted", and a replayed POST double-applies. A caller whose
# POST is an absolute-state write may opt back in with an explicit
# ``retries``.
METHOD_RETRIES = {"GET": RETRIES, "HEAD": RETRIES, "DELETE": 1}

# Answers that mean "not now" rather than "no": a reverse proxy holding the
# door while Jellyfin restarts (502/504), a server still warming up (503), a
# rate limiter (429). They ride the same ladder as a transport error, for
# the methods that carry a budget — POST still gets none. Not 500: Jellyfin
# answers deterministic 500s for broken items, and replaying those would only
# slow a walk by three backoffs per request.
RETRY_STATUSES = (429, 502, 503, 504)


class JellyfinError(Exception):
    """Base for all transport/API failures."""


class ServerUnreachable(JellyfinError):
    pass


class Unauthorized(JellyfinError):
    pass


class HttpError(JellyfinError):
    def __init__(self, status: int, message: str) -> None:
        super().__init__(message)
        self.status = status


def run_ladder(
    method: str,
    url: str,
    retries: int,
    attempt: Callable[[], Any],
    transport_errors: tuple[type[BaseException], ...],
    abort: Callable[[], bool] | None = None,
) -> Any:
    """The one retry ladder both transports ride: backoff, the abort check
    between attempts, the per-request log line, and the status taxonomy.

    Abort is checked between attempts because Kodi will not finalise a
    script while a thread it started is alive.
    """
    last_error: BaseException | None = None
    for attempt_index in range(retries + 1):
        if attempt_index:
            if abort is not None and abort():
                raise ServerUnreachable(
                    "%s %s: abandoned while stopping (%s)" % (method, url, last_error)
                )
            delay = BACKOFF_BASE_SECONDS * (2 ** (attempt_index - 1))
            time.sleep(delay + random.uniform(0, delay / 2))
            # sleep() cannot see the flag; check again.
            if abort is not None and abort():
                raise ServerUnreachable(
                    "%s %s: abandoned while stopping (%s)" % (method, url, last_error)
                )
        try:
            response = attempt()
        except transport_errors as error:
            LOG.debug(
                "attempt %d/%d failed for %s: %s",
                attempt_index + 1,
                retries + 1,
                url,
                error,
            )
            last_error = error
            continue

        # Every request, not just the failures, so request counts can be read
        # from the log. Debug level, and masked like every other line; kofin's
        # auth rides in headers, so the query string carries no secret.
        sent = getattr(response, "request", None)
        LOG.debug(
            "http %s %s -> %d",
            method,
            getattr(sent, "url", None) or getattr(response, "url", None) or url,
            response.status_code,
        )

        if response.status_code in (401, 403):
            raise Unauthorized("%s %s -> %d" % (method, url, response.status_code))
        if response.status_code in RETRY_STATUSES and attempt_index < retries:
            LOG.debug(
                "attempt %d/%d answered %d for %s; replaying",
                attempt_index + 1,
                retries + 1,
                response.status_code,
                url,
            )
            last_error = HttpError(
                response.status_code,
                "%s %s -> %d" % (method, url, response.status_code),
            )
            continue
        if 300 <= response.status_code < 400:
            # A redirect is refused on both transports: the Location is the
            # address the user should have entered.
            location = (getattr(response, "headers", None) or {}).get("Location")
            raise HttpError(
                response.status_code,
                "%s %s -> %d (redirected to %s; use that address)"
                % (method, url, response.status_code, location or "?"),
            )
        if response.status_code >= 400:
            raise HttpError(
                response.status_code,
                "%s %s -> %d" % (method, url, response.status_code),
            )
        return response

    raise ServerUnreachable("%s %s: %s" % (method, url, last_error))


def plugin_transport(user_agent: str = "") -> Http:
    """The transport for the *plugin* process.

    Standard library rather than ``requests``, because the requests import is
    paid on every cold click (kofin/core/stdhttp.py explains the split).

    Imported here rather than at module load so this module stays free of
    both trees until something actually asks for one.
    """
    from kofin.core.stdhttp import StdlibHttp

    return StdlibHttp(user_agent)


class StreamedResponse:
    """A streaming GET in flight: headers now, the body drained via chunks().

    Thin on purpose — retries, resume bookkeeping and file writes are the
    download manager's policy, not the transport's. What lives here is what
    every streaming caller needs identically: the abort check between chunks
    (the read timeout bounds a dead socket; this bounds a *live* one, which a
    multi-GB body otherwise keeps reading long past a stop request), the
    mid-body error taxonomy, and close() so an abandoned stream releases its
    pooled connection.
    """

    def __init__(
        self,
        response: requests.Response,
        abort: Callable[[], bool] | None,
        already_complete: bool = False,
    ) -> None:
        self._response = response
        self._abort = abort
        # The server answered 416 to a resume offset: everything was already
        # fetched.
        self.already_complete = already_complete

    @property
    def status(self) -> int:
        return int(self._response.status_code)

    def header(self, name: str) -> str:
        """A response header, '' when absent. Case-insensitive by hand so a
        test fake with a plain dict behaves like requests' own mapping."""
        for key, value in self._response.headers.items():
            if key.lower() == name.lower():
                return str(value)
        return ""

    def chunks(self) -> Iterator[bytes]:
        import requests

        if self.already_complete:
            return
        try:
            for chunk in self._response.iter_content(STREAM_CHUNK_BYTES):
                if self._abort is not None and self._abort():
                    raise ServerUnreachable("stream abandoned while stopping")
                if chunk:
                    yield chunk
        except requests.RequestException as error:
            # A body that dies mid-read is a connection fact, whatever
            # requests dresses it as (ChunkedEncodingError and friends).
            raise ServerUnreachable("stream interrupted: %s" % error) from error

    def close(self) -> None:
        try:
            self._response.close()
        except Exception as error:  # pragma: no cover - defensive
            LOG.debug("stream close failed: %s", error)


def _default_trust_adapter() -> requests.adapters.HTTPAdapter:
    """An https adapter whose TLS context is the standard library's default.

    requests on its own verifies against certifi's bundle. The default context
    trusts what OpenSSL does: the file named by ``SSL_CERT_FILE``, which Kodi
    sets from advancedsettings' ``catrustfile`` (and to its own bundle on
    Android, macOS and Windows), or else the system store. The plugin's
    transport, the websockets and Kodi's curl trust the same, so a CA the user
    gave Kodi is trusted here too. An ``HTTPS_PROXY`` connection uses a second
    pool, built by ``proxy_manager_for``, so that pool gets the same context.
    """
    import ssl

    from requests.adapters import HTTPAdapter

    class DefaultTrust(HTTPAdapter):
        def init_poolmanager(self, *args: Any, **kwargs: Any) -> None:
            kwargs["ssl_context"] = ssl.create_default_context()
            super().init_poolmanager(*args, **kwargs)

        def proxy_manager_for(self, proxy: str, **kwargs: Any) -> Any:
            kwargs["ssl_context"] = ssl.create_default_context()
            return super().proxy_manager_for(proxy, **kwargs)

    return DefaultTrust()


class Http:
    """A lazily created, kept-alive requests session."""

    def __init__(
        self,
        abort: Callable[[], bool] | None = None,
        user_agent: str = "",
    ) -> None:
        # Asked between retries: True means give up rather than replay. Passed
        # in rather than read here so this module keeps its no-Kodi-imports
        # property; the service wires its stop flag in (service/main.py).
        self._abort = abort
        # settings.user_agent(), passed in for the same reason. Empty leaves
        # the library's own.
        self._user_agent = user_agent
        self._session: requests.Session | None = None

    def session(self) -> requests.Session:
        import requests

        if self._session is None:
            session = requests.Session()
            session.mount("https://", _default_trust_adapter())
            if self._user_agent:
                session.headers["User-Agent"] = self._user_agent
            self._session = session
            LOG.debug("http session opened")
        return self._session

    def close(self) -> None:
        if self._session is not None:
            try:
                self._session.close()
            except Exception as error:  # pragma: no cover - defensive
                LOG.warning("session close failed: %s", error)
            self._session = None

    def request(
        self,
        method: str,
        url: str,
        headers: dict[str, str] | None = None,
        params: dict[str, Any] | None = None,
        json_body: dict[str, Any] | None = None,
        timeout: tuple[float, float] | None = None,
        retries: int | None = None,
    ) -> requests.Response:
        import requests

        if retries is None:
            retries = METHOD_RETRIES.get(method.upper(), 0)

        def attempt() -> requests.Response:
            # Redirects reach run_ladder's 3xx refusal like they do on the
            # stdlib transport, instead of being followed here alone.
            return self.session().request(
                method,
                url,
                headers=headers,
                params=params,
                json=json_body,
                timeout=timeout or DEFAULT_TIMEOUT,
                allow_redirects=False,
            )

        response: requests.Response = run_ladder(
            method,
            url,
            retries,
            attempt,
            # The last two are a body cut short mid-read and a body that will
            # not decompress: the transport failing, as on the stdlib side.
            (
                requests.ConnectionError,
                requests.Timeout,
                requests.exceptions.ChunkedEncodingError,
                requests.exceptions.ContentDecodingError,
            ),
            abort=self._abort,
        )
        return response

    def stream(
        self,
        url: str,
        headers: dict[str, str] | None = None,
        start: int = 0,
        timeout: tuple[float, float] | None = None,
        if_range: str = "",
    ) -> StreamedResponse:
        """One streaming GET — deliberately no retry ladder.

        The download manager owns retry and resume policy: a replayed
        multi-GB body is never the transport's call to make, and the
        manager's resume watermark decides where the next attempt starts.
        ``start`` resumes with a Range header; a 416 answer comes back as
        ``already_complete`` rather than an error. ``if_range`` rides with it
        as If-Range: a server whose file no longer matches that validator
        ignores the Range and answers with the whole file (200).
        """
        import requests

        sent = dict(headers or {})
        if start:
            sent["Range"] = "bytes=%d-" % start
            if if_range:
                sent["If-Range"] = if_range
        try:
            response = self.session().request(
                "GET",
                url,
                headers=sent,
                stream=True,
                timeout=timeout or DEFAULT_TIMEOUT,
            )
        except (requests.ConnectionError, requests.Timeout) as error:
            raise ServerUnreachable("GET %s: %s" % (url, error)) from error
        LOG.debug("http GET %s -> %d (stream)", url, response.status_code)
        if response.status_code == 416:
            response.close()
            return StreamedResponse(response, self._abort, already_complete=True)
        if response.status_code in (401, 403):
            response.close()
            raise Unauthorized("GET %s -> %d" % (url, response.status_code))
        if response.status_code >= 400:
            response.close()
            raise HttpError(
                response.status_code, "GET %s -> %d" % (url, response.status_code)
            )
        return StreamedResponse(response, self._abort)
