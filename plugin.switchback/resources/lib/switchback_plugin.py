import sys
from urllib.parse import parse_qs

# noinspection PyUnresolvedReferences
import xbmc
import xbmcplugin
import xbmcgui

from resources.lib.store import Store
from bossanova808.constants import TRANSLATE, KODI_MAJOR_VERSION
from bossanova808.logger import Logger
from bossanova808.notify import Notify


# PVR HACK!
# Needed to trigger live PVR playback with proper PVR controls (channel OSD, channel up/down etc)
# for an *off-screen* resolve - i.e. only for the "switchback" mode below, which plays a specific
# item with no user click for Kodi to hook into. A directly resolved-item ListItem/setResolvedUrl()
# gives you basic playback, but never routes through Kodi's PVR-aware
# CPVRGUIActionsPlayback::SwitchToChannel() path, so Kodi never activates the actual live-TV
# session. This was a genuine Kodi core bug (not addon-side, and not just an Omega-era thing, as an
# earlier pass at this assumed) - see https://github.com/xbmc/xbmc/issues/28877, fixed by
# https://github.com/xbmc/xbmc/pull/28893, landing in Kodi 22 (Piers). So this hack is only used
# below on Kodi < 22, where the underlying bug is still present.
# NOT needed for the default list mode further below on any Kodi version - an on-screen click on a
# pvr:// item there already routes through Kodi's native handling correctly on its own (and, per
# testing, using this hack there instead causes a hard crash - so don't. See the same issue link
# above for the crash report/discussion).
def pvr_hack(path, resume=False):
    """
    :param path: the pvr:// channel or recording path to play
    :param resume: for recordings, pass True to have Kodi apply its own tracked resume position
        (see bossanova808 script.service.playbackresumer for the full story on why - the short
        version: a manually-set resume position doesn't work reliably for PVR recordings, but
        PlayMedia's own "resume" keyword, which asks Kodi to apply whatever position it's already
        tracking for the item itself, does). Not meaningful for live channels - there's no
        position to resume to.
    """
    xbmc.PlayList(xbmc.PLAYLIST_VIDEO).clear()
    # Kodi is jonesing for one of these, so give it the sugar it needs, see: https://forum.kodi.tv/showthread.php?tid=381623&pid=3232778#pid3232778
    xbmcplugin.setResolvedUrl(int(sys.argv[1]), False, xbmcgui.ListItem())
    builtin = f'PlayMedia("{path}", resume)' if resume else f'PlayMedia("{path}")'
    Logger.debug("Work around PVR links not being handled by ListItem/setResolvedUrl - use PlayMedia instead:", builtin)
    # No ListItem to set a property on here, so set on the Home Window instead
    Store.update_home_window_switchback_property(path)
    xbmc.executebuiltin(builtin)


