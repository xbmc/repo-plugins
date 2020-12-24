import os
from datetime import datetime

LOG_PREFIX = '[PlayerStore] - '
        

class PlayerStore(object):
    apiTokenFile = None
    
    def __init__(self, log, apiTokenFile, playlistFile):
        self.log = log
        self.apiTokenFile = apiTokenFile
        self.playlistFile = playlistFile
        self._checkStorePath()
                    
    def getApiToken(self):
        apiToken = None
        try:
            with open(self.apiTokenFile, "r") as lines:
                for line in lines:
                    apiToken = line.strip()
                    self.log.info(LOG_PREFIX + "loading api-token '{}' from store-file '{}'", apiToken, self.apiTokenFile)
                    break
        except IOError as e:
            self.log.error(LOG_PREFIX + "caught exception while loading api-token using store-file '{}', exception: {}", self.apiTokenFile, e)
            
        return apiToken

    def setApiToken(self, apiToken):
        self.log.info(LOG_PREFIX + "saving api-token '{}' to store-file '{}'", apiToken, self.apiTokenFile)
        try:
            file = open(self.apiTokenFile, "w")
            if apiToken is not None:
                file.write(apiToken)
            file.close()
        except IOError as e:
            self.log.error(LOG_PREFIX + "caught exception while saving api-token using store-file '{}', exception: {}", self.apiTokenFile, e)
                    
    def getPlaylistUrl(self):
        
        return self.playlistFile

    def storePlaylist(self, playlist):
        self.log.info(LOG_PREFIX + "saving playlist to store-file '{}'", self.playlistFile)
        try:
            file = open(self.playlistFile, "w")
            file.write(playlist)
            file.close()
        except IOError as e:
            self.log.error(LOG_PREFIX + "caught exception while saving playlist using store-file '{}', exception: {}", self.playlistFile, e)

    def _checkStorePath(self):
        storeDir = os.path.dirname(self.apiTokenFile)
        if os.path.exists(storeDir):
            return
        try:
            os.makedirs(storeDir)
        except IOError as e:
            self.log.error(LOG_PREFIX + "caught exception while creating store-dir '{}', exception: {}", storeDir, e)
            return
