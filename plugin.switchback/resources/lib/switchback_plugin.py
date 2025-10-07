import sys
from urllib.parse import parse_qs

# noinspection PyUnresolvedReferences
import xbmc
import xbmcplugin
import xbmcgui

from resources.lib.store import Store
from bossanova808.constants import TRANSLATE
from bossanova808.logger import Logger
from bossanova808.notify import Notify


# PVR HACK!
# Needed to trigger live PVR playback with proper PVR controls.
# See https://forum.kodi.tv/showthread.php?tid=381623
def pvr_hack(path):
    xbmc.PlayList(xbmc.PLAYLIST_VIDEO).clear()
    # Kodi is jonesing for one of these, so give it the sugar it needs, see: https://forum.kodi.tv/showthread.php?tid=381623&pid=3232778#pid3232778
    xbmcplugin.setResolvedUrl(int(sys.argv[1]), False, xbmcgui.ListItem())
    # Get the full details from our stored playback
    # pvr_playback = Store.switchback.find_playback_by_path(path)
    builtin = f'PlayMedia("{path}")'
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
        Notify.kodi_notification(f"{switchback_to_play.pluginlabel_short}", 3000, image)

        # Short circuit here if PVR, see pvr_hack above.
        if 'pvr://channels' in switchback_to_play.path:
            pvr_hack(switchback_to_play.path)
            return

        # Normal path for everything else
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

    # See pvr_hack(path) above
    elif "pvr_hack" in modes:
        path_values = parsed_arguments.get('path')
        if not path_values or not path_values[0]:
            Logger.error("Missing 'path' parameter for pvr_hack")
            return
        path = path_values[0]
        Logger.debug(f"Triggering PVR Playback hack for {path}")
        pvr_hack(path)
        return

    # Default mode - show the whole Switchback List (each of which has a context menu option to delete itself)
    else:
        for index, playback in enumerate(Store.switchback.list[0:Store.maximum_list_length]):
            list_item = playback.create_list_item_from_playback()
            # Add delete option to this item
            list_item.addContextMenuItems([(TRANSLATE(32004), "RunPlugin(plugin://plugin.switchback?mode=delete&index=" + str(index) + ")")])
            # For detecting Switchback playbacks (in player.py)
            list_item.setProperty('Switchback', playback.path)
            # Use the 'proxy' URL if we're dealing with pvr_live and need to trigger the PVR playback hack
            if playback.source == "pvr_live":
                proxy_url = f"plugin://plugin.switchback?mode=pvr_hack&path={playback.path}"
                Logger.debug(f"Creating directory item with pvr_hack proxy url: {proxy_url}")
                xbmcplugin.addDirectoryItem(plugin_instance, proxy_url, list_item)
                # TODO -> not sure if URL encoding needed in some cases?  Maybe CodeRabbit knows?
                #     args = urlencode({'mode': 'pvr_hack', 'path': self.path})
                #     proxy_url = f"plugin://plugin.switchback/?{args}"

            # Otherwise use file for all Kodi library playbacks, and path for addons (as those may include tokens etc)
            else:
                url = playback.file if playback.source not in ["addon", "pvr_live"] else playback.path
                # Logger.debug(f"Creating directory item with url: {url}")
                xbmcplugin.addDirectoryItem(plugin_instance, url, list_item)

        xbmcplugin.endOfDirectory(plugin_instance, cacheToDisc=False)

    # And we're done...
    Logger.stop("(Plugin)")
