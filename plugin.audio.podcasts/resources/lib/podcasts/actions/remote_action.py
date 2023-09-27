import xbmcgui
from resources.lib.podcasts.actions.opml_action import OpmlAction
from resources.lib.podcasts.util import get_asset_path


class RemoteAction(OpmlAction):

    def __init__(self) -> None:
        super().__init__()

    def subscribe_feeds(self, feeds: list[dict]) -> 'tuple[list[dict], bool]':

        items: 'list[xbmcgui.ListItem]' = list()
        for f in feeds:
            li = xbmcgui.ListItem(
                label=f["title"], label2=f["subtitle"], path=f["url"])
            li.setArt({"thumb": f["icon"]})
            items.append(li)

        selected_feeds = xbmcgui.Dialog().multiselect(
            heading=self.addon.getLocalizedString(32126), options=items, useDetails=True)

        if selected_feeds == None:
            return [], True

        elif not selected_feeds:
            return feeds, False

        group, freeslots = self._select_target_group()
        if group == -1:
            return feeds, False

        elif freeslots < len(selected_feeds):
            xbmcgui.Dialog().ok(self.addon.getLocalizedString(32074),
                                self.addon.getLocalizedString(32075) % freeslots)
            return feeds, False

        else:
            self.addon.setSetting("group_%i_enable" % group, "True")
            i, j = 0, 0
            while (i < self._ENTRIES):
                if j < len(selected_feeds) and not self.addon.getSettingBool("group_%i_rss_%i_enable" % (group, i)):
                    self.addon.setSettingBool(
                        "group_%i_rss_%i_enable" % (group, i), True)
                    self.addon.setSetting("group_%i_rss_%i_name" % (
                        group, i), items[selected_feeds[j]].getLabel())
                    self.addon.setSetting("group_%i_rss_%i_url" % (
                        group, i), items[selected_feeds[j]].getPath())
                    self.addon.setSetting(
                        "group_%i_rss_%i_icon" % (group, i), items[selected_feeds[j]].getArt("thumb"))
                    j += 1

                i += 1

            xbmcgui.Dialog().notification(heading=self.addon.getLocalizedString(32085),
                                          message=self.addon.getLocalizedString(32127), icon=get_asset_path(asset="notification.png"))

            feeds = [f for i, f in enumerate(
                feeds) if i not in selected_feeds]

            return feeds, False
