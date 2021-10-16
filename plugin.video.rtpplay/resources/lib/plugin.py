import routing
import logging
import xbmcaddon
from sys import exit
from resources.lib import kodiutils
from resources.lib import kodilogging
from xbmcgui import ListItem, Dialog, INPUT_ALPHANUM
from xbmcplugin import addDirectoryItem, endOfDirectory, setResolvedUrl

from .kodiutils import format_date, get_stream_url, get_subtitles
from .rtpplayapi import RTPPlayAPI
import datetime as dt

from urllib.parse import urlencode

ADDON = xbmcaddon.Addon()
ICON = ADDON.getAddonInfo("icon")
logger = logging.getLogger(ADDON.getAddonInfo('id'))
kodilogging.config()
plugin = routing.Plugin()

rtpplayapi = RTPPlayAPI()

HEADERS = {
    "User-Agent": "RTP Play/2.0.26 (Linux;Android 11) ExoPlayerLib/2.11.8",
}


@plugin.route('/')
def index():
    livetv = ListItem("[B]{}[/B]".format(kodiutils.get_string(32012)))
    addDirectoryItem(handle=plugin.handle, listitem=livetv, isFolder=True, url=plugin.url_for(live, content='tv'))

    liveradio = ListItem("[B]{}[/B]".format(kodiutils.get_string(32013)))
    addDirectoryItem(handle=plugin.handle, listitem=liveradio, isFolder=True, url=plugin.url_for(live, content='radio'))

    programas = ListItem("[B]{}[/B]".format(kodiutils.get_string(32005)))
    addDirectoryItem(handle=plugin.handle, listitem=programas, isFolder=True, url=plugin.url_for(programs))

    pesquisar = ListItem("[B]{}[/B]".format(kodiutils.get_string(32006)))
    addDirectoryItem(handle=plugin.handle, listitem=pesquisar, isFolder=True, url=plugin.url_for(search))

    endOfDirectory(plugin.handle)


@plugin.route('/search')
def search():
    input_text = Dialog().input(kodiutils.get_string(32007), "", INPUT_ALPHANUM)
    return plugin.redirect(f'/search/{input_text}/1')


@plugin.route('/search/<input_text>/<page>')
def search_paged(input_text, page):
    showing_results = ListItem("{} [B]{}[/B]".format(kodiutils.get_string(32008), input_text))
    addDirectoryItem(handle=plugin.handle, listitem=showing_results, isFolder=False, url="")

    items_per_page = 30
    search_results = rtpplayapi.search(input_text, per_page=items_per_page, page=page, one_page=1)[0]
    for page in search_results:
        for res in page["programs"]:
            title = res["program_title"]
            img = res["program_image"]
            description = res["program_lead"]
            program_id = res["program_id"]

            liz = ListItem(title)
            liz.setArt({"thumb": img,
                        "icon": img,
                        "fanart": kodiutils.FANART})
            liz.setInfo("Video", infoLabels={"plot": description,
                                             "title": title})

            addDirectoryItem(
                plugin.handle,
                plugin.url_for(
                    programs_episodes,
                    title=title,
                    img=img,
                    prog_id=program_id,
                    page=1
                ), liz, True)

        if page.get("programs") and page.get("paging"):
            item_count = int(page["paging"]["total"])
            current_page = int(page["paging"]["current_page"])
            if current_page * items_per_page < item_count:
                nextpage = str(int(current_page) + 1)
                nextpage_listitem = ListItem(
                    "[B]{}[/B] - {} {} >>>".format(input_text, kodiutils.get_string(32009), nextpage))
                addDirectoryItem(handle=plugin.handle,
                                listitem=nextpage_listitem,
                                isFolder=True,
                                url=plugin.url_for(search_paged,
                                                    input_text=input_text,
                                                    page=nextpage))
        
        endOfDirectory(plugin.handle)


