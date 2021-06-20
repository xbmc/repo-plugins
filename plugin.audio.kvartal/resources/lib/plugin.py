import sys
from urllib.parse import parse_qsl
from resources.lib.menus import MenuList


def run():
    paramstring = sys.argv[2]
    params = dict(parse_qsl(paramstring[1:]))
    menu_list = MenuList()
    if params:
        if params["action"] == "listshows":
            menu_list.content_menu(params["show_id"])
        elif params["action"] == "getshowsummary":
            menu_list.view_show_summary(params["show_id"])
        elif params["action"] == "getepisodesummary":
            menu_list.view_episode_summary(params["show_id"], params["episode_id"])
        elif params["action"] == "play":
            menu_list.play_audio(params["audio"])
    else:
        menu_list.root_menu()
