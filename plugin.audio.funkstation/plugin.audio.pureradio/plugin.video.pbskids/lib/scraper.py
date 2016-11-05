# -*- coding: utf-8 -*-
# KodiAddon PBSKids
#
from t1mlib import t1mAddon
import json
import re
import os
import datetime
import urllib
import urllib2
import xbmc
import xbmcplugin
import xbmcgui
import HTMLParser
import sys

h = HTMLParser.HTMLParser()
qp  = urllib.quote_plus
uqp = urllib.unquote_plus
UTF8     = 'utf-8'

class myAddon(t1mAddon):

  def getAddonMenu(self,url,ilist):
    pg = self.getRequest('http://pbskids.org/pbsk/video/api/getShows/?callback=&destination=national&return=images')
    pg = pg.strip('()')
    a = json.loads(pg)['items']
    for b in a:
        name = b['title']
        plot = b['description']
        url = name
        ages = 'Ages %s' % b['age_range']
        thumb = b['images']['program-kids-square']['url']
        infoList = {}
        infoList['Title'] = name
        infoList['Plot']  = b['description']
        infoList['Studio'] = 'Ages %s' % b['age_range']
        ilist = self.addMenuItem(name,'GC', ilist, url, thumb, self.addonFanart, infoList, isFolder=True)
    return(ilist)

  def getAddonCats(self,url,ilist):
    dolist = [('episode', 'Episodes'), ('clip', 'Clips')]
    for kctype, name in dolist:
        infoList={}
        url = 'http://pbskids.org/pbsk/video/api/getVideos/?startindex=1&endindex=200&program=%s&type=%s&category=&group=&selectedID=&status=available&player=flash&flash=true' % (url.replace(' ','%20').replace('&','%26'), kctype)
        ilist = self.addMenuItem(name,'GE', ilist, url, self.addonIcon, self.addonFanart, infoList, isFolder=True)
    return(ilist)


  def getAddonEpisodes(self,url,ilist):
    pg = self.getRequest(url)
    a = json.loads(pg)['items']
    for b in a:
        name = b['title']
        plot = b['description']
        thumb  = b['images']['kids-mezzannine-16x9']['url']
        try:
           captions = b['captions']['srt']['url']
        except:
           captions = ''
        try:
           url = b['videos']['flash']['mp4-2500k']['url']
        except:
           try:
               url = b['videos']['flash']['mp4-1200k']['url']
           except:
                  url = b['videos']['flash']['url']

        fanart = thumb
        infoList={}
        infoList['Title'] = name
        infoList['Plot']  = plot
        ilist = self.addMenuItem(name,'GV', ilist, url+'|'+captions, thumb, fanart, infoList, isFolder=False)
    return(ilist)


  def getAddonVideo(self,url):
    url, captions = url.split('|',1)
    html = self.getRequest('%s?format=json' % url)
    url = json.loads(html)['url']
    try:
         url = 'http://kids.video.cdn.pbs.org/videos/%s' % url.split(':videos/',1)[1]
    except:
         pass

    liz = xbmcgui.ListItem(path = url)
    if captions != "" : liz.setSubtitles([captions])
    xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, liz)

