import xbmcgui
from xbmc import log
from xbmcaddon import Addon
from xbmc import Player
from api import API
from config import config

ADDON = Addon()
api = API()

ADDON_ID = ADDON.getAddonInfo('id')
ADDON_NAME = ADDON.getAddonInfo('name')


class PlayerWindow(xbmcgui.WindowDialog):
    def __init__(self):
        log('100FM player init')
        # ADDON.setSetting('page', '0')
        # ADDON.setSetting('channel', '0')
        self.data = api.get_all_channels()
        self.setCoordinateResolution(0)  # 1920x1080
        self.controls = {
            'buttons': []
        }

        # background
        overlay = xbmcgui.ControlImage(0, 0, 1920, 1080,
                                       'special://home/addons/{0}/fanart.jpg'.format(ADDON_ID))
        # top bar + shadow
        topbar = xbmcgui.ControlImage(0, 0, 1920, 290,
                                      'special://home/addons/{0}/resources/media/132f54.png'.format(ADDON_ID))
        topbar_shadow = xbmcgui.ControlImage(0, 290, 1920, 20,
                                             'special://home/addons/{0}/resources/media/shadow.png'.format(ADDON_ID))
        # equalizer
        eq = xbmcgui.ControlImage(0, 0, 1920, 290,
                                  'special://home/addons/{0}/resources/media/eq.png'.format(ADDON_ID))
        # logo text
        logo_text = xbmcgui.ControlLabel(40, 50, 300, 30, '[B]{0}[/B]'.format(ADDON.getLocalizedString(32010)),
                                         textColor='0xffF8F301')
        # logo
        logo = xbmcgui.ControlImage(50, 100, 260, 86,
                                    'special://home/addons/{0}/resources/media/100fm.png'.format(ADDON_ID))
        # pause
        self.pause = xbmcgui.ControlButton(360, 100, 90, 90, '',
                                           focusTexture='special://home/addons/{0}/resources/media/pause-hover.png'.format(
                                               ADDON_ID),
                                           noFocusTexture='special://home/addons/{0}/resources/media/pause.png'.format(
                                               ADDON_ID))
        # play
        self.play = xbmcgui.ControlButton(360, 100, 90, 90, '',
                                          focusTexture='special://home/addons/{0}/resources/media/play-hover.png'.format(
                                              ADDON_ID),
                                          noFocusTexture='special://home/addons/{0}/resources/media/play.png'.format(
                                              ADDON_ID))
        # now playing
        now_playing = xbmcgui.ControlLabel(500, 60, 300, 30, '[I]{0}[/I]'.format(ADDON.getLocalizedString(32011)),
                                           textColor='0xffF8F301')

        # current track:
        # self.current = xbmcgui.ControlImage(0, 0,
        #                                config['list']['thumbnail']['width'] + 8,
        #                                config['list']['thumbnail']['height'] + 8,
        #                                'special://home/addons/{0}/resources/media/f8f301.png'.format(ADDON_ID))

        # song title
        self.song = xbmcgui.ControlLabel(500, 100, 800, 30, '[B]Song Name[/B]',
                                         textColor='0xffFFFFFF')
        # artist name
        self.artist = xbmcgui.ControlLabel(500, 150, 800, 30, 'Artist',
                                           textColor='0xffCCCCCC')

        # time
        time = xbmcgui.ControlLabel(1668, 20, 800, 30, '$INFO[Player.Duration]',
                                    textColor='0xffBBBBBB')

        # channel name
        # self.channel_name = xbmcgui.ControlLabel(0, 320, 1920, 40, '', textColor='0xff132f54', alignment=2)

        # description
        # self.description = xbmcgui.ControlLabel(-400, 350, 2320, 30, '', textColor='0xff132f54', alignment=2)

        # record
        record = xbmcgui.ControlImage(1540, -70, 322, 340,
                                      'special://home/addons/{0}/resources/media/record.png'.format(ADDON_ID))
        # pointer
        pointer = xbmcgui.ControlImage(1880, 20, 30, 200,
                                       'special://home/addons/{0}/resources/media/pointer.png'.format(ADDON_ID))
        # channel name
        self.channel = xbmcgui.ControlImage(1640, 60, 120, 50, '')
        # slogan
        slogan = xbmcgui.ControlImage(1610, 125, 180, 40,
                                      'special://home/addons/{0}/resources/media/100-music.png'.format(ADDON_ID))

        # pagination
        self.prev = xbmcgui.ControlButton(50, config['list']['y'] + 220,
                                          config['list']['pagination']['width'],
                                          config['list']['pagination']['height'], '',
                                          focusTexture='special://home/addons/{0}/resources/media/prev-hover.png'.format(
                                              ADDON_ID),
                                          noFocusTexture='special://home/addons/{0}/resources/media/prev.png'.format(
                                              ADDON_ID)
                                          )
        self.next = xbmcgui.ControlButton(1750, config['list']['y'] + 220, config['list']['pagination']['width'],
                                          config['list']['pagination']['height'], '',
                                          focusTexture='special://home/addons/{0}/resources/media/next-hover.png'.format(
                                              ADDON_ID),
                                          noFocusTexture='special://home/addons/{0}/resources/media/next.png'.format(
                                              ADDON_ID)
                                          )

        # # volume
        # self.volume = xbmcgui.ControlSlider(105, 240, 165, 20)
        # # volume icons:
        # volume_off = xbmcgui.ControlImage(70, 244, 20, 20,
        #                                   'special://home/addons/{0}/resources/media/volume-off.png'.format(ADDON_ID))
        # volume_up = xbmcgui.ControlImage(285, 244, 20, 20,
        #                                   'special://home/addons/{0}/resources/media/volume-up.png'.format(ADDON_ID))

        # add all controls:
        self.addControls((overlay, topbar, topbar_shadow, eq, logo, logo_text, self.pause, self.play, time,
                          # self.description, self.channel_name,
                          now_playing, record, pointer, self.song, self.artist, self.channel, slogan,
                          self.prev, self.next))

        self.draw_channels()

        # set visibility:
        self.play.setVisibleCondition('[!Player.Playing]', True)
        self.pause.setVisibleCondition('[Player.Playing]', True)

        # set animations:
        pointer.setAnimations([('Conditional', 'effect=rotate end=-30 time=2000 center=1880,0 reversible=true \
            condition=Player.Playing')])
        record.setAnimations([('Conditional', 'effect=rotate end=359 time=3000 center=1700,100 loop=True \
            condition=Player.Playing')])
        # self.description.setAnimations([('WindowOpen', 'effect=zoom end=70 center=1400,350')])
        now_playing.setAnimations([('WindowOpen', 'effect=zoom end=70')])
        time.setAnimations([('WindowOpen', 'effect=zoom end=70')])
        self.song.setAnimations([('WindowOpen', 'effect=zoom end=130')])

        # draw previously selected channels and update pagination controls:
        self.update_channel()
        self.update_pagination()
        for idx, button in enumerate(self.controls['buttons']):
            if button.getLabel() == ADDON.getSetting('channel'):
                self.setFocus(button)

    def onAction(self, action):
        if action == xbmcgui.ACTION_BACKSPACE or action == xbmcgui.ACTION_PARENT_DIR or \
                        action == xbmcgui.ACTION_PREVIOUS_MENU or action == xbmcgui.ACTION_NAV_BACK:
            self.close()

    def onControl(self, control):
        if control == self.pause:
            Player().pause()
        elif control == self.play:
            Player().pause()
        elif control == self.next:
            page = int(ADDON.getSetting('page'))
            if page < len(self.data) / config['list']['per_page']:
                ADDON.setSetting('page', str(page + 1))
                self.draw_channels()
                self.update_pagination()
                self.setFocus(self.controls['buttons'][0])
        elif control == self.prev:
            page = int(ADDON.getSetting('page'))
            if page > 0:
                ADDON.setSetting('page', str(page - 1))
                self.draw_channels()
                self.update_pagination()
                self.setFocus(self.controls['buttons'][len(self.controls['buttons']) - 1])
        else:
            ADDON.setSetting('channel', control.getLabel())
            ADDON.setSetting('current', self.data[int(ADDON.getSetting('channel'))]['meta'])
            self.setProperty('current', self.data[int(ADDON.getSetting('channel'))]['meta'])
            Player().play(self.data[int(ADDON.getSetting('channel'))]['stream'])
            self.update_channel()

    def update_channel(self):
        channel = int(ADDON.getSetting('channel'))
        self.channel.setImage(self.data[channel]['label'])
        # self.channel_name.setLabel('[B]{0}[/B]'.format(self.data[channel]['name']))
        # self.description.setLabel(self.data[channel]['description'].replace('\\n', ' ').replace('\\"', '"'))
        self.setProperty('current', self.data[channel]['meta'])
        # current_channel_position = self.controls['buttons'][channel].getPosition()
        # self.current.setPosition(current_channel_position[0], current_channel_position[1])

    def update_pagination(self):
        page = int(ADDON.getSetting('page'))
        if page == 0:
            self.prev.setVisible(False)
        else:
            self.prev.setVisible(True)

        if page == len(self.data) / config['list']['per_page']:
            self.next.setVisible(False)
        else:
            self.next.setVisible(True)

    def draw_channels(self):
        self.removeControls(self.controls['buttons'])
        self.controls['buttons'] = []
        # add channels:
        for idx, item in enumerate(self.data[0 + config['list']['per_page'] * int(ADDON.getSetting('page')):
                config['list']['per_page'] + config['list']['per_page'] * int(ADDON.getSetting('page'))]):
            x = config['list']['x'] + \
                ((idx % config['list']['per_row']) * (
                    config['list']['thumbnail']['width'] + config['list']['margin']))
            y = config['list']['y'] + \
                ((idx / config['list']['per_row']) * (
                    config['list']['thumbnail']['height'] + config['list']['margin']
                ))
            # button:
            button = xbmcgui.ControlButton(x - 4,
                                           y - 4,
                                           config['list']['thumbnail']['width'] + 8,
                                           config['list']['thumbnail']['height'] + 8,
                                           str(idx + config['list']['per_page'] * int(ADDON.getSetting('page'))),
                                           noFocusTexture='special://home/addons/{0}/resources/media/transparent.png'.format(
                                               ADDON_ID),
                                           focusTexture='special://home/addons/{0}/resources/media/f8f301.png'.format(
                                               ADDON_ID))
            self.controls['buttons'].append(button)
            self.addControl(button)
            # thumbnail:
            self.addControl(xbmcgui.ControlImage(x,
                                                 y,
                                                 config['list']['thumbnail']['width'],
                                                 config['list']['thumbnail']['height'],
                                                 item['thumbnail']))
            # caption background:
            self.addControl(
                xbmcgui.ControlImage(x + (config['list']['thumbnail']['width'] - config['list']['label']['width']) / 2,
                                     y + (config['list']['thumbnail']['height'] - config['list']['label'][
                                         'height']) / 2,
                                     config['list']['label']['width'],
                                     config['list']['label']['height'],
                                     item['label']))
        # placeholders
        for idx in range(len(self.controls['buttons']), config['list']['per_page']):
            x = config['list']['x'] + \
                ((idx % config['list']['per_row']) * (
                    config['list']['thumbnail']['width'] + config['list']['margin']))
            y = config['list']['y'] + \
                ((idx / config['list']['per_row']) * (
                    config['list']['thumbnail']['height'] + config['list']['margin']
                ))
            self.addControl(xbmcgui.ControlImage(x,
                                                 y,
                                                 config['list']['thumbnail']['width'],
                                                 config['list']['thumbnail']['height'],
                                                 'special://home/addons/{0}/resources/media/cccccc.png'.format(
                                                     ADDON_ID)))

        # set navigation:
        for idx, button in enumerate(self.controls['buttons']):
            button.setNavigation(left=self.controls['buttons'][idx - 1] if idx > 0 else button,
                                 right=self.controls['buttons'][idx + 1] if (idx + 1) < len(
                                     self.controls['buttons']) else button,
                                 up=self.controls['buttons'][idx - config['list']['per_row']]
                                 if idx - config['list']['per_row'] >= 0 else button,
                                 down=self.controls['buttons'][idx + config['list']['per_row']]
                                 if idx + config['list']['per_row'] < len(self.controls['buttons']) else button)
        self.controls['buttons'][0].controlLeft(self.prev)
        self.controls['buttons'][len(self.controls['buttons']) - 1].controlRight(self.next)
        # set pagination navigation:
        self.next.controlLeft(self.controls['buttons'][len(self.controls['buttons']) - 1])
        self.prev.controlRight(self.controls['buttons'][0])
