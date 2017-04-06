import xbmc
import xbmcgui
from config import config
from xbmcaddon import Addon

ACTION_PARENT_DIR = 9
ACTION_PREVIOUS_MENU = 10
ADDON = Addon()
ADDON_ID = ADDON.getAddonInfo("id")
ADDON_NAME = ADDON.getAddonInfo("name")


class IntroWindow(xbmcgui.WindowDialog):
    def __init__(self, api):
        object.__init__(self)

        self.controls = {
            'buttons': []
        }
        self.api = api
        self.setCoordinateResolution(0)  # 1920x1080
        dimensions = {
            'spacing': {
                'normal': 20
            },
            'window': {
                'x1': 300,
                'x2': 1600,
                'y1': 200,
                'y2': 880,
            },
            'sidebar': {
                'width': 400
            },
            'logo': {
                'height': 210,
                'width': 200,
            },
            'description': {
                'height': 30
            },
            'thumbnail': {
                'height': 200,
                'width': 200,
                'per_row': 4
            },
            'exit': {
                'height': 50
            },
            'caption': {
                'height': 50
            }
        }
        categories = api.get_categories(1)

        # add favorites & atmospheres:
        categories += [
            {
                'id': 3,
                'name': ADDON.getLocalizedString(32102),
                'image': 'special://home/addons/plugin.audio.calmradio/resources/media/fanart/3.jpg'
            }
        ]

        # overlay
        overlay = xbmcgui.ControlImage(0,
                                       0,
                                       1920,
                                       1080,
                                       'special://home/addons/plugin.audio.calmradio/resources/media/000000-0.4.png')

        # popup
        popup = xbmcgui.ControlImage(dimensions['window']['x1'],
                                     dimensions['window']['y1'],
                                     dimensions['window']['x2'] - dimensions['window']['x1'],
                                     dimensions['window']['y2'] - dimensions['window']['y1'],
                                     'special://home/addons/plugin.audio.calmradio/resources/media/000000-0.8.png')
        # sidebar
        sidebar = xbmcgui.ControlImage(dimensions['window']['x1'],
                                       dimensions['window']['y1'],
                                       dimensions['sidebar']['width'],
                                       dimensions['window']['y2'] - dimensions['window']['y1'],
                                       'special://home/addons/plugin.audio.calmradio/resources/media/18B0E2-1.png')
        # logo
        logo = xbmcgui.ControlImage(dimensions['window']['x1'] + 100,
                                    dimensions['window']['y1'] + dimensions['spacing']['normal'],
                                    dimensions['logo']['width'],
                                    dimensions['logo']['height'],
                                    'special://home/addons/plugin.audio.calmradio/icon.png')
        # description
        description1 = xbmcgui.ControlLabel(dimensions['window']['x1'],
                                            dimensions['window']['y1'] + dimensions['logo']['height'] + 40,
                                            dimensions['sidebar']['width'],
                                            dimensions['description']['height'],
                                            ADDON.getLocalizedString(32355),
                                            textColor='aaffffff', alignment=2, font='font12')
        description2 = xbmcgui.ControlLabel(dimensions['window']['x1'],
                                            dimensions['window']['y1'] + dimensions['logo']['height'] + 80,
                                            dimensions['sidebar']['width'],
                                            dimensions['description']['height'],
                                            ADDON.getLocalizedString(32356).encode('utf-8'),
                                            textColor='ffffffff', alignment=2)

        # user account button:
        self.btn_account = xbmcgui.ControlButton(dimensions['window']['x1'] + dimensions['spacing']['normal'],
                                                 dimensions['window']['y2'] - (dimensions['spacing']['normal'] +
                                                                               dimensions['exit']['height']) * 3,
                                                 dimensions['sidebar']['width'] - dimensions['spacing']['normal'] * 2,
                                                 dimensions['exit']['height'],
                                                 ADDON.getLocalizedString(32350),
                                                 alignment=2,
                                                 noFocusTexture='special://home/addons/plugin.audio.calmradio/resources/media/FFFFFF-0.2.png',
                                                 focusTexture='special://home/addons/plugin.audio.calmradio/resources/media/FFFFFF-0.4.png')

        # exit button:
        self.btn_my_channels = xbmcgui.ControlButton(dimensions['window']['x1'] + dimensions['spacing']['normal'],
                                                     dimensions['window']['y2'] - (dimensions['spacing']['normal'] +
                                                                                   dimensions['exit']['height']) * 2,
                                                     dimensions['sidebar']['width'] - dimensions['spacing'][
                                                         'normal'] * 2,
                                                     dimensions['exit']['height'],
                                                     ADDON.getLocalizedString(32351),
                                                     alignment=2,
                                                     noFocusTexture='special://home/addons/plugin.audio.calmradio/resources/media/FFFFFF-0.2.png',
                                                     focusTexture='special://home/addons/plugin.audio.calmradio/resources/media/FFFFFF-0.4.png')

        # exit button:
        self.btn_exit = xbmcgui.ControlButton(dimensions['window']['x1'] + dimensions['spacing']['normal'],
                                              dimensions['window']['y2'] - dimensions['spacing']['normal'] -
                                              dimensions['exit']['height'],
                                              dimensions['sidebar']['width'] - dimensions['spacing']['normal'] * 2,
                                              dimensions['exit']['height'],
                                              ADDON.getLocalizedString(32352),
                                              alignment=2,
                                              focusTexture='special://home/addons/plugin.audio.calmradio/resources/media/FFFFFF-0.4.png')

        # add ui controls:
        self.addControls((overlay, popup, sidebar, logo, description1, description2,
                          self.btn_exit, self.btn_account, self.btn_my_channels))

        # add categories:
        for idx, item in enumerate(categories):
            x = dimensions['window']['x1'] + dimensions['sidebar']['width'] + dimensions['spacing']['normal'] + \
                ((idx % dimensions['thumbnail']['per_row']) * (
                    dimensions['thumbnail']['width'] + dimensions['spacing']['normal']))
            y = dimensions['window']['y1'] + dimensions['spacing']['normal'] + \
                ((idx / dimensions['thumbnail']['per_row']) * (
                    dimensions['thumbnail']['height'] + dimensions['spacing']['normal']))
            # button:
            button = xbmcgui.ControlButton(x - 3,
                                           y - 3,
                                           dimensions['thumbnail']['width'] + 6,
                                           dimensions['thumbnail']['height'] + 6,
                                           str(item['id']),
                                           noFocusTexture='special://home/addons/plugin.audio.calmradio/resources/media/0D5C77-1.png',
                                           focusTexture='special://home/addons/plugin.audio.calmradio/resources/media/18B0E2-1.png')
            self.controls['buttons'].append(button)
            self.addControl(button)
            # thumbnail:
            self.addControl(xbmcgui.ControlImage(x,
                                                 y,
                                                 dimensions['thumbnail']['width'],
                                                 dimensions['thumbnail']['height'],
                                                 '{0}{1}'.format('' if item['id'] == 3 or item['id'] == 99 else
                                                                 config['urls']['calm_arts_host'], item['image'])))
            # caption background:
            self.addControl(xbmcgui.ControlImage(x,
                                                 y + dimensions['thumbnail']['height'] - dimensions['caption'][
                                                     'height'],
                                                 dimensions['thumbnail']['width'],
                                                 dimensions['caption']['height'],
                                                 'special://home/addons/plugin.audio.calmradio/resources/media/000000-0.8.png'))
            # caption label:
            self.addControl(xbmcgui.ControlLabel(x,
                                                 y + dimensions['thumbnail']['height'] - dimensions['caption'][
                                                     'height'],
                                                 dimensions['thumbnail']['width'],
                                                 dimensions['caption']['height'],
                                                 item['name'].capitalize(),
                                                 font='font12',
                                                 alignment=6))

        # set navigation:
        for idx, button in enumerate(self.controls['buttons']):
            button.setNavigation(left=self.controls['buttons'][idx - 1] if idx > 0 else button,
                                 right=self.controls['buttons'][idx + 1] if (idx + 1) < len(
                                         self.controls['buttons']) else button,
                                 up=self.controls['buttons'][idx - dimensions['thumbnail']['per_row']]
                                 if idx - dimensions['thumbnail']['per_row'] >= 0 else button,
                                 down=self.controls['buttons'][idx + dimensions['thumbnail']['per_row']]
                                 if idx + dimensions['thumbnail']['per_row'] < len(
                                         self.controls['buttons']) else button)
        self.controls['buttons'][0].controlLeft(self.btn_account)
        self.controls['buttons'][len(self.controls['buttons']) - 1].controlRight(self.controls['buttons'][0])

        # side bar navigation:
        self.btn_account.setNavigation(self.controls['buttons'][0], self.btn_my_channels, self.controls['buttons'][0],
                                       self.controls['buttons'][0])
        self.btn_my_channels.setNavigation(self.btn_account, self.btn_exit, self.controls['buttons'][0],
                                           self.controls['buttons'][0])
        self.btn_exit.setNavigation(self.btn_my_channels, self.controls['buttons'][0], self.controls['buttons'][0],
                                    self.controls['buttons'][0])
        # focus on first button:
        self.setFocus(self.controls['buttons'][0])

    def onAction(self, action):
        if action == xbmcgui.ACTION_BACKSPACE or action == xbmcgui.ACTION_PARENT_DIR or \
                        action == xbmcgui.ACTION_PREVIOUS_MENU or action == xbmcgui.ACTION_NAV_BACK:
            self.close()

    def onControl(self, control):
        if control == self.btn_exit:
            self.close()
        elif control == self.btn_account:
            xbmc.executebuiltin('Addon.OpenSettings({0})'.format(ADDON_ID))
        elif control == self.btn_my_channels:
            self.setProperty('section', '99')
            self.setProperty('category', '0')
            self.close()
        else:
            if control.getLabel() == '3':
                self.setProperty('section', '3')
                self.setProperty('category', '0')
            else:
                self.setProperty('section', '1')
                self.setProperty('category', control.getLabel())
            self.close()
