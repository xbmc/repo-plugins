from resources.lib.podcasts.actions.opml_action import OpmlAction
from resources.lib.rssaddon.http_status_error import HttpStatusError
from resources.lib.podcasts.opml_file import parse_opml
from resources.lib.podcasts.gpodder import GPodder
from resources.lib.podcasts.podcastsaddon import ENTRIES, GROUPS

import xbmcgui

class ImportGPodderSubscriptionsAction(OpmlAction):

    def __init__(self):
        super().__init__()

    def _query_subscriptions_from_gpodder(self):

        try:
            host = self.addon.getSetting("gpodder_hostname")
            user = self.addon.getSetting("gpodder_username")
            password = self.addon.getSetting("gpodder_password")

            gPodder = GPodder(self.addon, host, user)
            sessionid = gPodder.login(password)
            subscriptions = gPodder.request_subscriptions(sessionid)
            name, entries = parse_opml(subscriptions)
            return name, entries

        except HttpStatusError as error:
            xbmcgui.Dialog().ok(self.addon.getLocalizedString(32151), error.message)
            return None, None

    def import_gpodder_subscriptions(self, only_new_ones=False):

        def _filter_new_ones(entries):
            _known_urls = list()
            for g in range(self._GROUPS):
                if self.addon.getSetting("group_%i_enable" % g) == "true":
                    for e in range(self._ENTRIES):
                        if self.addon.getSetting("group_%i_rss_%i_enable" % (g, e)) == "true":
                            _known_urls.append(self.addon.getSetting(
                                "group_%i_rss_%i_url" % (g, e)))

            return [e for e in entries if "params" in e and len(e["params"]) == 1 and "rss" in e["params"][0] and e["params"][0]["rss"] not in _known_urls]

        # Step 1: query subscriptions from gPodder
        name, entries = self._query_subscriptions_from_gpodder()
        if only_new_ones:
            entries = _filter_new_ones(entries)

        if len(entries) == 0:
            xbmcgui.Dialog().ok(
                self.addon.getLocalizedString(32071), self.addon.getLocalizedString(32088))
            return

        # Step 2: Select target group
        group, freeslots = self._select_target_group()
        if group == -1:
            return

        # Step 3: Select feeds
        feeds = self._select_feeds(name, entries, freeslots)
        if feeds == None:
            return

        # Step 4: Apply to group
        self._apply_to_group(entries, group, feeds)

        # Success
        xbmcgui.Dialog().notification(self.addon.getLocalizedString(
            32085), self.addon.getLocalizedString(32086))