@plugin.route('/live')
def live():
    content_type = plugin.args["content"][0]
    if content_type == "tv":
        channels = rtpplayapi.get_live_tv_channels()
    elif content_type == "radio":
        channels = rtpplayapi.get_live_radio_channels()
    else:
        raise Exception("Wrong content type")

    for channel in channels:
        name = channel["channel_name"]
        img = channel["channel_card_logo"]

        def find_on_air():
            for onair in channel["onair"].values():
                if "real_end_date_time_utc" not in onair or "real_date_time_utc" not in onair:
                    continue
                end = dt.datetime.fromisoformat(onair["real_end_date_time_utc"])
                start = dt.datetime.fromisoformat(onair["real_date_time_utc"])
                now = dt.datetime.now(dt.timezone.utc)
                if now < start or now > end:
                    continue
                return onair
            if "current" in channel["onair"]:
                return channel["onair"]["current"]

        onair = find_on_air()
        if not onair:
            continue
        end = dt.datetime.fromisoformat(onair["real_end_date_time_utc"])
        start = dt.datetime.fromisoformat(onair["real_date_time_utc"])
        now = dt.datetime.now(dt.timezone.utc)
        progpercent = round(100 * (now - start).seconds / (end - start).seconds)
        progimg = img

        liz = ListItem("[B][COLOR blue]{}[/COLOR][/B] ({}) [B]{}[/B]".format(
            name,
            onair["title"],
            str(progpercent) + "%" if progpercent <= 100 else '')
        )
        liz.setArt({"thumb": progimg,
                    "icon": progimg,
                    "fanart": kodiutils.FANART})
        liz.setProperty('IsPlayable', 'true')
        liz.setInfo("Video",
                    infoLabels={"plot": onair["description"]})
        addDirectoryItem(
            plugin.handle,
            plugin.url_for(
                live_play,
                label=name,
                channel=channel["channel_id"],
                img=progimg,
                prog=onair["title"]
            ), liz, False)
    endOfDirectory(plugin.handle)

@plugin.route('/live/play')
def live_play():
    channel = plugin.args["channel"][0]
    name = plugin.args["label"][0]
    prog = plugin.args["prog"][0]

    icon = ICON
    if "img" in plugin.args:
        icon = plugin.args["img"][0]

    channel = rtpplayapi.get_channel(channel)

    liz = ListItem("[COLOR blue][B]{}[/B][/COLOR] ({})".format(
        name,
        prog)
    )
    liz.setArt({"thumb": icon, "icon": icon})
    liz.setProperty('IsPlayable', 'true')

    liz.setPath("{}|{}".format(get_stream_url(channel[0]), urlencode(HEADERS)))
    setResolvedUrl(plugin.handle, True, liz)


@plugin.route('/programs')
def programs():
    categories = rtpplayapi.get_categories()

    addDirectoryItem(handle=plugin.handle, listitem=ListItem("Todos os Programas"),
                     isFolder=True, url=plugin.url_for(programs_category, name="Todos os Programas", id=0, page=1))

    for i, name in categories.items():
        name = name
        liz = ListItem(name)
        addDirectoryItem(handle=plugin.handle, listitem=liz, isFolder=True, url=plugin.url_for(programs_category,
                                                                                               name=name, id=i, page=1))

    endOfDirectory(plugin.handle)


