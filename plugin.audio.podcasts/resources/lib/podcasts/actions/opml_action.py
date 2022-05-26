import xbmcgui
from resources.lib.podcasts.actions.action import Action


class OpmlAction(Action):

    def __init__(self):
        super().__init__()

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

    def _select_feeds(self, name: str, entries: 'list[dict]', freeslots: 'list[int]') -> 'list[int]':

        selection = [e["name"]
                     for e in entries if "params" in e and len(e["params"]) == 1 and "rss" in e["params"][0]]

        if len(selection) == 0:
            xbmcgui.Dialog().ok(
                self.addon.getLocalizedString(32071), self.addon.getLocalizedString(32088))
            return None

        ok = False
        while not ok:
            feeds = xbmcgui.Dialog().multiselect(
                self.addon.getLocalizedString(32071), selection)
            if feeds == None:
                ok = True
            elif len(feeds) == 0:
                xbmcgui.Dialog().ok(self.addon.getLocalizedString(32072),
                                    self.addon.getLocalizedString(32073))
            elif len(feeds) > freeslots:
                xbmcgui.Dialog().ok(self.addon.getLocalizedString(32074),
                                    self.addon.getLocalizedString(32075) % freeslots)
            else:
                ok = True

        return feeds

    def _apply_to_group(self, entries: dict, group: int, feeds: 'list[int]') -> None:

        self.addon.setSetting("group_%i_enable" % group, "True")

        i, j = 0, 0
        while(i < self._ENTRIES):

            if j < len(feeds) and "false" == self.addon.getSetting("group_%i_rss_%i_enable" % (group, i)):
                self.addon.setSetting("group_%i_rss_%i_enable" %
                                      (group, i), "True")
                self.addon.setSetting("group_%i_rss_%i_name" %
                                      (group, i), entries[feeds[j]]["name"])
                self.addon.setSetting("group_%i_rss_%i_url" % (
                    group, i), entries[feeds[j]]["params"][0]["rss"])
                self.addon.setSetting("group_%i_rss_%i_icon" % (group, i), "")
                j += 1

            i += 1
