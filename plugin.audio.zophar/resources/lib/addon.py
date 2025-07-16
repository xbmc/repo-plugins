import sys
from typing import Final, Iterator, Optional, Tuple, Union, cast
from urllib.parse import parse_qs, urlencode

import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin
import xbmcvfs

from resources.lib import zophar

LOCALIZED_IDS: Final = {
    "Consoles": 30000,
    "Computers": 30001,
    "Music By Letter": 30002,
    "Info": 30003,
    "Search": 137,
    "Random Game": 30005,
    "Top 100 Games": 30006,
    "Developers": 30007,
    "Publishers": 30008,
    "Music by Year": 30009,
}

MONTHS_CODES: Final = (
    "Jan",
    "Feb",
    "Mar",
    "Apr",
    "May",
    "Jun",
    "Jul",
    "Aug",
    "Sep",
    "Oct",
    "Nov",
    "Dec",
)


ItemArgs = Tuple[str, xbmcgui.ListItem, bool]

BASE_URL: Final = sys.argv[0]
PLUGIN_HANDLE: Final = int(sys.argv[1])
ARGS: Final = parse_qs(sys.argv[2][1:])
ADDON: Final = xbmcaddon.Addon()
ADDON_PATH: Final = xbmcvfs.translatePath(ADDON.getAddonInfo("path"))


def build_url(**params: str) -> str:
    return f"{BASE_URL}?{urlencode(params)}"


def arg(key: str) -> Optional[str]:
    if x := ARGS.get(key):
        return x[0]


def i18n(string: Union[str, int]) -> str:
    if isinstance(string, str):
        if (id := LOCALIZED_IDS.get(string)) is None:
            return string
    else:
        id, string = string, str(string)

    if id >= 30000:
        return ADDON.getLocalizedString(id) or string

    return xbmc.getLocalizedString(id) or string


def date_normalize(value: str) -> str:
    # Input: `Feb 26th, 1987`, `Feb 1987`, `1987`.
    # Output: `1987-02-26`, `1987-02`, `1987`.
    parts = value.split()
    result = [parts.pop()]  # year

    if parts:
        month = MONTHS_CODES.index(parts.pop(0)) + 1
        result.append(f"{month:02}")

        if parts:
            if not (day := parts.pop()[:2])[1].isdecimal():
                day = f"0{day[0]}"

            result.append(day)

    return "-".join(result)


def menuitem_args(label: str) -> ItemArgs:
    return build_url(menu=label), xbmcgui.ListItem(i18n(label)), True


def submenuitem_args(item: zophar.Browsable) -> ItemArgs:
    name, path = item.name, item.path
    return build_url(path=path, submenu=name), xbmcgui.ListItem(i18n(name)), True


def infopageitem_args(item: zophar.Browsable) -> ItemArgs:
    return build_url(path=item.path), xbmcgui.ListItem(item.name), True


def gamelistitem_args(game: zophar.GameEntry) -> ItemArgs:
    label = game.name

    if platform := game.console:
        label += f" ({platform})"

    item = xbmcgui.ListItem(label)
    info: xbmc.InfoTagMusic = item.getMusicInfoTag()

    info.setAlbum(game.name)
    info.setGenres(["Soundtrack"])

    if year := game.year:
        info.setReleaseDate(year)

    if developer := game.developer:
        info.setArtist(developer)

    if cover := game.cover:
        item.setArt({"thumb": cover})

    return build_url(path=game.path), item, True


def add_gamelist(gamelist: zophar.GameListPage) -> None:
    items = list(map(gamelistitem_args, gamelist.entries))
    xbmcplugin.addDirectoryItems(PLUGIN_HANDLE, items)
    xbmcplugin.addSortMethod(PLUGIN_HANDLE, xbmcplugin.SORT_METHOD_LABEL)
    xbmcplugin.setContent(PLUGIN_HANDLE, "albums")
    xbmcplugin.setPluginCategory(PLUGIN_HANDLE, i18n(gamelist.title))


def build_menu(menu_items: zophar.Menu):
    items = list(menu_items)
    items.append("Search")  # add search item
    items = list(map(menuitem_args, items))
    xbmcplugin.addDirectoryItems(PLUGIN_HANDLE, items)
    xbmcplugin.addSortMethod(PLUGIN_HANDLE, xbmcplugin.SORT_METHOD_NONE)
    xbmcplugin.setContent(PLUGIN_HANDLE, "files")


def build_submenu(menu_items: zophar.Menu, menu: str):
    items = list(map(submenuitem_args, menu_items[menu]))
    xbmcplugin.addDirectoryItems(PLUGIN_HANDLE, items)
    xbmcplugin.addSortMethod(PLUGIN_HANDLE, xbmcplugin.SORT_METHOD_NONE)
    xbmcplugin.setContent(PLUGIN_HANDLE, "files")
    xbmcplugin.setPluginCategory(PLUGIN_HANDLE, i18n(menu))


