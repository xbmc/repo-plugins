"""Jellyfin websocket client: auth-header connect, keepalive, reconnect.

Transport only — received messages are handed to a callback; what they mean
is the service's business.
"""

import json
import threading
import time
from http import HTTPStatus
from typing import Any, Callable, Optional

import xbmc
import websocket

from kofin.core.log import Logger

LOG = Logger(__name__)

KEEPALIVE_SECONDS = 30
RECONNECT_SECONDS = 10
# Between attempts once the server has refused the session: the token is
# what fails, and only a new login changes it.
REJECTED_RETRY_SECONDS = 300
# The half-open verdict: a healthy socket never goes this long without an
# inbound frame, because the server echoes every KeepAlive _KeepAlive sends
# (and pushes ForceKeepAlive on its own). Two missed echoes plus grace.
STALE_SECONDS = 75
# How often the keepalive thread wakes to check liveness between sends.
LIVENESS_TICK = 15
IGNORED_MESSAGES = frozenset({"RefreshProgress", "KeepAlive", "ForceKeepAlive"})

EventCallback = Callable[[str, dict[str, Any]], None]
ConnectedCallback = Callable[[], None]


def socket_url(server_address: str) -> str:
    if server_address.startswith("https://"):
        return server_address.replace("https://", "wss://", 1) + "/socket"
    return server_address.replace("http://", "ws://", 1) + "/socket"


def handshake_header(authorization: str, user_agent: str) -> dict[str, str]:
    """The headers of a websocket handshake. websocket-client sends no
    User-Agent of its own; ``user_agent`` is settings.user_agent()."""
    header = {"Authorization": authorization}
    if user_agent:
        header["User-Agent"] = user_agent
    return header


class NoRedirectSocket(websocket.WebSocket):
    """A websocket whose handshake follows no redirect.

    websocket-client follows up to three redirects of a handshake by default
    and sends every header to each new address, the Authorization header
    included. With ``redirect_limit=0`` it follows none, but reports the
    redirect as a connected socket.
    """

    def connect(self, url: str, **options: Any) -> None:
        super().connect(url, **dict(options, redirect_limit=0))
        status = self.getstatus()
        if status != HTTPStatus.SWITCHING_PROTOCOLS:
            location = (self.getheaders() or {}).get("location")
            self.shutdown()
            raise websocket.WebSocketException(
                "handshake answered %s (to %s); a redirect is not followed"
                % (status, location)
            )


class NoRedirectApp(websocket.WebSocketApp):
    """A WebSocketApp whose sockets are NoRedirectSockets.

    run_forever builds a plain websocket.WebSocket, assigns it to ``sock``
    and connects it, with no redirect option to pass; the assignment makes
    it a NoRedirectSocket first, which holds no state of its own.
    """

    _socket: Optional[websocket.WebSocket] = None

    @property
    def sock(self) -> Optional[websocket.WebSocket]:
        return self._socket

    @sock.setter
    def sock(self, value: Optional[websocket.WebSocket]) -> None:
        if value is not None:
            value.__class__ = NoRedirectSocket
        self._socket = value


