#!/usr/bin/env python
# -*- coding: utf-8 -*-
########################################
#  Digitally Imported XBMC plugin
#  by Tim C. 'Bitcrusher' Steinmetz
#  http://qualisoft.dk
#  Github: https://github.com/Bitcrusher/Digitally-Imported-XBMC-plugin
#  Git Read-only: git://github.com/Bitcrusher/Digitally-Imported-XBMC-plugin.git
#
#  This Program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2, or (at your option)
#  any later version.
#
#  This Program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with XBMC; see the file COPYING.  If not, write to
#  the Free Software Foundation, 675 Mass Ave, Cambridge, MA 02139, USA.
#  http://www.gnu.org/copyleft/gpl.html
#

import os
import pickle
import sys
import re
import string
import urllib

import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon
import time
from xml.dom import minidom
from httpcomm import HTTPComm
from ConfigParser import SafeConfigParser
import json
from random import randrange
import Queue
import threading

# Import JSON - compatible with Python<v2.6
try:
    import json
except ImportError:
    import simplejson as json


# Config parser
pluginConfig = SafeConfigParser()
pluginConfig.read(os.path.join(os.path.dirname(__file__), "config.ini"))


# Various constants used throughout the script
HANDLE = int(sys.argv[1])
ADDON = xbmcaddon.Addon(id=pluginConfig.get('plugin', 'id'))

# Plugin constants
__plugin__ = ADDON.getAddonInfo('name')
__author__ = "Tim C. Steinmetz"
__url__ = "http://qualisoft.dk/"
__platform__ = "xbmc media center, [LINUX, OS X, WIN32]"
__date__ = pluginConfig.get('plugin', 'date')
__version__ = ADDON.getAddonInfo('version')


"""
 Thread class used for scraping individual playlists for each channel
"""
class scraperThread(threading.Thread):
    def __init__(self, musicObj, channel, channelMeta, channelCount):
        threading.Thread.__init__(self)
        self.musicObj = musicObj
        self.channel = channel
        self.channelMeta = channelMeta
        self.channelCount = channelCount

    def run(self):
        self.musicObj.addChannel(self.channel, self.channelMeta, self.channelCount)


