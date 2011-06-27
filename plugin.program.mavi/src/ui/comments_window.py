'''
Created on 5 jun. 2011

@author: Nick
'''
import xbmcgui #@UnresolvedImport
import xbmcplugin #@UnresolvedImport

from base_window import BaseWindow
from class_wiring import ClassWiring

class CommentsWindow(BaseWindow):
    

    def showComments(self, postId):
        postManager = ClassWiring().getPostsManager()
        comments = postManager.getComments(postId)
        
        self._populateList(comments)
 
    def _populateList(self, comments):
        items = list()
        if comments and comments.data:
            for item in comments.data:
                listItem = ("", xbmcgui.ListItem(item.author, item.body))
                items.append(listItem)
                
        xbmcplugin.addDirectoryItems(self._addonHandle, items, len(items))
        
    def _message(self, message):
        dialog = xbmcgui.Dialog()
        dialog.ok("test", message)