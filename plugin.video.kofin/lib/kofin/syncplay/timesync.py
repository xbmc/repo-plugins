"""NTP-style clock sync against the server.

The websocket TimeSync exchange runs on the **dedicated socket the server's
Hello advertises** (SYNCPLAY.md §3.1, the plugin binding), not on the main
``/socket``: a plugin cannot answer TimeSync there, and on unfixed servers an
unknown message type kills the shared socket."""

import json
import threading
from collections import deque
from typing import TYPE_CHECKING, Optional

import websocket

from kofin.core.log import Logger
from kofin.core.ws import NoRedirectSocket, handshake_header
from kofin.syncplay import utils

if TYPE_CHECKING:
    from kofin.syncplay.manager import SyncPlayManager


LOG = Logger(__name__)


class TimeSync(threading.Thread):
    """NTP-style clock sync against the server (SYNCPLAY.md §3).

    Keeps a sliding window of measurements and trusts the one with the
    smallest round trip. Prefers the dedicated websocket TimeSync exchange
    when the server advertises one (it measures a channel with no HTTP
    overhead and stamps t3 at receipt), falling back to GET /GetUtcTime.

    offset_ms is (server clock - local clock); server_now_ms() converts
    the local clock to the server's.
    """

    def __init__(self, manager: "SyncPlayManager", user_agent: str = "") -> None:
        threading.Thread.__init__(self, name="kofin-syncplay-timesync")
        self.daemon = True
        self.manager = manager
        self._user_agent = user_agent
        self.samples = deque(maxlen=utils.TIMESYNC_WINDOW)  # type: deque
        self.offset_ms = 0.0
        self.rtt_ms = None
        self.ping_ms = None
        self._greedy_remaining = utils.TIMESYNC_GREEDY_COUNT
        self._stop_event = threading.Event()
        self._kick_event = threading.Event()
        self._lock = threading.Lock()
        # The dedicated time-sync socket, when advertised.
        self._ws: Optional[websocket.WebSocket] = None

    def run(self) -> None:
        LOG.debug("--->[ syncplay timesync ]")

        while not self._stop_event.is_set():
            try:
                self._measure()
            except Exception as error:  # never kill the loop
                LOG.warning("Time sync measurement failed: %s", error)

            if self._greedy_remaining > 0:
                self._greedy_remaining -= 1
                interval = utils.TIMESYNC_GREEDY_INTERVAL
            else:
                interval = utils.TIMESYNC_INTERVAL

            self._kick_event.wait(interval)
            self._kick_event.clear()

        LOG.debug("---<[ syncplay timesync ]")

    def stop(self) -> None:
        self._stop_event.set()
        self._kick_event.set()
        self._close_ws()

    def force_update(self, reset: bool = False) -> None:
        """Re-measure greedily, e.g. on group join or wake from sleep."""
        if reset:
            with self._lock:
                self.samples.clear()

        self._greedy_remaining = utils.TIMESYNC_GREEDY_COUNT
        self._kick_event.set()

    # --- measurement ---------------------------------------------------

    def _measure(self) -> None:
        if self.manager.can_ws_timesync() and self._measure_ws():
            return

        self._measure_http()

    def _measure_ws(self) -> bool:
        """One exchange over the dedicated socket; returns False to fall back."""
        sock = self._ws_socket()

        if sock is None:
            return False

        t0 = int(utils.local_ms())

        try:
            sock.send(json.dumps({"MessageType": "TimeSync", "Data": t0}))
            raw = sock.recv()
            t3 = utils.local_ms()
        except Exception as error:
            LOG.debug("WebSocket TimeSync exchange failed: %s", error)
            self._close_ws()
            return False

        try:
            data = (json.loads(raw) or {}).get("Data") or {}
        except ValueError:
            LOG.debug("Unparseable TimeSync response: %r", raw)
            return False

        if data.get("T0") != t0:
            LOG.debug("Unmatched TimeSync response: %s", data)
            return False

        t1, t2 = data.get("T1"), data.get("T2")
        if t1 is None or t2 is None:
            # A reply that echoes T0 and omits the server's own stamps is not
            # a sample; the HTTP measurement takes this cycle.
            LOG.debug("Incomplete TimeSync response: %s", data)
            return False

        offset, rtt = utils.ntp_sample(t0, t1, t2, t3)
        self._add_sample(offset, rtt)
        return True

    def _ws_socket(self) -> Optional[websocket.WebSocket]:
        if self._ws is not None:
            return self._ws

        target = self.manager.timesync_ws_target()

        if not target:
            return None

        url, authorization = target

        try:
            self._ws = websocket.create_connection(
                url,
                timeout=3,
                header=handshake_header(authorization, self._user_agent),
                class_=NoRedirectSocket,
            )
        except Exception as error:
            LOG.debug("Time-sync socket connect failed: %s", error)
            return None

        LOG.debug("Time sync on dedicated socket %s", url)
        return self._ws

    def _close_ws(self) -> None:
        sock, self._ws = self._ws, None

        if sock is not None:
            try:
                sock.close()
            except Exception:
                pass

    def _measure_http(self) -> None:
        t0 = utils.local_ms()
        response = self.manager.get_utc_time()
        t3 = utils.local_ms()

        if not response:
            return

        t1 = utils.parse_iso_ms(response.get("RequestReceptionTime"))
        t2 = utils.parse_iso_ms(response.get("ResponseTransmissionTime"))

        if t1 is None or t2 is None:
            LOG.warning("Unusable GetUtcTime response: %s", response)
            return

        offset, rtt = utils.ntp_sample(t0, t1, t2, t3)
        self._add_sample(offset, rtt)

    def _add_sample(self, offset: float, rtt: float) -> None:
        if rtt < 0:  # nonsense measurement (clock stepped mid-exchange)
            return

        with self._lock:
            self.samples.append((offset, rtt))
            best_offset, best_rtt = min(self.samples, key=lambda s: s[1])

        self.offset_ms = best_offset
        self.rtt_ms = best_rtt
        self.ping_ms = max(best_rtt / 2.0, 0.0)

        LOG.debug(
            "Time sync: offset %.1fms rtt %.1fms (window %s)",
            best_offset,
            best_rtt,
            len(self.samples),
        )
        self.manager.on_timesync_update()
