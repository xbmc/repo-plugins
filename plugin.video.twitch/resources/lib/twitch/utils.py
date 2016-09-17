# -*- coding: utf-8 -*-
import sys
import json
import requests
from base64 import b64decode
from xbmcaddon import Addon
from constants import Keys
from exception import TwitchException

MAX_RETRIES = 5


class JSONScraper(object):
    '''
    Encapsulates execution request and parsing of response
    '''

    def __init__(self, logger):
        object.__init__(self)
        self.logger = logger

    '''
        Download Data from an url and returns it as a String
        @param url Url to download from (e.g. http://www.google.com)
        @param headers currently unused, backwards compatibility
        @returns String of data from URL
    '''

    def downloadWebData(self, url, headers=None):
        for _ in range(MAX_RETRIES):
            try:
                if headers:
                    headers[Keys.USER_AGENT] = Keys.USER_AGENT_STRING
                else:
                    headers = {Keys.USER_AGENT: Keys.USER_AGENT_STRING}

                response = requests.get(url, headers=headers, verify=False)
                data = response.content
                break
            except Exception as err:
                self.logger.debug("Error %s during HTTP Request, retrying", repr(err))
        else:
            raise TwitchException(TwitchException.HTTP_ERROR)
        return data

    '''
        Download Data from an url and returns it as JSON
        @param url Url to download from
        @param headers currently unused, backwards compability
        @returns JSON Object with data from URL
    '''

    def getJson(self, url, headers=None):
        def getClientID():
            # return a Client ID to use for Twitch API
            client_id = Addon().getSetting('oauth_client_id')  # get from settings
            if not client_id:  # not in settings
                try:
                    client_id = b64decode(Keys.CLIENT_ID)  # use Keys.CLIENT_ID
                except:
                    client_id = ''
            return client_id

        if not headers:
            headers = {}
        # Set api version and client id headers
        headers.setdefault(Keys.ACCEPT, Keys.API_VERSION)
        headers.setdefault(Keys.CLIENT_ID_HEADER, getClientID())

        jsonString = self.downloadWebData(url, headers)
        try:
            jsonDict = json.loads(jsonString)
            self.logger.debug(json.dumps(jsonDict, indent=4, sort_keys=True))
            return jsonDict
        except:
            raise TwitchException(TwitchException.JSON_ERROR)


class M3UPlaylist(object):
    def __init__(self, data, qualityList=None):
        self.playlist = dict()
        self.qualityList = qualityList or Keys.QUALITY_LIST_STREAM

        def parseQuality(ExtXMediaLine, ExtXStreamInfLine, Url):
            # find name of current quality, NAME=", 6 chars
            namePosition = ExtXMediaLine.find('NAME')
            if namePosition == -1:
                raise TwitchException(TwitchException.NO_PLAYABLE)
            qualityString = ''
            namePosition += 6
            for char in ExtXMediaLine[namePosition:]:
                if char == '"':
                    break
                qualityString += char
            return qualityString, Url

        lines = data.splitlines()
        linesIterator = iter(lines)
        for line in linesIterator:
            if line.startswith('#EXT-X-MEDIA:TYPE=VIDEO'):
                quality, url = parseQuality(line, next(linesIterator), next(linesIterator))
                qualityInt = self.qualityList.index(quality)
                self.playlist[qualityInt] = url
        if not self.playlist:
            # playlist dict is empty
            raise TwitchException(TwitchException.NO_PLAYABLE)

    # returns selected quality or best match if not available
    def getQuality(self, selectedQuality):
        bestDistance = len(self.qualityList) + 1

        if (selectedQuality in self.playlist.keys()) and (bestDistance == len(Keys.QUALITY_LIST_STREAM) + 1):
            # selected quality is available
            return self.playlist[selectedQuality]
        else:
            # not available, calculate differences to available qualities
            # return lowest difference / lower quality if same distance
            bestDistance = len(self.qualityList) + 1
            # if not using standard list, adjust selected quality to appropriate old quality
            if bestDistance != len(Keys.QUALITY_LIST_STREAM) + 1:
                if selectedQuality <= 2:
                    selectedQuality = 0
                elif selectedQuality <= 4:
                    selectedQuality = 1
                elif selectedQuality <= 6:
                    selectedQuality = 2
                elif selectedQuality <= 7:
                    selectedQuality = 3
                else:
                    selectedQuality = 4
            bestMatch = None

            for quality in sorted(self.playlist, reverse=True):
                newDistance = abs(selectedQuality - quality)
                if newDistance < bestDistance:
                    bestDistance = newDistance
                    bestMatch = quality

            return self.playlist[bestMatch]

    def __str__(self):
        return repr(self.playlist)
