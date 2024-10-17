from utils import *
import xbmcgui

class Element():
    def __init__(self, title="", args={}) -> None:
        self.is_folder = False
        self.title = title
        self.mode="url"
        self.art = None
        self.args = {k: v[0] for (k, v) in list(args.items())}

    def setMode(self, mode) -> None:
        self.mode = mode

    def isFolder(self) -> bool:
        return self.is_folder

    def construct(self):
        li = xbmcgui.ListItem(self.title)
        li.setIsFolder(self.is_folder)
        li.setArt(self.art)
        self.args['mode'] = self.mode
        new_url = build_url(self.args)
        return (new_url, li, True)

    def add(self, kodi_list) -> None:
        kodi_tuple = self.construct()
        kodi_list.append(kodi_tuple)

class Search(Element):
    def __init__(self,args={}) -> None:
        super().__init__(localize(30100), args)
        self.is_folder = True
        self.mode = "search"

class Podcasts(Element):
    def __init__(self, args={}) -> None:
        super().__init__(localize(30104), args)
        self.is_folder = True
        self.mode = "podcasts"

class Page(Element):
    def __init__(self, num = 0, plus = 1, args={}) -> None:
        super().__init__(localize(30101) if plus == -1 else localize(30102), args)
        self.is_folder = True
        self.args['page'] = num + plus

class Pages(Element):
    def __init__(self, item, args={}) -> None:
        self.is_folder = True
        (num, last) = item.pages
        self.pages = []
        if 1 < num:
            self.pages.append(Page(num, -1, args))
        if num < last:
            self.pages.append(Page(num, +1, args))
    def add(self, kodi_list) -> None:
        for page in self.pages:
            page.add(kodi_list)

class Folder(Element):
    def __init__(self, item, args={}) -> None:
        super().__init__(item.title, args)
        self.is_folder = True
        self.art = {'thumb': item.image, 'icon': item.icon}
        self.args = {
            'title': item.title,
            'url': item.path,
            'mode': "url",
        }

class Indexed(Element):
    def __init__(self, item, url, index, args={}) -> None:
        super().__init__("⭐ " + item.title if item.title is not None else "", args)
        self.is_folder = True
        self.art = {'thumb': item.image, 'icon': item.icon}
        self.mode = "index"
        self.args = {
            'title': item.title,
            'url': url,
            'index': index,
        }

class Playable(Element):
    def __init__(self, item, args={}) -> None:
        super().__init__(item.title, args)
        self.art = {'thumb': item.image, 'icon': item.icon}
        self.is_folder = False
        self.genre = item.genre if item.model == Model['Brand'] else "podcast"
        self.artists = item.artists
        self.duration = item.duration if item.duration is not None else 0
        self.release = item.release
        self.args['url'] = item.path
        self.path = item.path
        self.mode = "brand" if item.model == Model["Brand"] else "stream"

    def construct(self):
        (url, li, _) = super().construct()
        li.setProperty("IsPlayable", "true")

        tag = li.getMusicInfoTag(offscreen=True)
        tag.setMediaType("audio")
        tag.setTitle(self.title)
        tag.setURL(self.path)
        tag.setGenres([self.genre])
        tag.setArtist(self.artists)
        tag.setDuration(self.duration)
        tag.setReleaseDate(self.release)

        return(url, li, False)
