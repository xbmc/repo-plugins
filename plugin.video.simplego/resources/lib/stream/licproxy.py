"""Local proxy between inputstream.adaptive and the provider: manifest + Widevine licence.

Licence (POST /license): forwarded to MediaKind with the session's headers, so
the refusal reason in the 403 body gets logged (ISA never logs it) and the
headers avoid ISA's URL-encoding.

Manifest (GET /manifest): fetched and served rewritten, each track's keys declared
(see manifest.ManifestRewriter); init segments (GET /init) with their real key ID.
"""

import re
import threading
import time
from urllib.parse import urlencode

from resources.lib.net import localserver
from resources.lib.net import transport
from resources.lib.stream import dash
from resources.lib.stream import manifest

# Seconds a request relayed by a sleeping proxy may take (see LicenceProxy.sleep): the stream reopens meanwhile.
RELAY_TIMEOUT = 30


class LicenceProxy:
    """Serve one stream's manifest, init segments and licence on localhost.

    `url` and `manifest` are the addresses to hand ISA. The manifest's keys and their changes are
    `rewriter`'s (a manifest.ManifestRewriter).

    :param http: the HTTP session for the provider and the CDN (a net.transport.Session)
    :param license_url: the MediaKind licence endpoint
    :param headers: the licence request's headers, or a callable returning them (asked for each licence)
    :param log: log(msg), where the proxy's messages go
    :param on_refused: on_refused(code) once the licence server refused a challenge
    :param manifest_url: the provider's manifest, served rewritten at /manifest
    :param fallback_url: a manifest to play instead if manifest_url is refused before the first one is served:
        never switched to later, which would change the stream under the player
    :param stop_when: asked at every manifest refresh: True ends the stream (e.g. the parental lock)
    :param debug: debug(msg), where timings go (else log)
    :param rewriter: the manifest.ManifestRewriter of this stream, its proxy_base() this proxy's `base`;
        else one with its defaults
    """

    def __init__(
        self,
        http,
        license_url,
        headers,
        log,
        on_refused=None,
        manifest_url=None,
        fallback_url=None,
        stop_when=None,
        debug=None,
        rewriter=None,
    ):
        self._http = http
        self._url = license_url
        self._headers = headers
        self._log = log
        self._debug = debug or log
        self._on_refused = on_refused
        # Once refused, ISA keeps retrying every track and the manifest: answering all
        # with the refusal at once ends playback instead of hanging.
        self._refused = None
        self._manifest_url = manifest_url
        self._fallback_url = fallback_url
        self._fallback_lock = threading.Lock()
        self._manifest_served = False
        self._stop_when = stop_when
        self._static = None  # a static manifest as served, see _manifest
        self._rewrite_lock = threading.Lock()
        # After sleep: the stream to relay to, reopened at the first request.
        self._reopen = None
        self._target = None
        self._relay_http = None
        self._relay_lock = threading.Lock()
        self._server = None
        self.base = self.url = self.manifest = None  # see start
        self.rewriter = rewriter or manifest.ManifestRewriter(http, lambda: self.base, log, debug=debug)

    def start(self):
        """Serve on a free local port: `url` and `manifest` are then the addresses to hand ISA; return the proxy."""
        self._server = localserver.start(self.respond)
        self.base = "http://127.0.0.1:%d" % localserver.port(self._server)
        self.url = self.base + "/license"
        self.manifest = self.base + "/manifest"
        return self

    def serves(self, url):
        """Return whether a URL is one of this proxy's addresses (what Kodi plays, say)."""
        return self.base is not None and url.startswith(self.base + "/")

    def respond(self, request):
        """Answer ISA: POST /license, GET /manifest and /init; all relayed once asleep (see sleep)."""
        if self._reopen:
            return self._relay(request.method, request.path, request.query, request.body)
        if request.method == "POST":
            return self._forward(request.body)
        if request.path == "/init":
            return self._init(request.query.get("u", ""), request.query.get("k"))
        if request.path == "/manifest" and self._manifest_url:
            return self._manifest()
        return localserver.Response(404, b"", "text/plain")

    # ------------------------------------------------------------- licence

    def _forward(self, body):
        if self._refused:
            return self._refused
        try:
            headers = self._headers() if callable(self._headers) else self._headers
            r = self._http.post(self._url, data=body, headers=headers, timeout=manifest.HTTP_TIMEOUT)
        except Exception as e:  # noqa: BLE001 - the caller's headers (a token renewal) may fail any way
            self._log("licence request failed: %s" % e)
            return localserver.Response(502, b"", "text/plain")
        if r.status_code == 200:
            self._debug(
                "licence OK: challenge %d B -> licence %d B, keys: %s"
                % (len(body), len(r.content), "; ".join(dash.licence_keys(r.content)) or "?")
            )
        else:
            # MediaKind answers errors as <error><code>..</code><message>..</message></error>.
            m = re.search(rb"<code>(\d+)</code>.*?<message>([^<]*)</message>", r.content, re.S)
            reason = "%s %s" % (m.group(1).decode(), m.group(2).decode("utf-8", "replace")) if m else r.text[:200]
            self._log(
                "licence refused: HTTP %s, %s (challenge %d B, starts %s)" % (r.status_code, reason, len(body), body[:8].hex())
            )
            self._refused = _passed_on(r)
            if self._on_refused:
                # Not in this request's thread: a dialog there would hold up ISA's answer.
                threading.Thread(target=self._on_refused, args=(m.group(1).decode() if m else "",), daemon=True).start()
        return _passed_on(r)

    # ------------------------------------------------------------ manifest

    def _manifest(self):
        if self._refused:
            return localserver.Response(410, b"", "text/plain")
        if self._stop_when and self._stop_when():
            self._log("stream stopped: the programme now on is locked")
            return localserver.Response(410, b"", "text/plain")
        if self._static is not None:
            # A static manifest never changes: the one made by prefetch is served at once.
            return localserver.Response(200, self._static, "application/dash+xml")
        started = time.time()
        try:
            r = self._fetch_manifest()
            fetched = time.time()
            # One reader of the keys at a time: ISA's first request waits for a prefetch.
            with self._rewrite_lock:
                locked = time.time()
                first = not self.rewriter.has_keys()
                if self._static is not None:  # made meanwhile (the prefetch)
                    return localserver.Response(200, self._static, "application/dash+xml")
                rewritten = self.rewriter.rewrite(r.text, r.url)
                mpd = rewritten.mpd.encode("utf-8")
                if dash.is_static(r.text):
                    self._static = mpd
            if first:
                self._debug("first manifest: fetched in %.2fs, keys read in %.2fs" % (fetched - started, time.time() - fetched))
            else:
                # A live manifest is rewritten at every refresh (every few seconds): its cost, to measure.
                # The wait for the rewrite lock apart: a prefetch still reading the keys is no rewrite's cost.
                self._debug(
                    "manifest refresh: fetched in %.0f ms, waited %.0f ms, rewritten in %.0f ms (%s)"
                    % (
                        (fetched - started) * 1000,
                        (locked - fetched) * 1000,
                        (time.time() - locked) * 1000,
                        rewritten.steps,
                    )
                )
            self._manifest_served = True
            return localserver.Response(200, mpd, "application/dash+xml")
        except Exception as e:  # noqa: BLE001 - ISA gets an answer whatever failed, not a dropped connection
            self._log("manifest proxy failed: %s" % e)
            return localserver.Response(502, b"", "text/plain")

    def _fetch_manifest(self):
        """Return the provider's manifest: the fallback one for good if the first is refused before any is served."""
        r = self._http.get(self._manifest_url, timeout=manifest.HTTP_TIMEOUT)
        if self._fallback_url and not self._manifest_served and r.status_code >= 400:
            # The prefetch and ISA's first request may both get here: one switches, both fetch the fallback.
            with self._fallback_lock:
                if self._fallback_url:
                    self._log("manifest refused (HTTP %d): playing the fallback" % r.status_code)
                    self._manifest_url, self._fallback_url = self._fallback_url, None
            r = self._http.get(self._manifest_url, timeout=manifest.HTTP_TIMEOUT)
        r.raise_for_status()
        return r

    def prefetch(self):
        """Read the keys now, so the manifest is ready when ISA asks for it a moment later."""
        threading.Thread(target=self._manifest, daemon=True).start()

    def _init(self, url, kid=None):
        """Serve an init segment with its tenc key ID set to the one its fragments really use.

        :param kid: its part's (see manifest.ManifestRewriter._key_changes); else the one first read for it
        """
        try:
            r = self._http.get(url, timeout=manifest.HTTP_TIMEOUT)
            r.raise_for_status()
        except transport.Error as e:
            self._log("init segment proxy failed: %s" % e)
            return localserver.Response(502, b"", "text/plain")
        return localserver.Response(200, dash.with_tenc_kid(r.content, kid or self.rewriter.init_kid(url)), "video/mp4")

    def sleep(self, reopen):
        """Keep the address without a stream; any request then reopens the stream and is relayed to it.

        Kodi replays an item by its old address when it gets its display back
        (HDMI input switched away and back), long after the session closed.

        :param reopen: reopen() -> the new stream's proxy's `base`, or None
        """
        self._reopen = reopen
        self._target = None
        self._http.close()
        self._relay_http = transport.Session()

    def _relay(self, method, path, query, body):
        # Twice at most: the stream reopened before may be gone too by now.
        for _ in range(2):
            with self._relay_lock:
                if self._target is None:
                    self._target = self._reopen()
                    self._log("stream reopened for its old address" if self._target else "reopening the stream failed")
                target = self._target
            if not target:
                break
            try:
                address = target + path + ("?" + urlencode(query) if query else "")
                r = self._relay_http.request(method, address, data=body or None, timeout=RELAY_TIMEOUT)
            except transport.Error:
                with self._relay_lock:
                    if self._target == target:
                        self._target = None
                continue
            return _passed_on(r)
        return localserver.Response(503, b"", "text/plain")

    def stop(self):
        """Stop serving and close the HTTP connections."""
        localserver.stop(self._server)
        self._http.close()
        if self._relay_http:
            self._relay_http.close()


def _passed_on(r):
    """Return the provider's answer as it came, for ISA."""
    return localserver.Response(r.status_code, r.content, r.headers.get("Content-Type", "application/octet-stream"))
