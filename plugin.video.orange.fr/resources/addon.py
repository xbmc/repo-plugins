"""Addon entry point."""

import sys

import xbmc
import xbmcplugin
from lib.channelmanager import ChannelManager
from lib.iptvmanager import IPTVManager
from lib.utils.xbmctools import log, ok_dialog
from routing import Plugin

router = Plugin()


@router.route("/")
def index():
    """Display a welcome message."""
    log("Hello from plugin.video.orange.fr", xbmc.LOGINFO)
    ok_dialog("Hello from plugin.video.orange.fr")


@router.route("/channels/<channel_id>")
def channel(channel_id: str):
    """Load stream for the required channel id."""
    log(f"Loading channel {channel_id}", xbmc.LOGINFO)
    listitem = ChannelManager().load_channel_listitem(channel_id)
    if listitem is not None:
        xbmcplugin.setResolvedUrl(router.handle, True, listitem=listitem)


@router.route("/iptv/channels")
def iptv_channels():
    """Return JSON-STREAMS formatted data for all live channels."""
    log("Loading channels for IPTV Manager", xbmc.LOGINFO)
    port = int(router.args.get("port")[0])
    IPTVManager(port).send_channels()


@router.route("/iptv/epg")
def iptv_epg():
    """Return JSON-EPG formatted data for all live channel EPG data."""
    log("Loading EPG for IPTV Manager")
    port = int(router.args.get("port")[0])
    IPTVManager(port).send_epg()


if __name__ == "__main__":
    log(sys.version, xbmc.LOGDEBUG)
    router.run()
