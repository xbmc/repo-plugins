'''
Created on 3 jun 2011

@author: Nick
'''
import xbmcgui #@UnresolvedImport
import xbmcplugin #@UnresolvedImport

from class_wiring import ClassWiring
from ui.base_window import BaseWindow
from domain.multi_media_type import MultiMediaType

class MainWindow(BaseWindow):


    def showLatestPosts(self, after):
        subreddit = ClassWiring().getAddonManager().getSetting("subreddit")
        
        postsManager = ClassWiring().getPostsManager();
        posts = postsManager.getPosts(subreddit, after)
        size = len(posts.data)
        
        for item in posts.data:
            type = item.getMultiMediaType()
            if type is MultiMediaType.VIDEO_TYPE:
                self._getVideoListItem(item, size)
            elif type is MultiMediaType.IMAGE_TYPE:
                self._getActionListItem(item, size)
        
        label = ClassWiring().getAddonManager().getLocalizedString(30100)
        
        listItem = xbmcgui.ListItem(label=label)
        url = self._addonPath + "?action=main&id=" + item.kind + "_" + item.id;
        xbmcplugin.addDirectoryItem(self._addonHandle, url, listItem, True, size)
    
    def _setContextMenu(self, listItem, item):
        action = "XBMC.RunPlugin(" + self._addonPath + "?action=comment&id=" + item.id + ")"
        listItem.addContextMenuItems([("Comments", action)], True)
    
    def _getActionListItem(self, item, size):
#        title = "[IMAGE] "
        title = item.title
        listItem = xbmcgui.ListItem(label=title, thumbnailImage=item.thumbnail)
#        self._setContextMenu(listItem, item)

        url = self._addonPath + "?action=image&file=" + item.url;
        
        xbmcplugin.addDirectoryItem(self._addonHandle, url, listItem, False, size)
            
    def _getVideoListItem(self, item, size):
        pass
        #TODO
#        listItem = xbmcgui.ListItem(label = item.title, thumbnailImage = item.thumbnail)
#        self._setContextMenu(listItem, item)
#        
#        id = [part.split('=') for part in item.url.split('&')]
#
##        url = self._addonPath + "?video=youtube&id=" + id[0][1];
#        url = "plugin://plugin.video.youtube/?action=playbyid&videoid=" + id[0][1]

#        xbmcplugin.addDirectoryItem(self._addonHandle, url, listItem, False, size)