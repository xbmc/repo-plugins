from utils import get_radio_programs
from utils import get_program_audios

import xbmcgui
import xbmcplugin


class AudioHandler(object):
    def __init__(self, handle, url):
        self.handle = handle
        self.url = url

    def list_radio_programs(self):
        listing = []
        for program in get_radio_programs():
            title = program.get('title')
            radio = program.get('radio')
            program_url = program.get('@id')
            list_item = xbmcgui.ListItem(label=title)
            list_item.setInfo('music', {'title': title, 'album': radio})
            url = '{0}?action=audiolisting&program={1}'.format(self.url, program_url)
            is_folder = True
            listing.append((url, list_item, is_folder))

        # Add our listing to Kodi.
        xbmcplugin.addDirectoryItems(self.handle, listing, len(listing))
        # Add a sort method for the virtual folder items
        xbmcplugin.addSortMethod(self.handle, xbmcplugin.SORT_METHOD_NONE)
        xbmcplugin.endOfDirectory(self.handle)

    def list_program_audios(self, program):
        audios = get_program_audios(program)
        song_list = []
        for audio in audios:
            date = audio.get('date')
            title = audio.get('title')
            audio_url = audio.get('url')
            label = u'{0} ({1})'.format(date, title)
            # create a list item using the song filename for the label
            list_item = xbmcgui.ListItem(label=label)
            list_item.setProperty('IsPlayable', 'true')
            url = '{0}?action=audioplay&program={1}'.format(self.url, audio_url)
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
