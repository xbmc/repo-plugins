"""Addon routes."""

import xbmc

from lib.managers import CatchupManager, IPTVManager, StreamManager
from lib.router import router
from lib.utils.kodi import log


@router.route("/")
def index():
    """Display catchup TV channels."""
    log("Display home", xbmc.LOGINFO)
    CatchupManager().get_channels()


@router.route("/channels/<catchup_channel_id>/categories")
def channel_categories(catchup_channel_id: str):
    """Return catchup category listitems for the required channel id."""
    log(f"Loading catchup categories for channel {catchup_channel_id}", xbmc.LOGINFO)
    CatchupManager().get_categories(catchup_channel_id)


@router.route("/channels/<catchup_channel_id>/categories/<category_id>/articles")
def channel_category_articles(catchup_channel_id: str, category_id: str):
    """Return catchup category article listitems."""
    log(f"Loading catchup articles for category {category_id}", xbmc.LOGINFO)
    CatchupManager().get_articles(catchup_channel_id, category_id)


@router.route("/channels/<catchup_channel_id>/articles/<article_id>/videos")
def channel_article_videos(catchup_channel_id: str, article_id: str):
    """Return catchup article video listitems."""
    log(f"Loading catchup videos for article {article_id}", xbmc.LOGINFO)
    CatchupManager().get_videos(catchup_channel_id, article_id)


@router.route("/videos/<video_id>")
def video(video_id: str):
    """Return catchup video listitem."""
    log(f"Loading catchup video {video_id}", xbmc.LOGINFO)
    CatchupManager().play_video(video_id)


@router.route("/live-streams/<stream_id>")
def live_stream(stream_id: str):
    """Load live stream for the required channel id."""
    log(f"Loading live stream {stream_id}", xbmc.LOGINFO)
    StreamManager().load_live_stream(stream_id)


@router.route("/catchup-streams/<stream_id>")
def catchup_stream(stream_id: str):
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
