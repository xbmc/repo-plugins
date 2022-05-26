import xbmcaddon
import xbmcgui
import xbmcvfs


class Action:

    addon = None
    addon_dir = None
    anchor_for_latest = True

    _GROUPS = 10
    _ENTRIES = 10

    def __init__(self):

        self.addon = xbmcaddon.Addon()
        self.addon_dir = xbmcvfs.translatePath(self.addon.getAddonInfo('path'))

    def _select_target_group(self) -> 'tuple[int,int]':

        names = list()
        freeslots = list()
        for g in range(self._GROUPS):
            free = sum("false" == self.addon.getSetting(
                "group_%i_rss_%i_enable" % (g, r)) for r in range(self._ENTRIES))

            freeslots.append(free)

            names.append("%s %i: %s (%i %s)" %
                         (
                             self.addon.getLocalizedString(32000),
                             g + 1,
                             self.addon.getSetting("group_%i_name" % g),
                             free,
                             self.addon.getLocalizedString(32077)
                         ))

        selected = xbmcgui.Dialog().select(self.addon.getLocalizedString(32076), names)
        if selected > -1 and freeslots[selected] == 0:
            xbmcgui.Dialog().ok(heading=self.addon.getLocalizedString(32078),
                                message=self.addon.getLocalizedString(32084))
            return -1, 0

        elif selected == -1:
            return -1, 0

        else:
            return selected, freeslots[selected]

    def _select_target_opml_slot(self, heading: str, multi=False):

        selection = list()
        for g in range(self._GROUPS):
            filename = self.addon.getSetting("opml_file_%i" % g)
            selection.append("%s %i%s" % (self.addon.getLocalizedString(
                32023), g + 1, ": %s" % filename if filename else ""))

        dialog = xbmcgui.Dialog().multiselect if multi else xbmcgui.Dialog().select
        return dialog(heading, selection)
