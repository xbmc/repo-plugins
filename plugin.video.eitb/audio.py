from utils import get_radio_programs
from utils import get_program_audios
from utils import get_radios
from utils import get_program_seasons
from utils import get_program_season_chapters
import xbmcgui
import xbmcplugin


class AudioHandler(object):
    def __init__(self, handle, url):
        self.handle = handle
        self.url = url

    def list_radios(self):
        listing = []
        for radio in get_radios():
            title = radio.get("title")
            radio_url = radio.get("@id")
            list_item = xbmcgui.ListItem(label=title)
            list_item.setInfo("music", {"title": title, "album": title})
            url = "{0}?action=radio&program={1}".format(self.url, radio_url)
            is_folder = True
            listing.append((url, list_item, is_folder))

        # Add our listing to Kodi.
        xbmcplugin.addDirectoryItems(self.handle, listing, len(listing))
        # Add a sort method for the virtual folder items
        xbmcplugin.addSortMethod(self.handle, xbmcplugin.SORT_METHOD_NONE)
        xbmcplugin.endOfDirectory(self.handle)

    def list_radio_programs(self, station):
        listing = []
        for program in get_radio_programs(station):
            title = program.get("title")
            radio = program.get("radio")
            program_url = program.get("@id")
            list_item = xbmcgui.ListItem(label=title)
            list_item.setInfo("music", {"title": title, "album": radio})
            url = "{0}?action=audioprogram&program={1}".format(
                self.url, program_url
            )
            is_folder = True
            listing.append((url, list_item, is_folder))

        # Add our listing to Kodi.
        xbmcplugin.addDirectoryItems(self.handle, listing, len(listing))
        # Add a sort method for the virtual folder items
        xbmcplugin.addSortMethod(self.handle, xbmcplugin.SORT_METHOD_NONE)
        xbmcplugin.endOfDirectory(self.handle)

    def list_seasons(self, program):
        seasons = get_program_seasons(program)
        items = []
        for season in seasons:
            label = season.get("title")
            url = season.get("@id")
            list_item = xbmcgui.ListItem(label=label)
            url = "{0}?action=audioseason&program={1}".format(self.url, url)
            is_folder = True
            items.append((url, list_item, is_folder))

        # Add our listing to Kodi.
        xbmcplugin.addDirectoryItems(self.handle, items, len(items))
        # Add a sort method for the virtual folder items
        xbmcplugin.addSortMethod(self.handle, xbmcplugin.SORT_METHOD_NONE)
        xbmcplugin.endOfDirectory(self.handle)

    def list_program_season_chapters(self, season):
        chapters = get_program_season_chapters(season)
        items = []
        for chapter in chapters:
            label = chapter.get("title")
            url = chapter.get("@id")
            list_item = xbmcgui.ListItem(label=label)
            url = "{0}?action=audiochapter&program={1}".format(self.url, url)
            is_folder = True
            items.append((url, list_item, is_folder))

        # Add our listing to Kodi.
        xbmcplugin.addDirectoryItems(self.handle, items, len(items))
        # Add a sort method for the virtual folder items
        xbmcplugin.addSortMethod(self.handle, xbmcplugin.SORT_METHOD_NONE)
        xbmcplugin.endOfDirectory(self.handle)

    def list_program_audios(self, program):
        audio = get_program_audios(program)
        song_list = []

        date = audio.get("date")
        title = audio.get("title")
        audio_url = audio.get("url")
        label = u"{0} ({1})".format(date, title)
        # create a list item using the song filename for the label
        list_item = xbmcgui.ListItem(label=label)

        url = "{0}?action=audioplay&program={1}".format(self.url, audio_url)
        is_folder = False
        song_list.append((url, list_item, is_folder))

        # Add our listing to Kodi.
        xbmcplugin.addDirectoryItems(self.handle, song_list, len(song_list))
        # Add a sort method for the virtual folder items
        xbmcplugin.addSortMethod(self.handle, xbmcplugin.SORT_METHOD_NONE)
        xbmcplugin.endOfDirectory(self.handle)

    def play_audio(self, path):
        play_item = xbmcgui.ListItem(path=path)
        # Pass the item to the Kodi player.
        xbmcplugin.setResolvedUrl(self.handle, True, listitem=play_item)
