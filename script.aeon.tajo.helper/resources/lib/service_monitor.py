#!/usr/bin/python
# coding: utf-8

########################

import xbmc
import xbmcgui
import random
import os
import time

from resources.lib.helper import *
from resources.lib.player_monitor import PlayerMonitor
from resources.lib.extras_cache import scan_library, scan_music_library

########################

NOTIFICATION_METHOD = ['VideoLibrary.OnUpdate',
                       'VideoLibrary.OnScanFinished',
                       'VideoLibrary.OnCleanFinished',
                       'AudioLibrary.OnUpdate',
                       'AudioLibrary.OnScanFinished'
                       ]

########################

class Service(xbmc.Monitor):
    def __init__(self):
        self.player_monitor = False
        self.restart = False
        self.screensaver = False
        self.service_enabled = ADDON.getSettingBool('service')

        if self.service_enabled:
            self.start()
        else:
            self.keep_alive()

    def onNotification(self,sender,method,data):
        if ADDON_ID in sender and 'restart' in method:
            self.restart = True

        if method in NOTIFICATION_METHOD:
            sync_library_tags()

            if method.endswith('Finished'):
                reload_widgets(instant=True, reason=method)

                ''' Scan for extras folders and theme files after video library update
                '''
                if method == 'VideoLibrary.OnScanFinished':
                    scan_library()

                ''' Scan for music extras folders after audio library update
                '''
                if method == 'AudioLibrary.OnScanFinished':
                    scan_music_library()
            else:
                reload_widgets(reason=method)

    def onSettingsChanged(self):
        if condition('!IsEmpty(Window(Home).Property(reset_scan_running))'):
            return
        log('Service: Addon setting changed', force=True)
        self.restart = True

    def onScreensaverActivated(self):
        self.screensaver = True

    def onScreensaverDeactivated(self):
        self.screensaver = False

    def stop(self):
        if self.service_enabled:
            del self.player_monitor
            log('Service: Player monitor stopped', force=True)
            log('Service: Stopped', force=True)

        if self.restart:
            log('Service: Applying changes', force=True)
            xbmc.sleep(500) # Give Kodi time to set possible changed skin settings. Just to be sure to bypass race conditions on slower systems.
            DIALOG.notification(ADDON_ID, ADDON.getLocalizedString(32006))
            self.__init__()

    def keep_alive(self):
        log('Service: Disabled', force=True)

        while not self.abortRequested() and not self.restart:
            self.waitForAbort(5)

        self.stop()

    def start(self):
        log('Service: Started', force=True)

        self.player_monitor = PlayerMonitor()

        try:
            service_interval = float(xbmc.getInfoLabel('Skin.String(ServiceInterval)') or ADDON.getSetting('service_interval') or 0.5)
        except (ValueError, TypeError):
            service_interval = 0.5
        try:
            background_interval = int(xbmc.getInfoLabel('Skin.String(BackgroundInterval)') or ADDON.getSetting('background_interval') or 10)
        except (ValueError, TypeError):
            background_interval = 10
        widget_refresh = 0
        get_backgrounds = 200

        while not self.abortRequested() and not self.restart:

            ''' Only run timed tasks if screensaver is inactive to avoid keeping NAS/servers awake
            '''
            if not self.screensaver:

                ''' Grab fanarts
                '''
                if get_backgrounds >= 200:
                    log('Start new fanart grabber process')
                    arts = self.grabfanart()
                    get_backgrounds = 0

                else:
                    get_backgrounds += service_interval

                ''' Set background properties
                '''
                if background_interval >= 10:
                    if arts.get('all'):
                        self.setfanart('AeonTajoBackground', arts['all'])
                    if arts.get('videos'):
                        self.setfanart('AeonTajoBackgroundVideos', arts['videos'])
                    if arts.get('music'):
                        self.setfanart('AeonTajoBackgroundMusic', arts['music'])
                    if arts.get('movies'):
                        self.setfanart('AeonTajoBackgroundMovies', arts['movies'])
                    if arts.get('tvshows'):
                        self.setfanart('AeonTajoBackgroundTVShows', arts['tvshows'])
                    if arts.get('musicvideos'):
                        self.setfanart('AeonTajoBackgroundMusicVideos', arts['musicvideos'])
                    if arts.get('artists'):
                        self.setfanart('AeonTajoBackgroundMusic', arts['artists'])

                    background_interval = 0

                else:
                    background_interval += service_interval

                ''' Refresh widgets
                '''
                if widget_refresh >= 600:
                    reload_widgets(instant=True)
                    widget_refresh = 0

                else:
                    widget_refresh += service_interval

            self.waitForAbort(service_interval)

        self.stop()

    def grabfanart(self):
        arts = {}
        arts['movies'] = []
        arts['tvshows'] = []
        arts['musicvideos'] = []
        arts['artists'] = []
        arts['all'] = []
        arts['videos'] = []

        for item in ['movies', 'tvshows', 'artists', 'musicvideos']:
            dbtype = 'Video' if item != 'artists' else 'Audio'
            query = json_call('%sLibrary.Get%s' % (dbtype, item),
                              properties=['art'],
                              sort={'method': 'random'}, limit=40
                              )

            try:
                for result in query['result'][item]:
                    if result['art'].get('fanart'):
                        data = {'title': result.get('label', '')}
                        data.update(result['art'])
                        arts[item].append(data)

            except KeyError:
                pass

        arts['videos'] = arts['movies'] + arts['tvshows']

        for cat in arts:
            if arts[cat]:
                arts['all'] = arts['all'] + arts[cat]

        return arts

    def setfanart(self,key,items):
        arts = random.choice(items)
        winprop(key, arts.get('fanart', ''))
        for item in ['clearlogo', 'landscape', 'banner', 'poster', 'discart', 'title']:
            winprop('%s.%s' % (key, item), arts.get(item, ''))
