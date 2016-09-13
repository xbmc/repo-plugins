#!/usr/bin/python
# -*- coding: utf-8 -*-

#imports
from xbmcswift import Plugin, xbmc, xbmcaddon, xbmcplugin, xbmcgui, clean_dict
from urllib2 import urlopen, HTTPError
import xbmcgui
from pyxbmct.addonwindow import *
import sys
import json
import os.path
from urllib2 import Request
import urllib
import urllib2

__addon_name__		= xbmcaddon.Addon().getAddonInfo('name')
__id__				= xbmcaddon.Addon().getAddonInfo('id')
__lang__			= xbmcaddon.Addon().getLocalizedString
__addon__ 			= xbmcaddon.Addon()
__version__ 		= __addon__.getAddonInfo('version')
__profile_path__ 	= xbmc.translatePath( __addon__.getAddonInfo('profile') ).decode("utf-8")
__token_filepath__	= __profile_path__ + '/token.txt'


THUMBNAIL_VIEW_IDS = {'skin.confluence': 500,
                      'skin.aeon.nox': 551,
                      'skin.confluence-vertical': 500,
                      'skin.jx720': 52,
                      'skin.pm3-hd': 53,
                      'skin.rapier': 50,
                      'skin.simplicity': 500,
                      'skin.slik': 53,
                      'skin.touched': 500,
                      'skin.transparency': 53,
                      'skin.xeebo': 55}

# BEGIN # Plugin
class Plugin_mod(Plugin):

    def add_items(self, iterable, is_update=False, sort_method_ids=[],
                  override_view_mode=False):
        items = []
        urls = []
        for i, li_info in enumerate(iterable):
            
            items.append( 
                self._make_listitem(**li_info)
            )

            if self._mode in ['crawl', 'interactive']:
                print '[%d] %s%s%s (%s)' % (i + 1, '', li_info.get('label'),
                                            '', li_info.get('url'))
                urls.append(li_info.get('url'))

        if self._mode is 'xbmc':
            if override_view_mode:
                skin = xbmc.getSkinDir()
                thumbnail_view = THUMBNAIL_VIEW_IDS.get(skin)
                if thumbnail_view:
                    cmd = 'Container.SetViewMode(%s)' % thumbnail_view
                    xbmc.executebuiltin(cmd)
            xbmcplugin.addDirectoryItems(self.handle, items, len(items))
            for id in sort_method_ids:
                xbmcplugin.addSortMethod(self.handle, id)
            xbmcplugin.endOfDirectory(self.handle, updateListing=is_update)

        return urls

    def _make_listitem(self, label, label2='', iconImage='', thumbnail='',
                       path='', **options):
        
        li = xbmcgui.ListItem(label, label2=label2, iconImage=iconImage, thumbnailImage=thumbnail, path=path)
        cleaned_info = clean_dict(options.get('info'))        
        
        li.setArt({ 'poster': options.get('thumb')})
        li.setInfo('video', {
            'originaltitle': label,
            'title': label,
            'sorttitle': options.get('key')
        })
        
        if cleaned_info:
            li.setInfo('video', cleaned_info)
        if options.get('is_playable'):
            li.setProperty('IsPlayable', 'true')
        if options.get('context_menu'):
            li.addContextMenuItems(options['context_menu'])

        return options['url'], li, options.get('is_folder', True)

# END  # Plugin


# Plugin_mod
plugin = Plugin_mod(__addon_name__, __id__)

# BEGIN #
if plugin.get_setting('server_url'):
    SITE_PATH = plugin.get_setting('server_url')
else:
    SITE_PATH = 'http://mytv.bg/api/mobile_v2/'

# Onli load master menu
ONLI_MASTER_MENU = SITE_PATH + 'menu/index'

SITE_LOGIN_PAGE = SITE_PATH + 'user/signin'
# END #


@plugin.route('/')
def main_menu():

    request = urllib2.Request(ONLI_MASTER_MENU, headers={"User-Agent" : "XBMC/Kodi MyTV Addon " + str(__version__)})
    response = urllib2.urlopen(request)
    dataNew = json.loads(response.read())

    menulist = dataNew['menu']
    items = []
    for (key, val) in enumerate(menulist):
        items.append({
            "label": u"{0}".format(val['title']),
            "key": u"{0}".format(key),
            'url': plugin.url_for('tvList',type=val['key']),
            'thumb': "{0}".format(val["thumb"])})

    return plugin.add_items(items, False, [xbmcplugin.SORT_METHOD_VIDEO_SORT_TITLE, xbmcplugin.SORT_METHOD_VIDEO_TITLE])