def build_infopage(page: zophar.InfoPage):
    items = list(map(infopageitem_args, page.entries))
    xbmcplugin.addDirectoryItems(PLUGIN_HANDLE, items)
    xbmcplugin.addSortMethod(PLUGIN_HANDLE, xbmcplugin.SORT_METHOD_LABEL)
    xbmcplugin.setContent(PLUGIN_HANDLE, "files")
    # all infopages in submenu, so `submenu` is always exist
    xbmcplugin.setPluginCategory(PLUGIN_HANDLE, i18n(cast(str, arg("submenu"))))


def build_gamelist(gamelist: zophar.GameListPage, path: str):
    add_gamelist(gamelist)

    if (n := gamelist.page) < gamelist.total_pages:
        build_gamelist(zophar.gamelist(path, n + 1), path)


def get_audioformat(game: zophar.GamePage) -> zophar.AudioFormat:
    if ADDON.getSettings().getBool("flac") and game.has_format(zophar.AudioFormat.FLAC):
        return zophar.AudioFormat.FLAC
    return zophar.AudioFormat.MP3


def build_gamepage(game: zophar.GamePage):
    album, developer, cover = game.name, game.developer, game.cover
    mimetype = (format := get_audioformat(game)).mime

    if release_date := game.release_date:
        release_date = date_normalize(release_date)

    def _tracks() -> Iterator[ItemArgs]:
        for num, track in enumerate(game.tracks, 1):
            item = xbmcgui.ListItem(track.title)
            info: xbmc.InfoTagMusic = item.getMusicInfoTag()

            item.setMimeType(mimetype)
            item.setContentLookup(False)
            info.setTrack(num)
            info.setTitle(track.title)
            info.setDuration(track.length.seconds)
            info.setGenres(["Soundtrack"])
            info.setMediaType("song")
            info.setURL(url := track.url(format))
            info.setAlbum(album)

            if developer:
                info.setArtist(developer)

            if release_date:
                info.setReleaseDate(release_date)

            if cover:
                item.setArt({"thumb": cover})

            yield url, item, False

    xbmcplugin.addDirectoryItems(PLUGIN_HANDLE, list(_tracks()))
    xbmcplugin.addSortMethod(PLUGIN_HANDLE, xbmcplugin.SORT_METHOD_TRACKNUM)
    xbmcplugin.setContent(PLUGIN_HANDLE, "songs")
    xbmcplugin.setPluginCategory(PLUGIN_HANDLE, album)


class SearchDialog(xbmcgui.WindowXMLDialog):
    def __init__(self, *args, **kwargs) -> None:
        self.platforms = kwargs.pop("platforms")
        self.setProperty("platform", self.platforms[0])
        super().__init__(*args, **kwargs)

    def select_platform(self) -> None:
        if (id := xbmcgui.Dialog().select(i18n(30202), self.platforms)) != -1:
            self.setProperty("platform", self.platforms[id])

    @property
    def text(self) -> str:
        return cast(xbmcgui.ControlEdit, self.getControl(100)).getText()

    def onClick(self, control_id: int) -> None:
        if control_id == 100:  # edit control
            return self.getControl(102).setEnabled(len(self.text) >= 3)

        if control_id == 101:  # select platform button
            return self.select_platform()

        if control_id == 102:  # search button
            self.setProperty("context", self.text)
            return self.close()

    @classmethod
    def run(cls, platforms: zophar.Platforms) -> bool:
        dialog = cls(
            "search-dialog.xml",
            ADDON_PATH,
            "default",
            "1080i",
            platforms=list(platforms),
        )

        dialog.doModal()

        if context := dialog.getProperty("context"):
            platform = platforms[dialog.getProperty("platform")]

            if result := zophar.search(context, platform):
                add_gamelist(result)
                return True

            xbmcgui.Dialog().ok(i18n(283), i18n(284))  # not found dialog

        return False


def run() -> None:
    if path := arg("path"):
        page = zophar.page(path)

        if isinstance(page, zophar.GameListPage):
            build_gamelist(page, path)

        elif isinstance(page, zophar.GamePage):
            build_gamepage(page)

        elif isinstance(page, zophar.InfoPage):
            build_infopage(page)

    else:
        menu_items, platforms = zophar.home()

        if menu := arg("menu"):
            if menu != "Search":
                build_submenu(menu_items, menu)

            elif not SearchDialog.run(platforms):
                return

        else:
            build_menu(menu_items)

    xbmcplugin.endOfDirectory(PLUGIN_HANDLE)
