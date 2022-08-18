import xbmc
import xbmcgui
from resources.lib.podcasts.actions.opml_action import OpmlAction
from resources.lib.podcasts.opml_file import open_opml_file, parse_opml


class ImportOpmlAction(OpmlAction):

    def __init__(self):
        super().__init__()

    def import_opml(self) -> None:

        # Step 1: Select target group
        group, freeslots = self._select_target_group()
        if group == -1:
            return

        # Step 2: Select file
        name, entries = self._select_opml_file()
        if name == None:
            return

        # Step 3: Select feeds
        feeds = self._select_feeds(name, entries, freeslots)
        if feeds == None:
            return

        # Step 4: Confirm
        self._apply_to_group(entries, group, feeds)

        # Success
        xbmcgui.Dialog().notification(self.addon.getLocalizedString(
            32085), self.addon.getLocalizedString(32086))

    def _select_opml_file(self) -> 'tuple[str,list]':

        path = xbmcgui.Dialog().browse(
            type=1, heading=self.addon.getLocalizedString(32070), shares="", mask=".xml|.opml")
        if path == "":
            return None, None

        try:
            return parse_opml(open_opml_file(path))

        except:
            xbmc.log("Cannot read opml file %s" % path, xbmc.LOGERROR)
            return None, None