@plugin.route('/programs/category')
def programs_category():
    page = int(plugin.args["page"][0])
    cat_id = plugin.args["id"][0]
    cat_name = plugin.args["name"][0]

    pagei = ListItem("[B]{}[/B] - {} {}".format(cat_name, kodiutils.get_string(32009), page))
    pagei.setProperty('IsPlayable', 'false')
    addDirectoryItem(handle=plugin.handle, listitem=pagei, isFolder=False, url="")

    programs = rtpplayapi.list_programs(cat_id, one_page=page)[0][0]["programs"]

    for program in programs:
        prog_id = program["program_id"]
        title = program["program_title"]
        img = program["program_image"]
        description = program["program_lead"]
        episode_date = format_date(program["episode_date"])

        liz = ListItem("{} ({})".format(
            title,
            episode_date)
        )
        liz.setArt({"thumb": img,
                    "icon": img,
                    "fanart": kodiutils.FANART})
        liz.setInfo("Video", infoLabels={"plot": description,
                                         "title": title})

        addDirectoryItem(
            plugin.handle,
            plugin.url_for(
                programs_episodes,
                title=title,
                img=img,
                description=description,
                prog_id=prog_id,
                page=1
            ), liz, True)

    newpage = str(int(page) + 1)
    nextpage = ListItem("[B]{}[/B] - {} {} >>>".format(cat_name,
                                                       kodiutils.get_string(32009), newpage))
    addDirectoryItem(handle=plugin.handle, listitem=nextpage, isFolder=True,
                     url=plugin.url_for(programs_category, name=cat_name,
                                        id=cat_id, page=newpage))

    endOfDirectory(plugin.handle)


@plugin.route('/programs/episodes')
def programs_episodes():
    title = plugin.args["title"][0]
    img = plugin.args["img"][0]
    prog_id = plugin.args["prog_id"][0]
    page = int(plugin.args["page"][0])

    pagei = ListItem("[B]{}[/B] - {} {}".format(title, kodiutils.get_string(32009), page))
    pagei.setProperty('IsPlayable', 'false')
    addDirectoryItem(handle=plugin.handle, listitem=pagei, isFolder=False, url="")

    episodes = rtpplayapi.list_episodes(prog_id, one_page=page)[0][0]["episodes"]

    for episode in episodes:
        img = episode["asset_thumb"]
        description = episode["episode_description"]
        episode_date = format_date(episode["episode_date"])
        episode_id = episode["episode_id"]

        liz = ListItem(episode_date)
        liz.setArt({"thumb": img,
                    "icon": img,
                    "fanart": kodiutils.FANART})
        liz.setInfo("Video", infoLabels={"plot": description + "...",
                                         "title": episode_date})
        liz.setProperty('IsPlayable', 'true')

        addDirectoryItem(
            plugin.handle,
            plugin.url_for(
                programs_play,
                title=title,
                episode_date=episode_date,
                img=img,
                description=description,
                episode_id=episode_id,
                prog_id=prog_id
            ), liz, False)

    newpage = str(int(page) + 1)
    nextpage = ListItem(
        "[B]{}[/B] - {} {} >>>".format(title, kodiutils.get_string(32009), newpage))
    addDirectoryItem(handle=plugin.handle,
                     listitem=nextpage,
                     isFolder=True,
                     url=plugin.url_for(programs_episodes,
                                        title=title,
                                        img=img,
                                        prog_id=prog_id,
                                        page=newpage))

    endOfDirectory(plugin.handle)


@plugin.route('/programs/play')
def programs_play():
    title = plugin.args["title"][0]
    episode_date = plugin.args["episode_date"][0]
    img = plugin.args["img"][0]
    episode_id = plugin.args["episode_id"][0]
    prog_id = plugin.args["prog_id"][0]

    liz = ListItem("{} ({})".format(
        title,
        episode_date)
    )
    liz.setArt({"thumb": img, "icon": img})
    liz.setProperty('IsPlayable', 'true')

    episode = rtpplayapi.get_episode(prog_id, episode_id)["assets"][0]

    liz.setPath("{}|{}".format(get_stream_url(episode), urlencode(HEADERS)))

    subtitles = get_subtitles(episode)
    if subtitles:
        liz.setSubtitles(subtitles)

    setResolvedUrl(plugin.handle, True, liz)


def raise_notification():
    kodiutils.ok(kodiutils.get_string(32000), kodiutils.get_string(32002))
    exit(0)


def run():
    plugin.run()