class musicAddonXbmc:
    # settings used for multithreading
    threadMax = 8
    workQueue = Queue.Queue()

    # Resolves path to where plugin settings and cache will be stored
    addonProfilePath = xbmc.translatePath(ADDON.getAddonInfo('profile')).decode('utf-8')

    # Init CURL thingy
    curler = HTTPComm()

    # regex used to find all streams in a .pls
    re_playlistStreams = re.compile("File\d=([^\n]+)\s*Title\d=([^\n]+)", re.M | re.I)

    dictBitrate = [40, 64, 128, 320]

    # list of channels used when caching and retrieving from cache
    channelsList = []

    # unique listenkey if a premium member
    listenKey = ''

    # stores how many new channels/channelart was found
    newChannels = 0

    def __init__(self):
        # If stats is allowed and its been at least 24 hours since last checkin
        #if (ADDON.getSetting('allowstats') == "true") and (
        #        self.checkFileTime(self._checkinFile, self._addonProfilePath, 86400) == True):
        #    open(self._checkinFile, "w")
        #
        #    account = 'public'
        #    if ADDON.getSetting('username') != "":
        #        account = 'premium'
        #
        #    xbmc.log('Submitting stats', xbmc.LOGNOTICE)
        #    self._httpComm.get('http://stats.qualisoft.dk/?plugin=' + ADDON.getAddonInfo(
        #        'id') + '&version=' + __version__ + '&account=' + account + '&key=' + parser.get('plugin',
        #                                                                                         'checkinkey'))
        #
        xbmc.log("[PLUGIN] %s v%s (%s)" % ( __plugin__, __version__, __date__ ), xbmc.LOGNOTICE)


    """
     Let's get some tunes!
    """
    def run(self):
        threads = []

        # check if cache has expired
        if not ADDON.getSetting("forceupdate") == "true" \
                and not int(ADDON.getSetting("cacheexpire_days")) == 0 \
                and self.checkFileTime(pluginConfig.get('cache', 'cacheChannels'),
                                       ADDON.getSetting("cacheexpire_days")):
            ADDON.setSetting(id="forceupdate", value="true")

        if ADDON.getSetting("forceupdate") == "true":
            channels = []
            html = ""

            # if username is set, try to login and go for premium channels
            if ADDON.getSetting('username') != "":
                loginData = urllib.urlencode({'member_session[username]': ADDON.getSetting('username'),
                                              'member_session[password]': ADDON.getSetting('password')})

                # post login info and get frontpage html
                html = self.curler.request(pluginConfig.get('urls', 'login'), 'post', loginData)

                # if we could not reach di.fm at all
                if not bool(html):
                    xbmc.log('di.fm could not be reached', xbmc.LOGWARNING)
                    xbmcgui.Dialog().ok(ADDON.getLocalizedString(30100),
                                        ADDON.getLocalizedString(30101),
                                        ADDON.getLocalizedString(30102),
                                        ADDON.getLocalizedString(30103))
                    xbmcplugin.endOfDirectory(HANDLE, succeeded=True)
                    return True

                channels = json.loads(self.curler.request(pluginConfig.get('streams', 'premium%sk' % self.dictBitrate[int(ADDON.getSetting('bitrate'))]), 'get'))
                channelMeta = self.getChannelMetadata(html)

                premiumConfig = self.getPremiumConfig()

                # if premiumConfig['listenKey'] is blank, we did not log in correctly
                if premiumConfig is False or premiumConfig['listenKey'] == '':
                    xbmc.log('Login did not succeed', xbmc.LOGWARNING)
                    xbmcgui.Dialog().ok(ADDON.getLocalizedString(30170),
                                        ADDON.getLocalizedString(30171),
                                        ADDON.getLocalizedString(30172))
                    xbmcplugin.endOfDirectory(HANDLE, succeeded=True)
                    return True

                # if we should get the favorites or all channels
                if ADDON.getSetting("usefavorites") == 'true':
                    favplaylist = self.curler.request(pluginConfig.get('streams', 'favorites%sk' % self.dictBitrate[int(ADDON.getSetting('bitrate'))]) + '?' + premiumConfig['listenKey'], 'get')

                    channels = self.getFavoriteChannels(channels, favplaylist)
                    if len(channels) == 0:
                        xbmcgui.Dialog().ok(ADDON.getLocalizedString(30180),
                                            ADDON.getLocalizedString(30181),
                                            ADDON.getLocalizedString(30182))
                        xbmcplugin.endOfDirectory(HANDLE, succeeded=True)
                        return True

                # add listenkey to playlist urls
                for channel in channels:
                    channel['playlist'] = '%s?%s' % (channel['playlist'], premiumConfig['listenKey'])

            # go for free/public channels
            else:
                html = self.curler.request(pluginConfig.get('urls', 'frontpage'), 'get')

                # if we could not reach di.fm at all
                if not html:
                    xbmc.log(u'di.fm could not be reached', xbmc.LOGWARNING)
                    xbmcgui.Dialog().ok(ADDON.getLocalizedString(30100),
                                        ADDON.getLocalizedString(30101),
                                        ADDON.getLocalizedString(30102),
                                        ADDON.getLocalizedString(30103))
                    xbmcplugin.endOfDirectory(HANDLE, succeeded=True)
                    return True

                # put each playlist in a worker queue for threading
                channels = json.loads(self.curler.request(pluginConfig.get('streams', 'public'), 'get'))
                channelMeta = self.getChannelMetadata(html)

            for channel in channels:
                self.workQueue.put(channel)

            # starts 8 threads to download streams for each channel
            while not self.workQueue.empty():
                xbmc.log('Worker queue size is %s' % (str(self.workQueue.qsize())), xbmc.LOGNOTICE)

                if threading.activeCount() < self.threadMax and not self.workQueue.empty(): # checks if max threads are started
                    threads.append(scraperThread(self, self.workQueue.get(), channelMeta, len(channels)))
                    threads[-1].start()
                else: # else wait for 0.1 second
                    time.sleep(0.1)

            # wait for all threads to finish before continuing
            for t in threads:
                t.join()

            # Saves channels to cache and reset the "force update" flag
            if len(channels) > 0:
                pickle.dump(self.channelsList, open(os.path.join(self.addonProfilePath, pluginConfig.get('cache', 'cacheChannels')), "w"), protocol=0)
                ADDON.setSetting(id="forceupdate", value="false")

            if self.newChannels > 0:
                xbmcgui.Dialog().ok(ADDON.getLocalizedString(30130),
                                    ADDON.getLocalizedString(30131) + str(self.newChannels) + ADDON.getLocalizedString(30132),
                                    ADDON.getLocalizedString(30133),
                                    ADDON.getLocalizedString(30134))



        # else load channels from cache file
        else:
            self.channelsList = pickle.load(open(os.path.join(self.addonProfilePath, pluginConfig.get('cache', 'cacheChannels')), "r"))

            for channel in self.channelsList:
                self.addItem(channel['name'],
                             channel['streamUrl'],
                             channel['description'],
                             channel['bitrate'],
                             channel['asset'],
                             channel['isNew'],
                             len(self.channelsList))


        # Should channels be sorted A-Z?
        if ADDON.getSetting('sortaz') == "true":
            xbmcplugin.addSortMethod(HANDLE, sortMethod=xbmcplugin.SORT_METHOD_LABEL)

        # tell XMBC there are no more items to list
        xbmcplugin.endOfDirectory(HANDLE, succeeded=True)

        return True

    """
    Gets channel metadata from site html and cleans it up
    """
    def getChannelMetadata(self, html):

        # Will get JSON with all channel metadata
        re_channelMeta = re.compile(r"di.app.start\(({.+(?!\}\)))\)", re.M | re.I)
        
        channelMeta = re_channelMeta.findall(html)[0]

        # removes those pesky \u2019 and what not
        channelMeta = re.sub(r'\\u[\d\w]{4}','', channelMeta)
        # TODO proper handling of \uxxxx characters - en-/decoding issue

        channelMeta = json.loads(channelMeta) # parse the json
        channelMeta_sorted = {}
        for cMeta in channelMeta['channels']: # loop through meta data, using each channel ID as key instead
            channelMeta_sorted[cMeta['key']] = cMeta

        return channelMeta_sorted


    """
     Parses a playlist (if needed) and calls the function that adds it to the GUI
    """
    def addChannel(self, channel, channelMeta, channelCount):
        # set to true if new channelart is downloaded
        isNew = 0

        # if channel asset does not exist, download it
        if not os.path.exists(self.addonProfilePath + str(channel['key']) + '.png'):
            isNew = 1
            self.newChannels += 1
            self.getChannelAsset(str(channel['key']), "http:" + channelMeta[channel['key']]['asset_url'])

        # gets a random stream from the channels playlist if set in config (is on by default)
        if ADDON.getSetting('randomstream') == "true":
            playlist = self.curler.request(channel['playlist'] + self.listenKey, 'get')
            playlistStreams = self.re_playlistStreams.findall(playlist)
            streamUrl = playlistStreams[randrange(len(playlistStreams))][0]
        else:
            streamUrl = channel['playlist'] + self.listenKey

        bitrate = 40

        if ADDON.getSetting('username') != "":
            bitrate = self.dictBitrate[int(ADDON.getSetting('bitrate'))]

        # stores channel in list to be cached later
        co = {'name': channel['name'],
              'streamUrl': streamUrl,
              'description': channelMeta[channel['key']]['description'],
              'bitrate': bitrate,
              'asset': self.addonProfilePath + str(channel['key']) + '.png',
              'isNew': isNew}
        self.channelsList.append(dict(co))

        self.addItem(channel['name'],
                     streamUrl,
                     channelMeta[channel['key']]['description'],
                     bitrate,
                     self.addonProfilePath + str(channel['key']) + '.png',
                     isNew,
                     channelCount)


    """ Returns a bool
     Adds item to the XBMC GUI
    """
    def addItem(self, channelTitle, streamUrl, streamDescription, bitrate, icon, isNewChannel, totalItems):
        # tart it up a bit if it's a new channel
        if isNewChannel:
            li = xbmcgui.ListItem(label="[COLOR FF007EFF]" + channelTitle + "[/COLOR]", thumbnailImage=icon)
            xbmc.log(u"New channel found: %s" % channelTitle.encode('ascii', 'xmlcharrefreplace'), xbmc.LOGERROR)
        else:
            li = xbmcgui.ListItem(label=channelTitle, thumbnailImage=icon)

        # 320kb/sec is MP3
        if bitrate == 320 and ADDON.getSetting('username') != "":
            li.setProperty("mimetype", 'audio/mpeg')
        else:
            li.setProperty("mimetype", 'audio/aac')

        li.setInfo(type="Music", infoLabels={"Genre": channelTitle,
                                             "Comment": streamDescription,
                                             "Size": bitrate * 1024})
        li.setProperty("IsPlayable", "true")

        xbmcplugin.addDirectoryItem(handle=HANDLE, url=streamUrl, listitem=li, isFolder=False, totalItems=totalItems)

        return True


    """ Returns a bool
     Will check if channel asset/art is present in cache - if not, try to download
    """
    def getChannelAsset(self, channelId, assetUrl):
        try:
            data = self.curler.request(assetUrl, 'get')
            filepath = self.addonProfilePath + channelId + '.png'
            open(filepath, 'wb').write(data)
            xbmc.log('Found new channel art for with ID %s' % str(channelId), xbmc.LOGINFO)
        except Exception:
            sys.exc_clear() # Clears all exceptions so the script will continue to run
            xbmcgui.Dialog().ok(ADDON.getLocalizedString(30160), ADDON.getLocalizedString(30161),
                                ADDON.getLocalizedString(30162) + channelId)
            xbmc.log(ADDON.getLocalizedString(30160) + " " + ADDON.getLocalizedString(
                30161) + str(channelId) + " " + ADDON.getLocalizedString(30162) + str(channelId), xbmc.LOGERROR)
            return False

        return True


    """ Return a list containing a dictonary
     Filters out all channels that are not in the favorites list
    """
    def getFavoriteChannels(self, allchannels, favplaylist):
        channels = []
        re_favchannels = re.compile(r"File\d+=.+/([a-zA-Z0-9]+)", re.M | re.I)
        favchannelkeys = re_favchannels.findall(favplaylist)

        # if favorites list is empty, return empty list
        if int(len(favchannelkeys)) == 0:
            return channels

        for fav in favchannelkeys:
            for channel in allchannels:
                if fav == channel['key']:
                    channels.append(dict(channel))
                    break

        return channels


    """ Return a list containing a dictonary or false
     Returns the logged in users premium config
    """
    def getPremiumConfig(self):
        try:
            if ADDON.getSetting("forceupdate") == "true":

                # Login to api.audioaddict.com to retrieve useful data
                # Documentation: http://tobiass.eu/api-doc.html#13

                loginData = urllib.urlencode({'username': ADDON.getSetting('username'),
                                              'password': ADDON.getSetting('password')})
                # Download and save response
                jsonResponse = self.curler.request(pluginConfig.get('urls', 'apiAuthenticate'), 'post', loginData)
                jsonData = json.loads(jsonResponse)
                pickle.dump(jsonData, open(os.path.join(self.addonProfilePath, pluginConfig.get('cache', 'cachePremiumConfig')), "w"), protocol=0)

                # Load needed data into premiumConfig
                premiumConfig = {'listenKey' : jsonData['listen_key']}

            else:
                # Load data from local cache

                jsonData = pickle.load(open(os.path.join(self.addonProfilePath, pluginConfig.get('cache', 'cachePremiumConfig')), "r"))
                premiumConfig = {'listenKey' : jsonData['listen_key']}

            return premiumConfig

        except Exception:
            sys.exc_clear() # Clears all exceptions so the script will continue to run
            return False


    """ Return a bool
     Checks if a file is older than x days
    """
    def checkFileTime(self, filename, days):
        if not os.path.exists(self.addonProfilePath):
            os.makedirs(self.addonProfilePath)
            return True

        daysInSecs = int(days)*60*60*24

        file = os.path.join(self.addonProfilePath, filename)

        # If file exists, check timestamp
        if os.path.exists(file):
            if os.path.getmtime(file) > (time.time() - daysInSecs):
                xbmc.log(u'It has not been %s days since %s was last updated' % (days, file), xbmc.LOGNOTICE)
                return False
            else:
                xbmc.log(u'The cache file %s + has expired' % file, xbmc.LOGNOTICE)
                return True
        # If file does not exist, return true so the file will be created by scraping the page
        else:
            xbmc.log(u'The cache file %s does not exist' % file, xbmc.LOGNOTICE)
            return True


MusicAddonInstance = musicAddonXbmc()
MusicAddonInstance.run()
