import sys
from urllib.parse import parse_qsl
from xbmcgui import Dialog
from resources.lib.api import TeliaException
from resources.lib.menus import MenuList
from resources.lib.kodiutils import AddonUtils


class Router():

    def __init__(self, params):
        self.params = params
        self.menu_list = MenuList()

    def main_menu(self):
        if self.params:
            if self.params["menu"] == "page":
                self.page_menu()
            elif self.params["menu"] == "storePanel":
                self.menu_list.store_panel_menu(
                    self.params["storeId"], self.params["panelId"]
                )
            elif self.params["menu"] == "panel":
                self.menu_list.panel_menu(
                    self.params["panelId"], int(self.params["page"])
                )
            elif self.params["menu"] == "series":
                self.menu_list.series_menu(self.params["seriesId"])
            elif self.params["menu"] == "season":
                self.menu_list.season_menu(self.params["seasonId"])
            elif self.params["menu"] == "rent":
                self.menu_list.rent_menu(self.params["videoId"])
            elif self.params["menu"] == "searchmenu":
                self.menu_list.search_menu()
            elif self.params["menu"] == "newsearch":
                query_id = self.menu_list.search()
                if query_id is not None:
                    self.menu_list.panel_menu(query_id, 0, search=True)
            elif self.params["menu"] == "search":
                self.menu_list.panel_menu(
                    int(self.params["panelId"]),
                    int(self.params["page"]),
                    search=True
                )
            elif self.params["menu"] == "history":
                self.menu_list.show_search_history()
            elif self.params["menu"] == "removesearch":
                self.menu_list.search_history_update(
                    self.params["menu"], self.params["panelId"]
                )
                self.menu_list.refresh()
            elif self.params["menu"] == "clearsearch":
                self.menu_list.search_history_update(self.params["menu"])
                self.menu_list.refresh()
            elif self.params["menu"] == "addToList":
                self.menu_list.telia_play.add_to_my_list(self.params["mediaId"])
            elif self.params["menu"] == "removeFromList":
                self.menu_list.telia_play.remove_from_my_list(
                    self.params["mediaId"]
                )
                self.menu_list.refresh()
            elif self.params["menu"] == "play":
                self.menu_list.play_stream(
                    self.params["streamId"], self.params["streamType"]
                )
        else:
            self.menu_list.main_menu()

    def page_menu(self):
        if "mode" in self.params:
            if self.params["mode"] == "På TV":
                self.channel_menu()
            elif self.params["mode"] == "Alla Playtjänster":
                self.play_store()
            elif "pageId" in self.params:
                self.menu_list.page_submenu(
                    self.params["pageId"], self.params["mode"]
                )
        elif self.params["pageId"] == "epg":
            self.channel_menu()
        else:
            self.menu_list.page_menu(self.params["pageId"])

    def channel_menu(self):
        if "channelId" in self.params and "dayOffset" in self.params:
            self.menu_list.tv_programs_menu(
                self.params["channelId"], self.params["dayOffset"]
            )
        else:
            if "page" not in self.params:
                self.menu_list.tv_channels_menu()
            else:
                self.menu_list.tv_channels_menu(int(self.params["page"]))


    def play_store(self):
        if "storeId" in self.params:
            self.menu_list.play_store_menu(self.params["storeId"])
        else:
            self.menu_list.play_stores_menu()


def run():
    paramstring = sys.argv[2][1:]
    params = dict(parse_qsl(paramstring))
    try:
        router = Router(params)
        router.main_menu()
    except TeliaException as te:
        Dialog().textviewer(AddonUtils().name, str(te))