@plugin.route('/tvlist/<type>')
def tvList(type):

    menulist=[]
    items=[]
	
    dialog = xbmcgui.Dialog()

    if (not plugin.get_setting('username')) or (not plugin.get_setting('password')):
        dialog.ok(__lang__(30003), __lang__(30005))
        return
    
    signin = login(
        plugin.get_setting('username'), 
        plugin.get_setting('password'),
        type
    )
    
    if (not signin) or (not signin.token):
        return

    
    if not signin.data:
        return
    
    if 'menu' not in signin.data:
        if 'key' not in signin.data:
            dialog.ok(__lang__(30003), signin.data['msg'])
            return
        else:
			if 'quality_urls' in signin.data and len(signin.data['quality_urls']) > 1:
				for key,val in enumerate(signin.data['quality_urls']):
					items.append(val['title'])
				ret = dialog.select(__lang__(30006), items)
				tvPlay(signin.data['quality_urls'][ret]['key'])
				return
			tvPlay(signin.data['key'])
			return

    else:
        menulist = signin.data['menu']
        if not menulist:
            dialog.ok(__lang__(30003), __lang__(30004))
        if menulist:
            for (key, val) in enumerate(menulist):
                if val['type'] == 'item':
                    items.append({
                        "label": u"{0}".format(val['title']),
                        "key": u"{0}".format(key),
                        'url': plugin.url_for('tvPlay',type=val['key']),
                        'thumb': "{0}".format(val["thumb"])})
                elif val['type'] == 'menu':
                    items.append({
                        "label": u"{0}".format(val['title']),
                        "key": u"{0}".format(key),
                        'url': plugin.url_for('tvList',type=val['key']),
                        'thumb': "{0}".format(val["thumb"])})


    return plugin.add_items(items, False, [xbmcplugin.SORT_METHOD_VIDEO_SORT_TITLE, xbmcplugin.SORT_METHOD_VIDEO_TITLE])

@plugin.route('/tvPlay/<type>')
def tvPlay(type):
    xbmc.Player().play(type)
    return


# START # Login and using token for getting data.
class login:

    token = ""
    data = ""
    request = ""
    login_iteration = 0
    
    def __init__(self, username, password, type):
        self.usr = username
        self.pas = password
        self.type = type
        
        self.openReadFile()
        
        if not self.token:
            self.logIN()
            if not self.token:
                return
        
        self.data=self.getLive()
        self.data=self.getData(SITE_PATH + type)

    def logIN(self):
        self.data = self.makeUserPass()
        self.token = self.getData(SITE_LOGIN_PAGE)
        if self.token:
            self.writeInFile()
        
        return
    
    def getData(self, url):
        send = urllib.urlencode(self.data)
        self.request = urllib2.Request(url, send, headers={"User-Agent" : "XBMC/Kodi MyTV Addon " + str(__version__)})
        
        try:
            response = urllib2.urlopen(self.request)
        except HTTPError, e:
            dialog = xbmcgui.Dialog()
            dialog.ok(__lang__(30003), e.code)
            return
        
        data_result = response.read()
        
        try:
            res = json.loads(data_result)
        except Exception, e:
            xbmc.log('%s addon: %s' % (__addon_name__, e))
            return
        
        if 'token' in res:
            return res['token']
        
        if 'status' in res:
            if res['login'] == 'yes':

                if self.login_iteration > 0:
                    self.login_iteration = 0
                    return
                
                self.logIN()
                self.data=self.getLive()
                data_new=self.getData(url)
                self.login_iteration += 1
                
                return data_new

            else:

                dialog = xbmcgui.Dialog()
                dialog.ok(__lang__(30003), res['msg'])
                return
        
        return res

    def getLive(self):
        return {'token': self.token}

    def makeUserPass(self):
        return {
            "usr":self.usr,
            "pwd":self.pas,
            "access_type":"xbmc_kodi",
            "device_info": json.dumps({
                "board":xbmc.getInfoLabel("System.BuildVersion"),
                "brand":"xbmc/kodi " + xbmc.getInfoLabel("System.ProfileName"),
                "device":xbmc.getInfoLabel("System.KernelVersion"),
                "display":xbmc.getInfoLabel("System.FriendlyName"),
                "model":xbmc.getInfoLabel("System.BuildDate"),
                "product":"",
                "push_id":"",
                "uuid":""
            })
        }

    def writeInFile(self):
        fopen = open(__token_filepath__, "w+")
        fopen.write(self.token + " " + plugin.get_setting('username'))
        fopen.close()

    def openReadFile(self):
        if os.path.isfile(__token_filepath__):
            fopen = open(__token_filepath__, "r")
            temp_token = fopen.read()
            fopen.close()
            if temp_token:
				arr = temp_token.partition(" ")
				self.token = arr[0]
				if arr[1] and arr[1] != plugin.get_setting('username'):
					self.token = '';
				temp_token = ''
        else:
            self.writeInFile()
        
        
    def __log(self, text):
        xbmc.log('%s addon: %s' % (__addon_name__, text))

# END # LOGIN


# LOG Method
def __log(text):
    xbmc.log('%s addon: %s' % (__addon_name__, text))
    

if __name__ == '__main__':
    plugin.run()
