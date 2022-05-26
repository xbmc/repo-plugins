from resources.lib.podcasts.actions.action import Action

import xbmc
import xbmcgui


class UnassignOpmlAction(Action):

    def __init__(self):
        super().__init__()

    def unassign_opml(self) -> None:

        # Step 1: Select slots
        slots = self._select_target_opml_slot(
            self.addon.getLocalizedString(32087), multi=True)
        if slots == None or len(slots) == 0:
            return

        # Step 2: empty slots
        for slot in slots:
            self.addon.setSetting("opml_file_%i" % slot, " ")

        # Success
        xbmcgui.Dialog().notification(self.addon.getLocalizedString(
            32085), self.addon.getLocalizedString(32086))

    def _select_target_opml_slot(self, heading: str, multi=False):

        selection = list()
        for g in range(self._GROUPS):
            filename = self.addon.getSetting("opml_file_%i" % g)
            selection.append("%s %i%s" % (self.addon.getLocalizedString(
                32023), g + 1, ": %s" % filename if filename else ""))

        dialog = xbmcgui.Dialog().multiselect if multi else xbmcgui.Dialog().select
        return dialog(heading, selection)