class WSClient(threading.Thread):
    def __init__(
        self,
        server_address: str,
        auth_header: str,
        on_event: EventCallback,
        on_connected: ConnectedCallback,
        on_disconnected: Optional[ConnectedCallback] = None,
        user_agent: str = "",
        on_rejected: Optional[ConnectedCallback] = None,
    ) -> None:
        super().__init__(name="kofin-ws")
        self._on_rejected = on_rejected
        # The server refused the handshake for the session (401, 403): a
        # password change, a disabled user, the device removed. Set until a
        # handshake succeeds.
        self.rejected = False
        self._url = socket_url(server_address)
        self._user_agent = user_agent
        self._header = auth_header
        self._on_event = on_event
        self._on_connected = on_connected
        self._on_disconnected = on_disconnected
        self._stop = False
        # Whether the socket is currently up: run_forever returns on every
        # failure and the run loop retries, so the flag is what turns that
        # stream into one edge per actual transition.
        self._connected = False
        # Monotonic time of the last inbound frame — the liveness signal
        # half_open() polices (see its docstring).
        self._last_inbound = 0.0
        self._app: Optional[websocket.WebSocketApp] = None
        self._keepalive: Optional[_KeepAlive] = None

    def run(self) -> None:
        LOG.debug("websocket url: %s", self._url)
        # Socket-level timeout for the connect phase: without one, a
        # black-holed host blocks create_connection for the OS TCP timeout
        # (~2 min), through which stop()'s bounded join fails and the thread
        # leaks past a service restart. Module-global to websocket-client,
        # which is fine — kofin owns the only websocket in this process.
        websocket.setdefaulttimeout(10)
        while not self._stop:
            # A fresh app per attempt, because WebSocketApp.teardown() is
            # one-shot per instance: ``has_done_teardown`` is set in
            # __init__ and never reset by run_forever (websocket-client
            # 1.6.4, _app.py:236). So the first drop tears down and clears
            # ``sock``, but a later *failed connect* — setSock() assigns
            # ``sock`` before connect() raises — reaches an already-done
            # teardown that returns immediately and leaves the dead socket
            # in place, and the next run_forever raises "socket is already
            # opened".
            self._app = self._build_app()
            if self._stop:
                break
            # No ping_timeout and no reconnect=. ping_timeout tears healthy
            # connections down: the server's own 2-minute keepalive ping
            # corrupts websocket-client's pong bookkeeping. reconnect='s
            # internal retry invokes neither on_error nor on_close. This loop
            # owns reconnection instead, and half-open detection is
            # app-level: half_open() recycles the socket when the server's
            # KeepAlive echoes stop arriving.
            try:
                self._app.run_forever(ping_interval=10)
            except Exception:
                # One attempt's worth of failure, never the thread's life.
                # Reconnection is this loop's job and it cannot do it from
                # inside a traceback.
                LOG.exception("websocket attempt failed")
            # A Monitor for this wait only. Kodi queues a callback per
            # announcement for every Monitor object alive, in one queue for
            # the whole process, and only the thread that made the object can
            # take its callbacks off it -- which it does inside waitForAbort
            # and nowhere else. This thread sits in run_forever for as long as
            # the socket is up, and every Python thread in Kodi walks that
            # queue on each of its own waits
            # (RetardedAsyncCallbackHandler::makePendingCalls).
            wait = REJECTED_RETRY_SECONDS if self.rejected else RECONNECT_SECONDS
            if self._stop or xbmc.Monitor().waitForAbort(wait):
                break
        LOG.debug("websocket thread exit")

    def _build_app(self) -> "websocket.WebSocketApp":
        return NoRedirectApp(
            self._url,
            header=handshake_header(self._header, self._user_agent),
            on_open=self._handle_open,
            on_message=self._handle_message,
            on_error=self._handle_error,
            on_close=self._handle_close,
        )

    def stop(self) -> None:
        self._stop = True
        if self._keepalive is not None:
            self._keepalive.stop()
            self._keepalive = None
        app = self._app
        # The raw-socket handle is taken before close(): WebSocketApp.close()
        # drops its reference on the way through, and the escalation below
        # needs something left to sever.
        sock = getattr(app, "sock", None)
        if app is not None:
            try:
                app.close()
            except Exception as error:  # pragma: no cover - defensive
                LOG.debug("websocket close failed: %s", error)
        if not self.is_alive():
            return
        self.join(timeout=5)
        if not self.is_alive():
            return
        # The graceful close did not unblock the receive loop. That is what a
        # close handshake that raised looks like: the descriptor stays open,
        # recv() keeps delivering, and the thread outlives every deadline —
        # which blocks Kodi's script finalisation outright ("waiting on
        # thread"), because Kodi will not finalise a script while a thread it
        # started is alive. WebSocket.shutdown() closes the raw socket with no
        # handshake, which fails the pending recv immediately.
        try:
            if sock is not None:
                sock.shutdown()
        except Exception as error:  # pragma: no cover - defensive
            LOG.debug("websocket shutdown failed: %s", error)
        self.join(timeout=5)
        if self.is_alive():  # pragma: no cover - watchdog logging only
            LOG.warning("websocket thread did not stop within deadline")

    def _handle_open(self, app: "websocket.WebSocketApp") -> None:
        self.rejected = False
        if self._stop:
            # A connect completing while stop() tears the client down must
            # not restart the machinery: the keepalive it would spawn has no
            # stop() left to run it down, and the connected callback would
            # fire into a service that is mid-teardown.
            return
        LOG.debug("websocket connected")
        self._connected = True
        self._last_inbound = time.monotonic()
        if self._keepalive is not None:
            self._keepalive.stop()
        self._keepalive = _KeepAlive(app, self)
        self._keepalive.start()
        try:
            self._on_connected()
        except Exception:
            LOG.exception("on_connected callback failed")

    def _handle_close(
        self,
        app: "websocket.WebSocketApp",
        status_code: Optional[int] = None,
        message: Optional[str] = None,
    ) -> None:
        """One callback per real drop.

        Reported only when a socket that was actually open goes down, so a
        server that stays unreachable — where run_forever keeps failing to
        connect — does not fire this on every retry. A deliberate stop() is
        not a drop either.
        """
        was_connected = self._connected
        self._connected = False

        if not was_connected or self._stop:
            return

        LOG.debug("websocket disconnected (%s %s)", status_code, message)

        if self._on_disconnected is None:
            return

        try:
            self._on_disconnected()
        except Exception:
            LOG.exception("on_disconnected callback failed")

    def half_open(self) -> bool:
        """True — after closing the socket — when the connection has gone
        silent for STALE_SECONDS.

        The liveness contract: the server echoes every application-level
        KeepAlive sent at it, so a healthy socket receives a frame at least
        every KEEPALIVE_SECONDS. A half-open socket (NAT drop, sleeping AP)
        receives nothing while sends keep succeeding into the void — the
        one failure shape nothing else detects. Closing makes run_forever
        return; the run loop reconnects, and on_open fires the catch-up.
        """
        if not self._connected:
            return False
        if time.monotonic() - self._last_inbound <= STALE_SECONDS:
            return False
        LOG.debug("websocket half-open: no traffic for %ss; recycling", STALE_SECONDS)
        try:
            if self._app is not None:
                self._app.close()
        except Exception as error:  # pragma: no cover - defensive
            LOG.debug("half-open close failed: %s", error)
        return True

    def _handle_message(self, app: "websocket.WebSocketApp", raw: str) -> None:
        if self._stop:
            # A stopped client hands its owner nothing: the service is
            # mid-teardown and the objects the callback reaches — the
            # Library, the kofin database — may already be gone.
            return
        # Every inbound frame is liveness, including the KeepAlive echoes the
        # event filter below discards and frames that fail to parse.
        self._last_inbound = time.monotonic()
        try:
            message = json.loads(raw)
        except ValueError:
            LOG.warning("undecodable websocket message")
            return
        message_type = message.get("MessageType", "")
        if message_type in IGNORED_MESSAGES:
            return
        data = message.get("Data") or {}
        if not isinstance(data, dict):
            data = {"Value": data}
        try:
            self._on_event(message_type, data)
        except Exception:
            LOG.exception("event handler failed for %s", message_type)

    def _handle_error(self, app: "websocket.WebSocketApp", error: Exception) -> None:
        LOG.debug("websocket error: %s", error)
        status = getattr(error, "status_code", None)
        if (
            isinstance(error, websocket.WebSocketBadStatusException)
            and status in (HTTPStatus.UNAUTHORIZED, HTTPStatus.FORBIDDEN)
            and not self.rejected
        ):
            self.rejected = True
            LOG.warning(
                "the server refused the session (%s); waiting for a new login", status
            )
            if self._on_rejected is not None:
                try:
                    self._on_rejected()
                except Exception:
                    LOG.exception("rejected-session callback failed")


class _KeepAlive(threading.Thread):
    """Sends the Jellyfin application-level KeepAlive and polices its echo.

    One thread for both halves because they are one contract: every KeepAlive
    sent is echoed by the server, so the sender is exactly the thread that
    knows silence is abnormal (WSClient.half_open).
    """

    def __init__(self, app: "websocket.WebSocketApp", client: "WSClient") -> None:
        super().__init__(name="kofin-ws-keepalive")
        self._app = app
        self._client = client
        self._halt = threading.Event()

    def stop(self) -> None:
        self._halt.set()
        self.join(timeout=5)

    def run(self) -> None:
        since_send = 0
        while not self._halt.wait(LIVENESS_TICK):
            if self._client.half_open():
                return
            since_send += LIVENESS_TICK
            if since_send < KEEPALIVE_SECONDS:
                continue
            since_send = 0
            try:
                self._app.send(
                    json.dumps({"MessageType": "KeepAlive", "Data": KEEPALIVE_SECONDS})
                )
            except Exception as error:
                LOG.debug("keepalive send failed: %s", error)
                return
