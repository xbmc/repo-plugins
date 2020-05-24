import functools
from contextlib import contextmanager

from sys import version_info

if version_info.major > 2:
    from urllib.parse import parse_qsl
else:
    from urlparse import parse_qsl

import xbmcgui
import xbmcplugin
import xbmcaddon
import xbmc
from resources.lib import curiositystream as cs

tr = xbmcaddon.Addon().getLocalizedString


@contextmanager
def authorize_context():
    """
    This authorize context will display a progress dialog when the
    CuriosityStream API is performing a login and eventually will show
    an error message in the Kodi UI
    """
    dialog = xbmcgui.DialogProgress()
    dialog.create(tr(30001))
    try:
        yield
        dialog.close()
    except cs.CSAuthFailed as e:
        dialog.close()
        xbmcgui.Dialog().ok(tr(30002), e.error_message)
    except Exception as e:
        dialog.close()
        xbmcgui.Dialog().ok(tr(30002), "Internal error: {}".format(str(e)))


class Router(object):
    def __init__(self, plugin_url, plugin_handle):
        self._plugin_url = plugin_url
        self._plugin_handle = plugin_handle
        self._cs_api = cs.CuriosityStream(
            username=xbmcaddon.Addon().getSetting("username"),
            password=xbmcaddon.Addon().getSetting("password"),
            profile_path=xbmc.translatePath(xbmcaddon.Addon().getAddonInfo("profile")),
            auth_context=authorize_context,
        )
        # ensure the user is logged in by calling my_account api
        self._cs_api.my_account()

    def route(self, query):
        params = dict(parse_qsl(query[1:]))
        action = params.get("action", "list_root")
        parent = params.get("parent", None)
        page = params.get("page", None)
        if action == "list_root":
            self._list_root()
        elif action == "list_categories":
            self._list_categories(parent)
        elif action in [
            "watchlist",
            "list_media",
            "list_collections",
            "list_collections2",
            "history",
            "list_popular",
            "recently_added",
            "watching",
            "recommended",
        ]:
            self._list_media_or_collections(action, parent, page)
        elif action == "play":
            self._play_media(params["media"])
        elif action == "change_watchlist":
            self._change_watchlist(
                params["media"], params["is_bookmarked"], params["is_collection"]
            )
        elif action == "search":
            query = params.get("query", None)
            query = xbmcgui.Dialog().input(tr(30022)) if not query else query
            if not query:
                return
            self._list_media_or_collections(action, parent, page, query)

    def _list_root(self):
        """
        Root listing reflects the CuriosityStream site sections:
        * Watchlist
        * Browse Categories
        * Collections: the curated collections (v2 in the API)
        * History
        * Trending Today
        * Pick Up where you left off
        * Newest Additions
        * We Suggest for You
        """

        def root_entry(action, label):
            return (
                "{}?action={}".format(self._plugin_url, action),
                xbmcgui.ListItem(label=label),
                True,
            )

        listing = [
            root_entry("watchlist", tr(30013)),
            root_entry("list_categories", tr(30014)),
            root_entry("list_collections2", tr(30015)),
            root_entry("history", tr(30016)),
            root_entry("list_popular", tr(30018)),
            root_entry("watching", tr(30019)),
            root_entry("recently_added", tr(30020)),
            root_entry("recommended", tr(30021)),
            root_entry("search", tr(30022)),
        ]
        xbmcplugin.addDirectoryItems(self._plugin_handle, listing, len(listing))
        xbmcplugin.addSortMethod(self._plugin_handle, xbmcplugin.SORT_METHOD_NONE)
        xbmcplugin.endOfDirectory(self._plugin_handle)

    def _list_categories(self, parent):
        listing = []
        for category in self._cs_api.categories(parent):
            list_item = xbmcgui.ListItem(label=category["label"])
            list_item.setArt(category["art"])
            url = "{}?action={}&parent={}".format(
                self._plugin_url,
                # there is only two level of categories on CuriosityStream
                "list_media" if parent is not None else "list_categories",
                category["name"],
            )
            is_folder = True
            listing.append((url, list_item, is_folder))
        if parent is not None:
            # adds a meta-category "All" to browse all media in all subcategories
            listing.append(
                (
                    "{}?action=list_media&parent={}".format(self._plugin_url, parent),
                    xbmcgui.ListItem(label=tr(30012)),
                    True,
                )
            )
        xbmcplugin.addDirectoryItems(self._plugin_handle, listing, len(listing))
        xbmcplugin.addSortMethod(
            self._plugin_handle, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE
        )
        xbmcplugin.endOfDirectory(self._plugin_handle)

    def _list_media_or_collections(self, action, parent, page, query=None):
        listing = []
        api_by_action = {
            "list_media": functools.partial(self._cs_api.media, parent, page),
            "list_collections": functools.partial(
                self._cs_api.collections_v1, parent, page
            ),
            "list_collections2": functools.partial(
                self._cs_api.collections_v2, parent, page
            ),
            "watchlist": functools.partial(self._cs_api.watchlist, page),
            "history": functools.partial(self._cs_api.history, page),
            "list_popular": functools.partial(self._cs_api.popular, page),
            "recently_added": functools.partial(self._cs_api.recently_added, page),
            "watching": functools.partial(self._cs_api.watching, page),
            "recommended": functools.partial(self._cs_api.recommended, page),
            "search": functools.partial(self._cs_api.search, query, page),
        }
        media, prev_page, next_page = api_by_action[action]()

        def pagination_entry(new_page, label):
            return (
                "{}?action={}{}{}{}".format(
                    self._plugin_url,
                    action,
                    "&query={}".format(query) if query else "",
                    "&parent={}".format(parent) if parent else "",
                    "&page={}".format(new_page),
                ),
                xbmcgui.ListItem(label=label),
                True,
            )

        if prev_page:
            listing.append(pagination_entry(prev_page, tr(30011)))

        folder_action = (
            "list_collections2"
            if action == "list_collections2" and parent is None
            else "list_collections"
        )
        for m in media:
            # there are two different types of media on CuriosityStream:
            # - collections: a group of videos of the same theme/series
            # - non-collections: are videos not belonging to any collection
            # The collections will be represented as folder and the rest as playable items
            list_item = xbmcgui.ListItem(label=m["label"])
            list_item.setArt(m["art"])
            list_item.setInfo("video", m["video"])
            list_item.setProperty("IsPlayable", "false" if m["is_folder"] else "true")
            list_item.addContextMenuItems(
                [
                    (
                        tr(30023) if m["is_bookmarked"] else tr(30024),
                        "RunPlugin({}?action=change_watchlist"
                        "&media={}&is_bookmarked={}&is_collection={})".format(
                            self._plugin_url,
                            m["id"],
                            m["is_bookmarked"],
                            m["is_folder"],
                        ),
                    )
                ]
            )

            url = "{}?action={}{}".format(
                self._plugin_url,
                "{}&parent=".format(folder_action) if m["is_folder"] else "play&media=",
                m["id"],
            )
            listing.append((url, list_item, m["is_folder"]))

        if next_page:
            listing.append(pagination_entry(next_page, tr(30010)))

        xbmcplugin.addDirectoryItems(self._plugin_handle, listing, len(listing))
        xbmcplugin.addSortMethod(self._plugin_handle, xbmcplugin.SORT_METHOD_NONE)
        xbmcplugin.endOfDirectory(self._plugin_handle, updateListing=page is not None)

    def _play_media(self, media):
        stream = self._cs_api.media_stream_info(media)
        play_item = xbmcgui.ListItem(path=stream["streams"][0]["master_playlist_url"])
        play_item.setSubtitles([c["file"] for c in stream["subtitles"]])
        xbmcplugin.setResolvedUrl(self._plugin_handle, True, listitem=play_item)

    def _change_watchlist(self, media_id, is_bookmarked, is_collection):
        self._cs_api.update_user_media(
            media_id, is_bookmarked != "True", is_collection == "True"
        )
        dialog = xbmcgui.Dialog()
        dialog.notification(
            tr(30025), tr(30026) if is_bookmarked == "True" else tr(30027),
        )
        xbmc.executebuiltin("Container.Refresh()")
