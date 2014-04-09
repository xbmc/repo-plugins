# -*- coding: utf-8 -*-
import sys
import os
import re
import time
import random
import urllib

if sys.version_info >=  (2, 7):
    import json as _json
else:
    import simplejson as _json 
    

import xbmcplugin
import xbmcgui
import xbmc

import mycgi
import utils

from loggingexception import LoggingException
from provider import Provider
from BeautifulSoup import BeautifulSoup


urlRoot = u"http://www.vineroulette.com"

class VineProvider(Provider):

    def GetProviderId(self):
        return u"Vine"

    def ExecuteCommand(self, mycgi):
        return super(VineProvider, self).ExecuteCommand(mycgi)
    
    def GetHeaders(self):
        headers = {
                   u'DNT' : u'1'
                   }
        return headers

    def GetWarningFile(self):
        return os.path.join( sys.modules[u"__main__"].DATA_FOLDER, 'warning_shown')

    def ShowRootMenu(self):
        self.log(u"", xbmc.LOGDEBUG)

        warningFilePath = self.GetWarningFile()
        if not os.path.exists(warningFilePath):
            dialog = xbmcgui.Dialog()
            # WARNING: These videos are not moderated. By using this plugin you are accepting sole responsibility for any and all consequences of said use.
            action = dialog.yesno(self.GetProviderId(), self.language(30240), self.language(30241), self.language(30242), self.language(30260), self.language(30250) ) # 1=Continue; 0=Cancel
    
            if action == 0:
                return True
            
            f = open(warningFilePath, u"w")
            f.write('')
            f.close()
            
        try:
            listItems = []
            # Search by #tag
            label = self.language(30210)
            thumbnailPath = self.GetThumbnailPath(label)

            newListItem = xbmcgui.ListItem( label=self.language(30210) )
            newListItem.setThumbnailImage(thumbnailPath)
            url = self.GetURLStart() + u'&search=1'
            
            listItems.append((url, newListItem, True))

            # Popular hashtags            
            thumbnailPath = self.GetThumbnailPath(label)

            newListItem = xbmcgui.ListItem( label=self.language(30001) )
            newListItem.setThumbnailImage(thumbnailPath)
            url = self.GetURLStart() + u'&popular=1'
            listItems.append((url, newListItem, True))
            
            # Trending hashtags            
            thumbnailPath = self.GetThumbnailPath(label)

            newListItem = xbmcgui.ListItem( label=self.language(30002) )
            newListItem.setThumbnailImage(thumbnailPath)
            url = self.GetURLStart() + u'&trending=1'
            
            listItems.append((url, newListItem, True))

            xbmcplugin.addDirectoryItems( handle=self.pluginHandle, items=listItems )
            xbmcplugin.endOfDirectory( handle=self.pluginHandle, succeeded=True )
            
            return True
        except (Exception) as exception:
            exception = LoggingException.fromException(exception)

            #TODO Change text
            # Error processing categories
            exception.addLogMessage(self.language(30795))
            exception.process(self.language(30765), self.language(30795), severity = xbmc.LOGWARNING)
    
            return False
    
        

    def ParseCommand(self, mycgi):
        self.log(u"", xbmc.LOGDEBUG)

        (search, popular, trending, page, label) = mycgi.Params( u'search', u'popular', u'trending', u'page', u'label')

        if search <> '':
            return self.DoSearch()

        if popular <> '':
            return self.ShowTagsOfType("Popular")

        if trending <> '':
            return self.ShowTagsOfType("Trending")

        if page <> '':
            return self.ShowVinesByTag(page, label)

    def ShowVinesByTag(self, page, label):
        self.log("page: " + repr(page))
        url = urlRoot + page
        
        try:
            jsonText = None
            listItems = []
            html = self.httpManager.GetWebPageDirect(url)

            pattern = "<script.*>\s*var\s*vines\s*=\s*(\[.*\])\s*;\s*</script>"
            match = re.search(pattern, html, re.MULTILINE | re.DOTALL)

            jsonText = match.group(1)
    
            jsonData = _json.loads(jsonText)

            soup = BeautifulSoup(html)
            
            previous = soup.find('li', 'previous')
            next = soup.find('li', 'next')
            
            if previous:
                listItem = xbmcgui.ListItem("<< " + previous.text)
                url = self.GetURLStart() + u'&page=' + previous.a['href'] 
                listItems.append((url, listItem, True))
            else:
                self.AddOrderLinks(soup, listItems)
                
            for vineData in jsonData:
                url = vineData['vineVideoURL']
                icon = vineData['vineImageURL']
              
                infoLabels = {u'Title': vineData['vineDescription'], u'Plot': vineData['vineDescription']}
                
                self.log("infoLabels: " + utils.drepr(infoLabels))
                listItem = xbmcgui.ListItem(vineData['vineDescription'], iconImage = icon )
                listItem.setInfo(u'video', infoLabels)
                listItems.append((url, listItem))
            
            if next:
                listItem = xbmcgui.ListItem(">> " + next.text)
                url = self.GetURLStart() + u'&page=' + next.a['href']
                listItems.append((url, listItem, True))
                
            xbmcplugin.addDirectoryItems( handle=self.pluginHandle, items=listItems )
            xbmcplugin.endOfDirectory( handle=self.pluginHandle, succeeded=True )

            self.log( "listItems: " + repr(listItems)) 

        except (Exception) as exception:
            exception = LoggingException.fromException(exception)

            if jsonText is not None:
                msg = u"jsonText:\n\n%s\n\n" % jsonText
                exception.addLogMessage(msg)
                
            # Error processing web page
            exception.addLogMessage(self.language(30780))
            exception.process(self.language(30280), self.language(30780), severity = self.logLevel( xbmc.LOGERROR ))
    
            
    def AddOrderLinks(self, soup, listItems):
        orderP = soup.find('p', 'hidden-xs')
        for orderAnchor in orderP.findAll('a', 'btn-default'):
            text = '[ ' + orderAnchor.text + ' ]'
            newListItem = xbmcgui.ListItem( label=text )
            url = self.GetURLStart() + u'&page=' + mycgi.URLEscape(orderAnchor['href'])
            listItems.append( (url,newListItem,True) )
            
        #thumbnailPath = self.GetThumbnailPath(thumbnail)
        #newListItem.setThumbnailImage(thumbnailPath)

        
    def ShowTagsOfType(self, tagType):
        try:
            html = self.httpManager.GetWebPageDirect(urlRoot)
            soup = BeautifulSoup(html)
            
            ul = soup.find('h2', text=tagType)
            
            listItems = []
            for anchor in ul.parent.parent.findAll('a'):
                if anchor.text.find('#') == -1:
                    continue
                tag = anchor.text.replace('#','')
                newListItem = xbmcgui.ListItem( label='#' + tag )
                url = self.GetURLStart() + u'&page=' + self.GetTagPage(tag)
                
                listItems.append((url, newListItem, True))
                
            xbmcplugin.addDirectoryItems( handle=self.pluginHandle, items=listItems )
            xbmcplugin.endOfDirectory( handle=self.pluginHandle, succeeded=True )
            
            return True
            
        except (Exception) as exception:
            raise exception
        

    def GetTagPage(self, tag, pageNumber = None):
        if pageNumber:
            return "/tag/%s/%s" % (tag, pageNumber)
        else:
            return "/tag/%s" % tag
        
    def DoSearchQuery( self, query ):
        self.log("query: %s" % query, xbmc.LOGDEBUG)
        
        query = query.replace('#','')
        query = query.replace(' ','')
        
        page = self.GetTagPage(query) 
        return self.ShowVinesByTag(page, 'Search')
