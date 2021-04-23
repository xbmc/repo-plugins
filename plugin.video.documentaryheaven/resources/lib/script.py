from urllib.parse import parse_qsl
from resources.lib.api import DocumentaryHeaven


def router(paramstring):

    docuheaven = DocumentaryHeaven()

    params = dict(parse_qsl(paramstring))
    if params:
        if params["action"] == "listall":
            docuheaven.all_list(params["url"])
        if params["action"] == "listcategories":
            docuheaven.categories_list(params["url"])
        elif params["action"] == "listalltime":
            docuheaven.toplist(params["url"])
        elif params["action"] == "listthisyear":
            docuheaven.toplist(params["url"])
        elif params["action"] == "search":
            docuheaven.search()
        elif params["action"] == "listsearch":
            docuheaven.search_list(params["query"], int(params["offset"]))
        elif params["action"] == "showplot":
            docuheaven.show_plot(params["url"])
        elif params["action"] == "playmedia":
            docuheaven.play_video(params["url"])
    else:
        docuheaven.main_menu_list()
