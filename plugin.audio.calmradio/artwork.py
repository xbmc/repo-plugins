import xbmcgui
from xbmcaddon import Addon

ACTION_PARENT_DIR = 9
ACTION_PREVIOUS_MENU = 10
ADDON = Addon()
# ADDON_ID = ADDON.getAddonInfo('id')
# ADDON_NAME = ADDON.getAddonInfo('name')

class ArtworkWindow(xbmcgui.WindowDialog):
    def __init__(self):
        dimentions = {
            'spacing': {
              'normal': 20,
              'medium': 15,
              'small': 10
            },
            'cover': {
                'x1': 610,
                'x2': 1310,
                'y1': 215,
                'y2': 915,
            },
            'topbar': {
                'height': 180
            },
            'details': {
                'height': 160
            },
            'label': {
                'height': 30
            },
            'button': {
                'width': 40
            }
        }
        self.setCoordinateResolution(0) # 1920x1080

        # overlay
        self.overlay = xbmcgui.ControlImage(0,
                                       0,
                                       1920,
                                       1080,
                                       'special://home/addons/plugin.audio.calmradio/resources/media/000000-0.8.png')

        # top bar
        topbar = xbmcgui.ControlImage(
            0,
            0,
            1920,
            dimentions['topbar']['height'],
            'special://home/addons/plugin.audio.calmradio/resources/media/18B0E2-1.png'
        )

        # logo
        logo = xbmcgui.ControlImage(dimentions['spacing']['small'],
                                    dimentions['spacing']['small'],
                                    dimentions['topbar']['height'] - 2 * dimentions['spacing']['small'],
                                    dimentions['topbar']['height'] - 2 * dimentions['spacing']['small'],
                                    'special://home/addons/plugin.audio.calmradio/icon.png')

        # channel name
        self.channel = xbmcgui.ControlLabel(
            dimentions['topbar']['height'] - 2 * dimentions['spacing']['small'] +
            2 * dimentions['spacing']['small'],
            dimentions['spacing']['small'],
            1920 - dimentions['topbar']['height'] - 2 * dimentions['spacing']['small'] -
                2 * dimentions['spacing']['small'],
            dimentions['label']['height'],
            'Channel Name'
        )

        # channel description
        self.description = xbmcgui.ControlLabel(
            dimentions['topbar']['height'] - 2 * dimentions['spacing']['small'] +
            2 * dimentions['spacing']['small'],
            2 * dimentions['spacing']['small'] + dimentions['label']['height'],
            1920 - dimentions['topbar']['height'] - 2 * dimentions['spacing']['small'] -
                2 * dimentions['spacing']['small'],
            dimentions['label']['height'],
            'Channel Description',
            font='font12'
        )

        # close button
        self.btn_close = xbmcgui.ControlButton(
            1920 - dimentions['spacing']['small'] - dimentions['button']['width'],
            dimentions['spacing']['small'],
            dimentions['button']['width'],
            dimentions['button']['width'],
            'X',
            focusTexture='special://home/addons/plugin.audio.calmradio/resources/media/FFFFFF-0.4.png',
            noFocusTexture='special://home/addons/plugin.audio.calmradio/resources/media/FFFFFF-0.2.png',
            alignment=6,
            textColor='0xAAFFFFFF',
            focusedColor='0xFFFFFFFF'
        )

        # shadow
        cover_shadow = xbmcgui.ControlImage(
            dimentions['cover']['x1'] - dimentions['spacing']['normal'],
            dimentions['cover']['y1'] - dimentions['details']['height'] / 2 - dimentions['spacing']['normal'],
            dimentions['cover']['x2'] - dimentions['cover']['x1'] + 2 * dimentions['spacing']['normal'],
            dimentions['cover']['y2'] - dimentions['cover']['y1'] + dimentions['details']['height']
                 + 2 * dimentions['spacing']['normal'],
            'special://home/addons/plugin.audio.calmradio/resources/media/box-shadow.png'
        )

        # album art
        self.cover = xbmcgui.ControlImage(
            dimentions['cover']['x1'],
            dimentions['cover']['y1'] - dimentions['details']['height'] / 2,
            dimentions['cover']['x2'] - dimentions['cover']['x1'],
            dimentions['cover']['y2'] - dimentions['cover']['y1'],
            'special://home/addons/plugin.audio.calmradio/resources/media/18B0E2-1.png'
        )

        # details
        details = xbmcgui.ControlImage(dimentions['cover']['x1'],
                                     dimentions['cover']['y2'] - dimentions['details']['height'] / 2,
                                     dimentions['cover']['x2'] - dimentions['cover']['x1'],
                                     dimentions['details']['height'],
                                     'special://home/addons/plugin.audio.calmradio/resources/media/18B0E2-1.png')


        # song name
        self.song = xbmcgui.ControlLabel(
            dimentions['cover']['x1'] + dimentions['spacing']['normal'],
            dimentions['cover']['y2'] + dimentions['spacing']['normal'] -
                dimentions['details']['height'] / 2,
            dimentions['cover']['x2'] - dimentions['cover']['x1'] -
                2 * dimentions['spacing']['normal'],
            dimentions['label']['height'],
            'Song Name'
        )

        # album title
        self.album = xbmcgui.ControlLabel(
            dimentions['cover']['x1'] + dimentions['spacing']['normal'],
            dimentions['cover']['y2'] + 2 * dimentions['spacing']['normal'] -
                dimentions['details']['height'] / 2 +
                dimentions['label']['height'],
            dimentions['cover']['x2'] - dimentions['cover']['x1'] -
                2 * dimentions['spacing']['normal'],
            dimentions['label']['height'],
            'Album Title',
            font='font12'
        )

        # artist
        self.artist = xbmcgui.ControlLabel(
            dimentions['cover']['x1'] + dimentions['spacing']['normal'],
            dimentions['cover']['y2'] + 2 * dimentions['spacing']['normal'] -
                dimentions['details']['height'] / 2 +
                2 * dimentions['label']['height'],
            dimentions['cover']['x2'] - dimentions['cover']['x1'] -
                2 * dimentions['spacing']['normal'],
            dimentions['label']['height'],
            'Artist Name',
            font='font12'
        )
        # add all controls:
        self.addControls((self.overlay, topbar, logo, self.channel, self.description, self.btn_close,
                          cover_shadow, self.cover, details, self.song, self.album, self.artist))
        # set focus on close button:
        self.setFocus(self.btn_close)


    def onAction(self, action):
        if action == ACTION_PREVIOUS_MENU or action == ACTION_PARENT_DIR:
            self.setProperty('Closed', 'True')
            self.close()
        else:
            # set focus on close button:
            self.setFocus(self.btn_close)

    def onControl(self, control):
        if control == self.btn_close:
            self.close()
