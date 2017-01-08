import sys
import routing
from api import API
from xbmc import Player, sleep, translatePath, getCondVisibility
from xbmcgui import getCurrentWindowDialogId
from xbmcaddon import Addon
from player import PlayerWindow

ADDON = Addon()
ADDON_HANDLE = int(sys.argv[1])
ADDON_ID = ADDON.getAddonInfo('id')
ADDON_NAME = ADDON.getAddonInfo('name')
ADDON_DATA_FOLDER = translatePath(ADDON.getAddonInfo('profile')).decode('utf-8')
PLUGIN = routing.Plugin()


@PLUGIN.route('/')
def index():
    """
    Main add-on popup
    :return:
    """
    player_window = PlayerWindow()
    api = API()

    # stop player if track is not part of this addon:
    if Player().isPlaying() and '.100fm.' not in Player().getPlayingFile():
        Player().stop()

    # create player window and display:
    player_window.show()
    player_window_id = getCurrentWindowDialogId()

    while getCondVisibility('Window.IsActive({0})'.format(player_window_id)):
        if player_window.getProperty('current') != '':
            song = api.get_current_song(player_window.getProperty('current'))
            player_window.song.setLabel('[CAPITALIZE][B]{0}[/B][/CAPITALIZE]'.format(song['name']))
            player_window.artist.setLabel('[CAPITALIZE]{0}[/CAPITALIZE]'.format(song['artist']))
        sleep(4000)
    del player_window


if __name__ == '__main__':
    PLUGIN.run()
