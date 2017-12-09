'''
    Copyright (C) 2014-2016 ddurdle

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.


'''

import sys
import cgi
import re





#http://stackoverflow.com/questions/1208916/decoding-html-entities-with-python/1208931#1208931
def _callback(matches):
    id = matches.group(1)
    try:
        return unichr(int(id))
    except:
        return id

def decode(data):
    return re.sub("&#(\d+)(;|(?=\s))", _callback, data).strip()

def getParameter(key,default=''):
    try:
        value = plugin_queries[key]
        if value == 'true':
            return True
        elif value == 'false':
            return False
        else:
            return value
    except:
        return default

def getSetting(key,default=''):
    try:
        value = addon.getSetting(key)
        if value == 'true':
            return True
        elif value == 'false':
            return False
        else:
            return value
    except:
        return default

def getSettingInt(key,default=0):
    try:
        value = addon.getSetting(key)
        if value == '':
            return default
        if value == 'true':
            return True
        elif value == 'false':
            return False
        else:
            return value
    except:
        return default

def parse_query(query):
    queries = {}
    try:
        queries = cgi.parse_qs(query)
    except:
        return
    q = {}
    for key, value in queries.items():
        q[key] = value[0]
    q['mode'] = q.get('mode', 'main')
    return q



plugin_queries = None
try:
    plugin_queries = parse_query(sys.argv[2][1:])
except:
    plugin_queries = None


# global variables
import constants
addon = constants.addon


#
#
#
class settings:
    # Settings

    ##
    ##
    def __init__(self, addon):
        self.addon = addon
        #self.integratedPlayer = self.getSetting('integrated_player', False)
        self.cc = getParameter('cc', self.getSetting('cc', True))
        self.srt = getParameter('srt', self.getSetting('srt', True))
        #self.srt_folder = getParameter('srt_folder', self.getSetting('srt_folder', False))
        self.strm = getParameter('strm', True) ## force to TRUE, set to false manually

        self.username = getParameter('username', '')
        self.setCacheParameters()
        self.promptQuality = getParameter('promptquality', self.getSetting('prompt_quality', True))
        self.parseTV = self.getSetting('parse_tv', True)
        self.parseMusic = self.getSetting('parse_music', True)
        self.skipResume = self.getSetting('video_skip', 0.98)
#        self.cloudResume = self.getSetting('resumepoint', 0)
        self.cloudResumePrompt = self.getSetting('resumeprompt', False)
#        self.cloudSpreadsheet = self.getSetting('library_filename', 'CLOUD_DB')
        self.tv_watch  = self.getSetting('tv_db_watch', False)
        self.movie_watch  = self.getSetting('movie_db_watch', False)
        self.localDB = self.getSetting('local_db', False)

        self.seek = getParameter('seek', 0)
        self.trace = getSetting('trace', False)

        self.photoResolution = int(self.getSettingInt('photo_resolution', 0))
        if self.photoResolution == 0:
            self.photoResolution = 1280
        elif self.photoResolution == 1:
            self.photoResolution = 1920
        elif self.photoResolution == 2:
            self.photoResolution = 3840
        elif self.photoResolution == 3:
            self.photoResolution = 7680
        elif self.photoResolution == 4:
            self.photoResolution = 15360
        elif self.photoResolution == 5:
            self.photoResolution = 720
        else:
            self.photoResolution = 99999


#        self.thumbnailResolution = int(self.getSetting('thumb_resolution', 0))
#        if self.thumbnailResolution == 0:
#            self.thumbnailResolution = 80
#        elif self.thumbnailResolution == 1:
#            self.thumbnailResolution = 120
#        else:
#            self.thumbnailResolution = 200

        self.streamer =  self.getSetting('streamer', True)
        self.streamPort =  int(self.getSettingInt('stream_port', 8011))


        self.encfsDownloadType = int(self.getSettingInt('encfs_download_type', 1))


    def setVideoParameters(self):
        self.resume = getParameter('resume', False)

        self.playOriginal = getParameter('original', self.getSetting('never_stream', False))


    def setCacheParameters(self):
        self.cache = getParameter('cache', False)
#        self.download = self.getSetting('always_cache', getParameter('download', False))
        self.download = getParameter('download', getSetting('always_cache', False))
        self.play = getParameter('play', getSetting('always_cache', False))
        self.cachePath = self.getSetting('cache_folder')
        self.cacheSingle = self.getSetting('cache_single')
        self.cachePercent = self.getSetting('cache_percent', 10)
        self.cacheChunkSize = self.getSetting('chunk_size', 32 * 1024)
        self.cacheContinue = self.getSetting('cache_continue', False)
        self.cacheSRT = self.getSetting('cache_srt', False)
        self.cacheThumbnails = self.getSetting('cache_thumbnails', False)

        if self.cache:
            self.download = False
            self.play = False

    def setEncfsParameters(self):
        self.encfsCacheSingle = self.getSetting('encfs_cache_single')
        self.encfsCachePercent = self.getSetting('encfs_cache_percent', 10)
        self.encfsCacheChunkSize = self.getSetting('encfs_chunk_size', 32 * 1024)
        self.encfsSource = self.getSetting('encfs_source')
        self.encfsTarget = self.getSetting('encfs_target')
        self.encfsContinue = self.getSetting('encfs_continue', False)
        self.encfsStream = self.getSetting('encfs_stream', False)
        self.encfsExp = self.getSetting('encfs_exp', False)

        self.encfsInode = int(self.getSetting('encfs_inode', 0))
        self.encfsLast = self.getSetting('encfs_last', '')

    def setCryptoParameters(self):
        self.cryptoPassword = self.getSetting('crypto_password')
        self.cryptoSalt = self.getSetting('crypto_salt')

    def getParameter(self, key, default=''):
        try:
            value = plugin_queries[key]
            if value == 'true':
                return True
            elif value == 'false':
                return False
            else:
                return value
        except:
            return default

    def getSetting(self, key, default=''):
        try:
            value = self.addon.getSetting(key)
            if value == 'true':
                return True
            elif value == 'false':
                return False
            else:
                return value
        except:
            return default



    def getSettingInt(self, key,default=0):
        try:
            return int(self.addon.getSetting(key))
        except:
            return default

