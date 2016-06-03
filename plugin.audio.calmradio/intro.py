import xbmc, xbmcgui
from config import config
from xbmcaddon import Addon

ACTION_PARENT_DIR = 9
ACTION_PREVIOUS_MENU = 10
ADDON = Addon()
ADDON_ID = ADDON.getAddonInfo("id")
ADDON_NAME = ADDON.getAddonInfo("name")

class IntroWindow(xbmcgui.WindowDialog):
    def __init__(self, api):
        self.controls = {
            'buttons': []
        }
        self.api = api
        self.setCoordinateResolution(0) # 1920x1080
        dimentions = {
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
        sub_categories = api.get_subcategories(1)

        # add favorites & atmospheres:
        sub_categories += [
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
        popup = xbmcgui.ControlImage(dimentions['window']['x1'],
                                          dimentions['window']['y1'],
                                          dimentions['window']['x2'] - dimentions['window']['x1'],
                                          dimentions['window']['y2'] - dimentions['window']['y1'],
                                          'special://home/addons/plugin.audio.calmradio/resources/media/000000-0.8.png')
        # sidebar
        sidebar = xbmcgui.ControlImage(dimentions['window']['x1'],
                                       dimentions['window']['y1'],
                                       dimentions['sidebar']['width'],
                                       dimentions['window']['y2'] - dimentions['window']['y1'],
                                       'special://home/addons/plugin.audio.calmradio/resources/media/18B0E2-1.png')
        # logo
        logo = xbmcgui.ControlImage(dimentions['window']['x1'] + 100,
                                    dimentions['window']['y1'] + dimentions['spacing']['normal'],
                                    dimentions['logo']['width'],
                                    dimentions['logo']['height'],
                                    'special://home/addons/plugin.audio.calmradio/icon.png')
        # description
        description1 = xbmcgui.ControlLabel(dimentions['window']['x1'],
                                            dimentions['window']['y1'] + dimentions['logo']['height'] + 40,
                                            dimentions['sidebar']['width'],
                                            dimentions['description']['height'],
                                            ADDON.getLocalizedString(32355),
                                            textColor='aaffffff', alignment=2, font='font12')
        description2 = xbmcgui.ControlLabel(dimentions['window']['x1'],
                                            dimentions['window']['y1'] + dimentions['logo']['height'] + 80,
                                            dimentions['sidebar']['width'],
                                            dimentions['description']['height'],
                                            ADDON.getLocalizedString(32356).encode('utf-8'),
                                            textColor='ffffffff', alignment=2)

        # user account button:
        self.btn_account = xbmcgui.ControlButton(dimentions['window']['x1'] + dimentions['spacing']['normal'],
                                                dimentions['window']['y2'] - (dimentions['spacing']['normal'] +
                                                dimentions['exit']['height']) * 3,
                                                dimentions['sidebar']['width'] - dimentions['spacing']['normal'] * 2,
                                                dimentions['exit']['height'],
                                                ADDON.getLocalizedString(32350),
                                                alignment=2,
                                                noFocusTexture='special://home/addons/plugin.audio.calmradio/resources/media/FFFFFF-0.2.png',
                                                focusTexture='special://home/addons/plugin.audio.calmradio/resources/media/FFFFFF-0.4.png')

        # exit button:
        self.btn_my_channels = xbmcgui.ControlButton(dimentions['window']['x1'] + dimentions['spacing']['normal'],
                                                dimentions['window']['y2'] - (dimentions['spacing']['normal'] +
                                                dimentions['exit']['height']) * 2,
                                                dimentions['sidebar']['width'] - dimentions['spacing']['normal'] * 2,
                                                dimentions['exit']['height'],
                                                ADDON.getLocalizedString(32351),
                                                alignment=2,
                                                noFocusTexture='special://home/addons/plugin.audio.calmradio/resources/media/FFFFFF-0.2.png',
                                                focusTexture='special://home/addons/plugin.audio.calmradio/resources/media/FFFFFF-0.4.png')

        # exit button:
        self.btn_exit = xbmcgui.ControlButton(dimentions['window']['x1'] + dimentions['spacing']['normal'],
                                              dimentions['window']['y2'] - dimentions['spacing']['normal'] -
                                                dimentions['exit']['height'],
                                              dimentions['sidebar']['width'] - dimentions['spacing']['normal'] * 2,
                                              dimentions['exit']['height'],
                                              ADDON.getLocalizedString(32352),
                                              alignment=2,
                                              focusTexture='special://home/addons/plugin.audio.calmradio/resources/media/FFFFFF-0.4.png')

        # add ui controls:
        self.addControls((overlay, popup, sidebar, logo, description1, description2,
                          self.btn_exit, self.btn_account, self.btn_my_channels))

        # add categories:
        for idx, item in enumerate(sub_categories):
            x = dimentions['window']['x1'] + dimentions['sidebar']['width'] + dimentions['spacing']['normal'] + \
                ((idx % dimentions['thumbnail']['per_row']) * (dimentions['thumbnail']['width'] + dimentions['spacing']['normal']))
            y = dimentions['window']['y1'] + dimentions['spacing']['normal'] + \
                ((idx / dimentions['thumbnail']['per_row']) * (dimentions['thumbnail']['height'] + dimentions['spacing']['normal']))
            # button:
            button = xbmcgui.ControlButton(x - 3,
                                           y - 3,
                                           dimentions['thumbnail']['width'] + 6,
                                           dimentions['thumbnail']['height'] + 6,
                                           str(item['id']),
                                           noFocusTexture='special://home/addons/plugin.audio.calmradio/resources/media/0D5C77-1.png',
                                           focusTexture='special://home/addons/plugin.audio.calmradio/resources/media/18B0E2-1.png')
            self.controls['buttons'].append(button)
            self.addControl(button)
            # thumbnail:
            self.addControl(xbmcgui.ControlImage(x,
                                                 y,
                                                 dimentions['thumbnail']['width'],
                                                 dimentions['thumbnail']['height'],
                                                 '{0}{1}'.format('' if item['id'] == 3 or item['id'] == 99 else
                                                                 config['urls']['calm_arts_host'], item['image'])))
            # caption background:
            self.addControl(xbmcgui.ControlImage(x,
                                                 y + dimentions['thumbnail']['height'] - dimentions['caption']['height'],
                                                 dimentions['thumbnail']['width'],
                                                 dimentions['caption']['height'],
                                                 'special://home/addons/plugin.audio.calmradio/resources/media/000000-0.8.png'))
            # caption label:
            self.addControl(xbmcgui.ControlLabel(x,
                                                 y + dimentions['thumbnail']['height'] - dimentions['caption']['height'],
                                                 dimentions['thumbnail']['width'],
                                                 dimentions['caption']['height'],
                                                 item['name'].capitalize(),
                                                 font='font12',
                                                 alignment=6))


        # set navigation:
        for idx, button in enumerate(self.controls['buttons']):
            button.setNavigation(left=self.controls['buttons'][idx - 1] if idx > 0 else button,
                                 right=self.controls['buttons'][idx + 1] if (idx + 1) < len(self.controls['buttons']) else button,
                                 up=self.controls['buttons'][idx - dimentions['thumbnail']['per_row']]
                                    if idx - dimentions['thumbnail']['per_row'] >= 0 else button,
                                 down=self.controls['buttons'][idx + dimentions['thumbnail']['per_row']]
                                    if idx + dimentions['thumbnail']['per_row'] < len(self.controls['buttons']) else button)
        self.controls['buttons'][0].controlLeft(self.btn_account)
        self.controls['buttons'][len(self.controls['buttons']) - 1].controlRight(self.controls['buttons'][0])

        # side bar navigation:
        self.btn_account.setNavigation(self.controls['buttons'][0], self.btn_my_channels, self.controls['buttons'][0], self.controls['buttons'][0])
        self.btn_my_channels.setNavigation(self.btn_account, self.btn_exit, self.controls['buttons'][0], self.controls['buttons'][0])
        self.btn_exit.setNavigation(self.btn_my_channels, self.controls['buttons'][0], self.controls['buttons'][0], self.controls['buttons'][0])
        # focus on first button:
        self.setFocus(self.controls['buttons'][0])

    def onAction(self, action):
        if action == ACTION_PREVIOUS_MENU or action == ACTION_PARENT_DIR:
            self.close()

    def onControl(self, control):
        if control == self.btn_exit:
            self.close()
        elif control == self.btn_account:
            xbmc.executebuiltin('Addon.OpenSettings({0})'.format(ADDON_ID))
        elif control == self.btn_my_channels:
            self.setProperty('category', '99')
            self.setProperty('sub_category', '0')
            self.close()
        else:
            if control.getLabel() == '3':
                self.setProperty('category', '3')
                self.setProperty('sub_category', '0')
            else:
                self.setProperty('category', '1')
                self.setProperty('sub_category', control.getLabel())
            self.close()
