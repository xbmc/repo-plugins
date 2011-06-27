'''
Created on 4 jun. 2011

@author: Nick
'''
import xbmc #@UnresolvedImport
import os.path as Path
import os as OS

class CacheManager:
    """ Handles caching of files """
    
    
    CACHE_DIR = "special://temp/mavi/"

    def __init__(self):
        self._ensureDir(self.CACHE_DIR)

    def _writeFile(self, file, filepath):
        filepath = xbmc.translatePath(filepath)
        out = open(filepath, "wb")
        out.write(file)
        out.close()

    def storeFile(self, file, filename):
        filepath = self.CACHE_DIR + filename
        self._writeFile(file, filepath)
        return filepath
    
    def urlToFilename(self, url):
        return Path.basename(url)

    def _ensureDir(self, dir):
        dir = xbmc.translatePath(dir)
        if not Path.exists(dir):
            OS.makedirs(dir)
    
    def clearCache(self):
        self._clearDir(self.CACHE_DIR)
        
    def _clearDir(self, dirName):
        for name in OS.listdir(dirName):
            file = Path.join(dirName, name)
            if not Path.isdir(file):
                path = xbmc.translatePath(file)
                OS.remove(path)