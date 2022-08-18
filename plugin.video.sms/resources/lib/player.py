"""
    Copyright (C) 2020 Scott Ware
    This file is part of Scoot Media Streamer (plugin.video.sms)
    SPDX-License-Identifier: GPL-3.0-only
    See LICENSE.txt for more information
"""

import xbmc

class SMSPlayer(xbmc.Player):
    ended = False

    def __init__(self, *args):
        xbmc.Player.__init__(self)
        
    def onPlayBackEnded(self):
        self.ended = True

    def onPlayBackStopped(self):
        self.ended = True

def monitorPlayback(url, addonUrl):
    monitor = xbmc.Monitor()
    player = SMSPlayer()

    xbmc.log(msg='URL: ' + url, level=xbmc.LOGDEBUG);
    xbmc.log(msg='Addon URL: ' + addonUrl, level=xbmc.LOGDEBUG);

    count = 0
    currentFile = None
    playbackStarted = False

    while not monitor.abortRequested():
        if xbmc.Player().isPlaying():
            currentFile = xbmc.Player().getPlayingFile()
            
            xbmc.log(msg='Current File: ' + currentFile, level=xbmc.LOGDEBUG);

            if (currentFile == url) or (currentFile == addonUrl):
                playbackStarted = True
            else:
                if playbackStarted:
                    return
                
                count = count + 1

        if player.ended:
            return

        if count > 4:
            return

        if monitor.waitForAbort(5):
            return
