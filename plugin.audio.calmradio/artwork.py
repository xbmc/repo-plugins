import xbmcgui
from xbmc import executebuiltin, log
from xbmcaddon import Addon

ADDON = Addon()


# ADDON_ID = ADDON.getAddonInfo('id')
# ADDON_NAME = ADDON.getAddonInfo('name')


class ArtworkWindow(xbmcgui.WindowDialog):
    def __init__(self):
        self.setCoordinateResolution(0)  # 1920x1080

        # overlay
        self.overlay = xbmcgui.ControlImage(0, 0, 1920, 1080,
                                            'special://home/addons/plugin.audio.calmradio/resources/media/000000-0.8.png')

        # top bar
        topbar = xbmcgui.ControlImage(0, 0, 1920, 100,
                                      'http://imagen.nirelbaz.com/?size=1x1&hexa=18b0e244'
                                      )

        # calm radio - label
        calmradio = xbmcgui.ControlImage(30, 10, 340, 80,
                                         'special://home/addons/plugin.audio.calmradio/resources/media/calmradio-w.png')
        # channel name
        self.channel = xbmcgui.ControlLabel(810, 160, 1060, 30, 'Channel Name', textColor='0xff18b0e2')

        # channel description
        self.description = xbmcgui.ControlTextBox(810, 200, 1060, 800, 'Channel Description')

        # recent songs
        # recent = xbmcgui.ControlLabel(840, 730, 950, 30, '[B]Recent Songs:[/B]')
        # self.recent_1 = xbmcgui.ControlLabel(840, 860, 950, 30, 'Song 1')
        # self.recent_2 = xbmcgui.ControlLabel(840, 890, 950, 30, 'Song 2')
        # self.recent_3 = xbmcgui.ControlLabel(840, 920, 950, 30, 'Song 3')

        self.btn_volume = xbmcgui.ControlButton(1760, 20, 60, 60, '',
                                                focusTexture='special://home/addons/plugin.audio.calmradio/resources/media/volume.png',
                                                noFocusTexture='special://home/addons/plugin.audio.calmradio/resources/media/volume.png'
                                                )

        self.btn_mute = xbmcgui.ControlButton(1760, 20, 60, 60, '',
                                              focusTexture='special://home/addons/plugin.audio.calmradio/resources/media/mute.png',
                                              noFocusTexture='special://home/addons/plugin.audio.calmradio/resources/media/mute.png'
                                              )


        # self.btn_timer = xbmcgui.ControlButton(1760, 20, 60, 60, '',
        #                                        focusTexture='special://home/addons/plugin.audio.calmradio/resources/media/timer.png',
        #                                        noFocusTexture='special://home/addons/plugin.audio.calmradio/resources/media/timer.png'
        #                                        )

        # self.btn_cancel_timer = xbmcgui.ControlButton(1760, 20, 60, 60, '',
        #                                               focusTexture='special://home/addons/plugin.audio.calmradio/resources/media/cancel-timer.png',
        #                                               noFocusTexture='special://home/addons/plugin.audio.calmradio/resources/media/cancel-timer.png'
        #                                               )

        self.btn_close = xbmcgui.ControlButton(1830, 20, 60, 60, '',
                                               focusTexture='special://home/addons/plugin.audio.calmradio/resources/media/close.png',
                                               noFocusTexture='special://home/addons/plugin.audio.calmradio/resources/media/close.png'
                                               )

        # shadow
        cover_shadow = xbmcgui.ControlImage(30, 140, 740, 900,
                                            'special://home/addons/plugin.audio.calmradio/resources/media/box-shadow.png'
                                            )

        spinner = xbmcgui.ControlImage(400, 520, 54, 55,
                                       'special://home/addons/plugin.audio.calmradio/resources/media/spinner.gif'
                                       )

        # album art
        self.cover = xbmcgui.ControlImage(50, 160, 700, 720,
                                          ''
                                          )

        # song name
        self.song = xbmcgui.ControlLabel(70, 890, 660, 30, 'Song Name', textColor='0xff18b0e2')

        # album title
        self.album = xbmcgui.ControlLabel(70, 940, 660, 30, 'Album Title', font='font12')

        # artist
        self.artist = xbmcgui.ControlLabel(70, 975, 660, 30, 'Artist Name', font='font12')
        # add all controls:
        self.addControls((self.overlay, topbar, calmradio, self.channel, self.description,
                          # recent, self.recent_1, self.recent_2, self.recent_3,
                          self.btn_mute, self.btn_volume, self.btn_close,
                          cover_shadow, spinner, self.cover, self.song, self.album, self.artist))

        # set navigation:
        self.btn_mute.setNavigation(self.btn_mute, self.btn_mute, self.btn_close, self.btn_close)
        self.btn_volume.setNavigation(self.btn_volume, self.btn_volume, self.btn_close, self.btn_close)
        self.btn_close.setNavigation(self.btn_close, self.btn_close, self.btn_mute, self.btn_mute)

        # set animations:
        self.channel.setAnimations([('WindowOpen', 'effect=zoom end=110')])
        self.artist.setAnimations([('WindowOpen', 'effect=zoom end=90')])
        self.album.setAnimations([('WindowOpen', 'effect=zoom end=90')])
        self.btn_volume.setAnimations([('Unfocus', 'effect=fade start=100 end=40 time=300')])
        self.btn_mute.setAnimations([('Unfocus', 'effect=fade start=100 end=40 time=300')])
        # self.btn_timer.setAnimations([('Unfocus', 'effect=fade start=100 end=40 time=300')])
        # self.btn_cancel_timer.setAnimations([('Unfocus', 'effect=fade start=100 end=40 time=300')])
        self.btn_close.setAnimations([('Unfocus', 'effect=fade start=100 end=40 time=300')])

        # set visibility conditions:
        self.btn_volume.setVisibleCondition('[!Player.Muted]', False)
        self.btn_mute.setVisibleCondition('[Player.Muted]', False)
        # self.btn_cancel_timer.setVisibleCondition('[!Control.IsVisible({0})]'
        #                                           .format(self.btn_timer.getId()), False)

        self.setFocus(self.btn_mute)

    def onAction(self, action):
        if action == xbmcgui.ACTION_BACKSPACE or action == xbmcgui.ACTION_PARENT_DIR or \
                        action == xbmcgui.ACTION_PREVIOUS_MENU or action == xbmcgui.ACTION_NAV_BACK:
            self.close()

    def onControl(self, control):
        if control == self.btn_mute or control == self.btn_volume:
            executebuiltin('Mute')

        # elif control == self.btn_timer:
        #     executebuiltin('AlarmClock(CalmSleepTimer, PlayerControl(Stop))')
        #     self.btn_timer.setVisible(False)

        # elif control == self.btn_cancel_timer:
        #     executebuiltin('CancelAlarm(CalmSleepTimer)')
        #     self.btn_timer.setVisible(True)

        elif control == self.btn_close:
            executebuiltin('PlayerControl(Stop)')
            self.close()
