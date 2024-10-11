"""Addon routes."""

import xbmc

from lib.managers import CatchupManager, IPTVManager, StreamManager
from lib.router import router
from lib.utils.kodi import log


@router.route("/")
def index():
    """Display catchup service index."""
    log("Display catchup index", xbmc.LOGINFO)
    CatchupManager().build_directory()


@router.route("/catchup/<path:levels>")
def catchup_(levels: str):
    """Display catchup service directory."""
    log(f"Display catchup directory {levels}", xbmc.LOGINFO)
    CatchupManager().build_directory(levels)


@router.route("/stream/live/<stream_id>")
def stream_live(stream_id: str):
    """Load live stream for the required channel id."""
    log(f"Loading live stream {stream_id}", xbmc.LOGINFO)
    StreamManager().load_live_stream(stream_id)


@router.route("/stream/catchup/<stream_id>")
def stream_catchup(stream_id: str):
    """Load live stream for the required video id."""
    log(f"Loading catchup stream {stream_id}", xbmc.LOGINFO)
    StreamManager().load_chatchup_stream(stream_id)


@router.route("/iptv/channels")
def iptv_channels():
    """Return JSON-STREAMS formatted data for all live channels."""
    log("Loading channels for IPTV Manager", xbmc.LOGINFO)
    port = int(router.args.get("port")[0])
    IPTVManager(port).send_channels()


@router.route("/iptv/epg")
def iptv_epg():
    """Return JSON-EPG formatted data for all live channel EPG data."""
    log("Loading EPG for IPTV Manager", xbmc.LOGINFO)
    port = int(router.args.get("port")[0])
    IPTVManager(port).send_epg()
