#!/usr/bin/env python
# -*- coding: utf-8 -*-

import urllib, urllib2, re, os, sys
import simplejson as json
channelsTV = {'laune': {'name': 'La Une', 'icon': 'laune.png','module':'rtbf'},
            'ladeux': {'name': 'La Deux', 'icon': 'ladeux.png','module':'rtbf'},
            'latrois': {'name': 'La Trois', 'icon': 'latrois.png','module':'rtbf'},
            }
channelsRadio = {'lapremiere': {'name': 'La Première', 'icon': 'lapremiere.png','module':'rtbf'},
            'vivacite': {'name': 'Vivacité', 'icon': 'vivacite.png','module':'rtbf'},
            'musiq3': {'name': 'Musiq 3', 'icon': 'musiq3.png','module':'rtbf'},
            'classic21': {'name': 'Classic 21', 'icon': 'classic21.png','module':'rtbf'},
            'purefm': {'name': 'Pure FM', 'icon': 'purefm.png','module':'rtbf'},
            }
categories = {'35':{'name': 'Series'},
             '36':{'name': 'Films'},
             '1':{'name': 'Info'},
             '9':{'name': 'Sport'},
             '11':{'name': 'Football'},
             '40':{'name': 'Humour'},
             '29':{'name': 'Divertissement'},
             '44':{'name': 'Vie Quotidienne'},
             '31':{'name': 'Documentaire'},
             '18':{'name': 'Culture'},
             '23':{'name': 'Musique'},
             '32':{'name': 'Enfants'}
            }

from htmlentitydefs import name2codepoint

try:
    import xbmcplugin, xbmcgui, xbmcaddon, xbmc
    in_xbmc = True
    __settings__ = xbmcaddon.Addon(id='plugin.video.rtbf.auvio')
    __language__ = __settings__.getLocalizedString
    home = __settings__.getAddonInfo('path')
except:
    in_xbmc = False 

def get_url(url, referer='http://www.duckduckgo.com'):
    if not in_xbmc:
        print 'Get url:', url
    req = urllib2.Request(url)
    req.addheaders = [('Referer', referer),
            ('Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.2.3) Gecko/20100101 Firefox/11.0 ( .NET CLR 3.5.30729)')]
    response = urllib2.urlopen(req)
    data = response.read()
    response.close()
    return data

def uniquify(list):
    new_list = []
    for e in list:
        if e not in new_list:
            new_list.append(e)
    return new_list

remove_accent_regex = re.compile(r"""&([a-zA-Z])(acute;|circ;|grave;)""")
def removehtml(txt):
    return remove_accent_regex.sub(r'\1', txt)

def clear_entity(txt):
    new_txt = ''
    for c in txt:
        if ord(c) > 128:
            new_txt += '.'
        else:
            new_txt += c
    return new_txt

def htmlentitydecode(s):
    s = clear_entity(s)
    return re.sub('&(%s);' % '|'.join(name2codepoint),
            lambda m: unichr(name2codepoint[m.group(1)]), s)

def time2str(t):
    time_division = [('s', 60), ('m', 60), ('h', 24)]
    time = []
    for symbol, duration in time_division:
        v = t % duration
        if v > 0:
            time.insert(0, str(v) + symbol)
        t = t / duration
    return ' '.join(time)

def addLink(name, url, iconimage, **kwargs):
    name = name.replace('&#039;', "'").replace('&#034;', '"')
    if not in_xbmc:
        xbmc.log('Title: [' + name + ']',xbmc.LOGDEBUG)
        xbmc.log('Img:' + iconimage,xbmc.LOGDEBUG)
        xbmc.log('Url:'+ url,xbmc.LOGDEBUG)
        return True
    if 'Title' not in kwargs:
        kwargs['Title'] = name
    ok = True
    liz = xbmcgui.ListItem(name, iconImage='DefaultVideo.png', thumbnailImage=iconimage)
    liz.setInfo(type='Video', infoLabels=kwargs)
    liz.setProperty('IsPlayable', 'true')
    ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=url, listitem=liz)
    return ok

def array2url(**args):
    vals = []
    for key, val in args.iteritems():
        vals.append(key + '=' + urllib.quote_plus(val))      
    return sys.argv[0] + "?" + '&'.join(vals)

