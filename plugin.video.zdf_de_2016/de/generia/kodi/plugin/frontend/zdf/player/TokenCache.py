import os
from datetime import datetime

LOG_PREFIX = '[TokenCache] - '
        

class TokenCache(object):
    storeFile = None
    
    def __init__(self, log, storeFile):
        self.log = log
        self.storeFile = storeFile
        self._checkStorePath()
                    
    def getApiToken(self):
        apiToken = None
        try:
            with open(self.storeFile, "r") as lines:
                for line in lines:
                    apiToken = line.strip()
                    self.log.info(LOG_PREFIX + "loading api-token '{}' from store-file '{}'", apiToken, self.storeFile)
                    break
        except IOError, e:
            self.log.error(LOG_PREFIX + "caught exception while loading api-token using store-file '{}', exception: {}", self.storeFile, e)
            
        return apiToken

    def setApiToken(self, apiToken):
        self.log.info(LOG_PREFIX + "saving api-token '{}' to store-file '{}'", apiToken, self.storeFile)
        try:
            file = open(self.storeFile, "w")
            if apiToken is not None:
                file.write(apiToken)
            file.close()
        except IOError, e:
            self.log.error(LOG_PREFIX + "caught exception while saving api-token using store-file '{}', exception: {}", self.storeFile, e)

    def _checkStorePath(self):
        storeDir = os.path.dirname(self.storeFile)
        if os.path.exists(storeDir):
            return
        try:
            os.makedirs(storeDir)
        except IOError, e:
            self.log.error(LOG_PREFIX + "caught exception while creating store-dir '{}', exception: {}", storeDir, e)
            return
