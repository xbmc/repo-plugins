'''
Created on 4 jun. 2011

@author: Nick
'''
import xbmc #@UnresolvedImport
import shutil
import os.path

from managers.cache_manager import CacheManager

class TempImageManager(CacheManager):
    
    def __init__(self):
        self.TEMP_DIR = self.CACHE_DIR + "image_temp/"
        self._ensureDir(self.TEMP_DIR)
        
    def storeFile(self, file, filename):
        path = self.TEMP_DIR + os.path.splitext(filename)[0] + "/"
        self._ensureDir(path)
        filepath = path + filename
        self._writeFile(file, filepath)
        return filepath
    
    def clearCache(self):
        shutil.rmtree(xbmc.translatePath(self.TEMP_DIR))