def addDir(name, iconimage, **args):
    name = name.replace('&#039;', "'").replace('&#034;', '"')
    u = array2url(**args)
    if not in_xbmc:
        xbmc.log('Title: [' + name + ']',xbmc.LOGDEBUG)
        xbmc.log('Img:' + iconimage,xbmc.LOGDEBUG)
        xbmc.log('Url:' + u,xbmc.LOGDEBUG)
        for key in args:
            print key + ': ' + args[key]
        return True
    liz = xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
    liz.setInfo(type="Video", infoLabels={ "Title": name })
    ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz, isFolder=True)
    return ok

def playUrl(url):
    xbmc.log('Play url:' + url,xbmc.LOGDEBUG)
    if not in_xbmc:
        return True
    liz = xbmcgui.ListItem(path=url)
    return xbmcplugin.setResolvedUrl(handle=int(sys.argv[1]), succeeded=True, listitem=liz)
    
class Channel(object):
    def __init__(self, context):
        self.channel_id = context.get('channel_id')
        self.main_url = self.get_main_url()
        if in_xbmc:
            try:
               self.icon = xbmc.translatePath(os.path.join(home, 'resources/' + context['icon']))
            except:
               self.icon = 'DefaultVideo.png'	    
        else:
            self.icon = context.get('icon')
        action = context.get('action')
        xbmc.log('action:' + action,xbmc.LOGDEBUG)
        if action == 'show_categories':
            self.get_categories(context)
        elif action == 'show_videos':
            self.get_videos(context)
        elif action == 'show_videos_cat':
            self.get_videos_cat(context)
        elif action == 'play_video':
            self.play_video(context)
        elif action == 'play_live':
            self.play_live(context)
        elif action == 'scan_empty':
            self.scan_empty(context)
        elif action == 'show_tv':
            self.show_tv(context)
        elif action == 'show_radio':
            self.show_radio(context)
        elif action == 'show_program':
            self.get_programs(context)
        elif action == 'show_category':
            self.get_category(context)
        elif action == 'show_lives':
            self.get_lives(context)
        elif action == 'show_channel':
            self.get_channel(context)

    def show_tv(self, datas):
	for channel_id, ch in channelsTV.iteritems():
	    if in_xbmc:
                icon = xbmc.translatePath(os.path.join(home, 'resources/' + ch['icon']))
                addDir(ch['name'], icon, channel_id=channel_id, action='show_channel')
            else:
                xbmc.log(str(ch['name']) +' '+ channel_id + ' show_channel',xbmc.LOGDEBUG)

    def show_radio(self, datas):
	for channel_id, ch in channelsRadio.iteritems():
            if in_xbmc:
               icon = xbmc.translatePath(os.path.join(home, 'resources/' + ch['icon']))
               addDir(ch['name'], icon, channel_id=channel_id, action='show_channel')
            else:
                xbmc.log(str(ch['name']) +' '+ channel_id + ' show_channel',xbmc.LOGDEBUG)
    
    def show_cat(self, datas):
    	self.get_cat(context)
	for channel_id, ch in channelsRadio.iteritems():
            if in_xbmc:
               icon = xbmc.translatePath(os.path.join(home, 'resources/' + ch['icon']))
               addDir(ch['name'], icon, channel_id=channel_id, action='show_categories')
            else:
                xbmc.log(str(ch['name']) +' '+ channel_id + ' show_categories',xbmc.LOGDEBUG)

    def set_main_url(self):
        return ''
            
    def get_categories(self, skip_empty_id = True):
        pass
    
    def get_subcategories(self, datas):
        pass
        
    def get_videos(self, datas):
        pass
    
    def play_video(self, datas):
        pass
    
    def get_lives(self, datas):
        pass
    
    def play_live(self, datas):
        pass
    
    def scan_empty(self, datas):
        cats = []
        def addCat(name, img, **kargs):
            cats.append(kargs)
        vids = []
        def addVid(title, vurl, img):
            vids.append(1)
        self_module = sys.modules[__name__]
        self_module.addDir = addCat
        self_module.addLink = addVid
        self.get_categories(False)
        new_id2skip = []
        i = 0
        nb = len(cats)
        cat_done = []
        for cat in cats:
            xbmc.log(str(i) + '/' + str(nb),xbmc.LOGDEBUG)
            i += 1
            vids = []
            self.get_videos(cat)
            if not len(vids):
                new_id2skip.append(cat['id'])
            cat_done.append(cat['id'])
            xbmc.log('done: ' + ',' .join(cat_done),xbmc.LOGDEBUG)
            xbmc.log('id2skip: ' + ','.join(new_id2skip),xbmc.LOGDEBUG)
