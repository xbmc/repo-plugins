# -*- coding: utf-8 -*-

import os
import urllib2
 
try:
    from xml.etree import ElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET

#import pydevd
#pydevd.settrace('localhost', stdoutToServer=True, stderrToServer=True)

import bromixbmc
__plugin__ = bromixbmc.Plugin()

__FANART__ = os.path.join(__plugin__.getPath(), "fanart.jpg")
if not __plugin__.getSettingAsBool('showFanart'):
    __FANART__ = ''
__ICON__ = os.path.join(__plugin__.getPath(), "icon.png")

__SETTING_SUPPORT_ANIMATED_GIF__ = __plugin__.getSettingAsBool('supportAnimatedGifs')

__ACTION_SHOW_CHANNEL__ = 'showChannel'
__ACTION_SHOW_GALLERY__ = 'showGallery'

def _getChannelContentXml(channel_id, page):
    result = None
    
    url = 'http://api.break.com'
    if channel_id=='-1':
        url+='/invoke/homepage/includeyoutube/'
    elif channel_id=='-2':
        url+='/invoke/listgalleries/'
        if __SETTING_SUPPORT_ANIMATED_GIF__:
            url+='includegif/'
    else:
        url+='/invoke/channel/includeyoutube/'
        url+=channel_id
        url+='/'
        
    url+=str(page)+'/'
    url+='25/'
    
    if channel_id!='-1' and channel_id!='-2':
        url+='PG/'
    
    opener = urllib2.build_opener()
    opener.addheaders = [('User-Agent', 'stagefright/1.2 (Linux;Android 4.4.2)')
                         ]
    try:
        content = opener.open(url)
        result = ET.XML(content.read())
    except:
        # do nothing
        pass
    
    return result

def _getGalleryContentXml(gallery_id, page, contentCount):
    result = None
    
    gifUrl = ''
    if __SETTING_SUPPORT_ANIMATED_GIF__:
        gifUrl = 'includegif/'
            
    url = 'http://api.break.com/invoke/gallery/%s%s/%s/%s/' % (gifUrl, gallery_id, page, contentCount)
    
    opener = urllib2.build_opener()
    opener.addheaders = [('User-Agent', 'stagefright/1.2 (Linux;Android 4.4.2)')
                         ]
    try:
        content = opener.open(url)
        result = ET.XML(content.read())
    except:
        # do nothing
        pass
    
    return result

def showIndex(page):
    xml = _getChannelContentXml('-2', page)
    if xml!=None:
        pageCount = 0
        try:
            pageCount = int(xml.get('PageCount'))
        except:
            pageCount = 1
            
        for content in xml:
            contentName = content.find('ContentTitle').text
            
            contentId = content.find('ContentID').text
            contentThumb = content.find('ContentStaticURL').text
            contentCount = content.find('ChildContentCount').text
                 
            if contentId and contentName:
                params = {'action': __ACTION_SHOW_GALLERY__,
                          'id': contentId,
                          'contentcount': contentCount
                          }
                __plugin__.addDirectory(name=contentName, params=params, thumbnailImage=contentThumb, fanart=__FANART__)
        
        if page<pageCount:
            params = {'action': __ACTION_SHOW_CHANNEL__,
                      'id': id,
                      'page': str(page+1)
                      }
            __plugin__.addDirectory(__plugin__.localize(30000)+' ('+str(page+1)+')', params=params, fanart=__FANART__)

    __plugin__.endOfDirectory()
    
def showGallery(gallery_id, page, contentCount):
    xml = _getGalleryContentXml(gallery_id, page, contentCount)
    if xml!=None:
        for content in xml:
            contentTitle = content.find('ContentTitle').text
            image = content.find('ContentStaticURL').text
            
            __plugin__.addImage(name=contentTitle, image_url=image, fanart=__FANART__)
            pass 
        pass
    
    __plugin__.endOfDirectory()


action = bromixbmc.getParam('action')
gallery_id = bromixbmc.getParam('id')
page = int(bromixbmc.getParam('page', '1'))
contentCount = bromixbmc.getParam('contentcount')

if action == __ACTION_SHOW_GALLERY__ and contentCount!=None and gallery_id!=None:
    showGallery(gallery_id, page, contentCount)
else:
    showIndex(page)