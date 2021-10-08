from urllib.parse import parse_qsl
from resources.lib.menus import MenuList


def router(paramstring):

    menu_list = MenuList()

    params = dict(parse_qsl(paramstring))
    if params:
        if params["action"] == "showdocs":
            menu_list.show_documentaries(params["path"], params["page"])
        if params["action"] == "showcategories":
            menu_list.show_categories()
        elif params["action"] == "showtoplist":
            menu_list.show_toplist(params["path"])
        elif params["action"] == "showsearchmenu":
            menu_list.show_search_menu()
        elif params["action"] == "newsearch":
            query_id = menu_list.search()
            if query_id is not None:
                menu_list.show_searched_documentaries(query_id, 0)
        elif params["action"] == "showsearchhistory":
            menu_list.show_search_history()
        elif params["action"] == "removesearch":
            menu_list.search_history_update(params["action"],
                                            remove_id=params["remove_id"])
        elif params["action"] == "clearsearch":
            menu_list.search_history_update(params["action"])
        elif params["action"] == "searchdocs":
            menu_list.show_searched_documentaries(params["query_id"],
                                                  int(params["offset"]))
        elif params["action"] == "showplot":
            menu_list.show_plot(params["path"])
        elif params["action"] == "playmedia":
            menu_list.play_video(params["path"])
    else:
        menu_list.show_main_menu()