def run():
    Logger.start("(Plugin)")
    # This also forces an update of the Switchback list from disk, in case of changes via the service side of things.
    Store()

    plugin_instance = int(sys.argv[1])
    xbmcplugin.setContent(plugin_instance, 'video')

    parsed_arguments = parse_qs(sys.argv[2][1:])
    Logger.debug(parsed_arguments)
    mode = parsed_arguments.get('mode', None)
    modes = set([m.strip() for m in mode[0].split(",") if m.strip()]) if mode else set()
    if modes:
        Logger.info(f"Switchback mode: {mode}")
    else:
        Logger.info("Switchback mode: default - generate 'folder' of items")

    # Switchback mode - easily swap between switchback.list[0] and switchback.list[1]
    # If there's only one item in the list, then resume playing that item
    if "switchback" in modes:

        # First, determine what to play, if anything...
        if not Store.switchback.list:
            Notify.error(TRANSLATE(32007))
            Logger.error("No Switchback found to play")
            return

        if len(Store.switchback.list) == 1:
            switchback_to_play = Store.switchback.list[0]
            Logger.debug("Switchback to index 0")
        else:
            switchback_to_play = Store.switchback.list[1]
            Logger.debug("Switchback to index 1")

        # We know what to play...
        Logger.info(f"Switchback! Switching back to: {switchback_to_play.pluginlabel}")
        Logger.debug(f"Path: [{switchback_to_play.path}]")
        Logger.debug(f"File: [{switchback_to_play.file}]")
        image = switchback_to_play.poster or switchback_to_play.icon
        at_timestamp = f" at {switchback_to_play.resume_timestamp}" if switchback_to_play.resume_timestamp else ""
        if switchback_to_play.source == "pvr_live":
            # Retuning live TV involves Kodi spinning up a full PVR session (buffering etc), which
            # can take several seconds - call this out so it doesn't read as broken/unresponsive
            notification_text = f"Re-tuning live TV: {switchback_to_play.pluginlabel_short} (this may take a moment)"
        elif switchback_to_play.source == "pvr_recording":
            notification_text = f"Resuming PVR Recording: {switchback_to_play.pluginlabel_short}{at_timestamp}"
        elif at_timestamp:
            notification_text = f"Resuming: {switchback_to_play.pluginlabel_short}{at_timestamp}"
        else:
            notification_text = switchback_to_play.pluginlabel_short
        Notify.kodi_notification(notification_text, 3000, image)

        # Short circuit here if PVR and we're on a Kodi still needing the PVR hack (see pvr_hack
        # above). Kodi core PR https://github.com/xbmc/xbmc/pull/28893 (fixing
        # https://github.com/xbmc/xbmc/issues/28877) resolves this properly from Piers (22) onwards
        # (confirmed via testing against a pre-release Kodi build with the fix, all 4 PVR
        # onscreen/offscreen x live/recording combinations working correctly, hack-free), so the
        # hack is no longer used there, for either live or recordings. Recordings still need the
        # hack pre-fix (with resume=True) - a directly resolved item doesn't reliably apply the
        # resume position for a recording off-screen, same issue as live TV's controls.
        if switchback_to_play.source in ("pvr_live", "pvr_recording") and KODI_MAJOR_VERSION < 22:
            pvr_hack(switchback_to_play.path, resume=(switchback_to_play.source == "pvr_recording"))
            return

        # Normal path for everything else (and for PVR on Kodi 22+)
        list_item = switchback_to_play.create_list_item_from_playback()
        list_item.setProperty('Switchback', switchback_to_play.path)
        # Store.update_home_window_switchback_property(switchback_to_play.path)
        xbmcplugin.setResolvedUrl(plugin_instance, True, list_item)
        Logger.stop("(Plugin)")
        return

    # Delete an item from the Switchback list - e.g. if it is not playing back properly from Switchback
    elif "delete" in modes:
        index_values = parsed_arguments.get('index')
        if index_values:
            try:
                idx = int(index_values[0])
            except (ValueError, TypeError):
                Logger.error("Invalid 'index' parameter for delete:", index_values)
                return
            if 0 <= idx < len(Store.switchback.list):
                Logger.info(f"Deleting playback {idx} from Switchback list")
                Store.switchback.list.pop(idx)
            else:
                Logger.error("Index out of range for delete:", idx)
                return
        else:
            Logger.error("Missing 'index' parameter for delete")
            return

        # Save the updated list and then reload it, just to be sure
        Store.switchback.save_to_file()
        Store.switchback.load_or_init()
        Store.update_switchback_context_menu()
        Logger.debug("Force refreshing the container, so Kodi immediately displays the updated Switchback list")
        xbmc.executebuiltin("Container.Refresh")

    # Default mode - show the whole Switchback List (each of which has a context menu option to delete itself)
    else:
        for index, playback in enumerate(Store.switchback.list[0:Store.maximum_list_length]):
            list_item = playback.create_list_item_from_playback()
            # Add delete option to this item
            list_item.addContextMenuItems([(TRANSLATE(32004), "RunPlugin(plugin://plugin.switchback?mode=delete&index=" + str(index) + ")")])
            # For detecting Switchback playbacks (in player.py)
            list_item.setProperty('Switchback', playback.path)
            # No pvr_hack proxy here - an on-screen click on a pvr:// item routes through Kodi's own
            # native PVR-aware handling correctly (proper controls, no crash) without our help. The
            # hack is only needed for the "switchback" mode above, which resolves off-screen with no
            # user click for Kodi to hook into. Use file for all Kodi library playbacks, and path for
            # addons/PVR (as addon paths may include tokens etc, and PVR only has a path)
            url = playback.file if playback.source not in ["addon", "pvr_live", "pvr_recording"] else playback.path
            xbmcplugin.addDirectoryItem(plugin_instance, url, list_item)

        xbmcplugin.endOfDirectory(plugin_instance, cacheToDisc=False)

    # And we're done...
    Logger.stop("(Plugin)")
