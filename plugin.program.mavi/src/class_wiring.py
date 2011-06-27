'''
Created on 3 jun 2011

@author: Nick
'''
from xbmcaddon import Addon
from managers.connection_manager import ConnectionManager
from managers.posts_manager import PostsManager
from managers.cache_manager import CacheManager
from managers.temp_image_manager import TempImageManager

class ClassWiring(object):

    def __call__(self):
        return self
    
    def getConnectionManager(self):
        try: 
            self._connectionManager
        except AttributeError:
            self._connectionManager = ConnectionManager()
            
        return self._connectionManager
    
    def getPostsManager(self):
        try: 
            self._postsManager
        except AttributeError:
            self._postsManager = PostsManager(self.getConnectionManager())
            
        return self._postsManager
    
    def getCacheManager(self):
        try: 
            self._cacheManager
        except AttributeError:
            self._cacheManager = CacheManager()
            
        return self._cacheManager
    
    def getTempImageManager(self):
        try: 
            self._tempImageManager
        except AttributeError:
            self._tempImageManager = TempImageManager()
            
        return self._tempImageManager
    
    def getAddonManager(self):
        try: 
            self._addonManager
        except AttributeError:
            self._addonManager = Addon("plugin.program.mavi")
        
        return self._addonManager