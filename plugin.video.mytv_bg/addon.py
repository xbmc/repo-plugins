#!/usr/bin/python
# -*- coding: utf-8 -*-

#imports
from xbmcswift import Plugin, xbmc, xbmcaddon, xbmcplugin, xbmcgui, clean_dict
from urllib2 import urlopen, HTTPError
import urlparse
import xbmcgui
from pyxbmct.addonwindow import *
import sys
import json
import os.path
from urllib2 import Request
import urllib
import urllib2
import datetime
import time

__addon__ 			= xbmcaddon.Addon()
__addon_name__		= __addon__.getAddonInfo('name')
__id__				= __addon__.getAddonInfo('id')
__lang__			= __addon__.getLocalizedString
__version__ 		= __addon__.getAddonInfo('version')
__profile_path__ 	= xbmc.translatePath( __addon__.getAddonInfo('profile') ).decode("utf-8")
__token_filepath__	= __profile_path__ + '/token.txt'


# BEGIN # Plugin
class Plugin_mod(Plugin):

    def add_items(self, iterable, is_update=False, sort_method_ids=[]):
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
            xbmcplugin.addDirectoryItems(self.handle, items, len(items))
            for id in sort_method_ids:
                xbmcplugin.addSortMethod(self.handle, id)
            xbmcplugin.endOfDirectory(self.handle, updateListing=is_update)

        return urls

    def _make_listitem(self, label, path='', **options):
        
        li = xbmcgui.ListItem(label, path=path)
        cleaned_info = clean_dict(options.get('info'))        
        
        li.setArt({ 'poster': options.get('thumb'), 'thumb': options.get('thumb')})
        li.setInfo('video', {
            'originaltitle': label,
            'title': label,
            'sorttitle': options.get('key')
        })
        
        return options['url'], li, options.get('is_folder', True)

# END  # Plugin


# Plugin_mod
plugin = Plugin_mod(__addon_name__, __id__)

# BEGIN #
if plugin.get_setting('server_url'):
    SITE_PATH = plugin.get_setting('server_url')
else:
    SITE_PATH = 'http://bgtime.tv/api/mobile_v4/'


# Onli load master menu
ONLI_MASTER_MENU = SITE_PATH + 'menu/index'

SITE_LOGIN_PAGE = SITE_PATH + 'user/signin'
# END #


@plugin.route('/')
def main_menu():

    request = urllib2.Request(ONLI_MASTER_MENU, headers={"User-Agent" : "XBMC/Kodi BGTime.TV Addon " + str(__version__)})
    response = urllib2.urlopen(request)

    dataNew = json.loads(response.read())
   
    menulist = dataNew['menu']
    items = []

    for (key, val) in menulist.iteritems():
        label = val['title'].encode('utf-8')
        items.append({
            'label': label,
            'key': u"{0}".format(key),
            'url': plugin.url_for('tvList', url=val['key'], title=label),
            'thumb': "{0}".format(val["thumb"])})

    return plugin.add_items(items, False, [xbmcplugin.SORT_METHOD_VIDEO_SORT_TITLE, xbmcplugin.SORT_METHOD_VIDEO_TITLE])


@plugin.route('/tvlist/<url>')
def tvList(url):
	args = urlparse.parse_qs(sys.argv[2][1:], keep_blank_values=True, strict_parsing=False)
	title_tmp = args.get('title', None)
	filters = False
	if title_tmp is None:
		title = ''
	else:
		title = title_tmp[0].decode('utf-8').encode('utf-8');

	show_title_tmp = args.get('show_title', None)

	if show_title_tmp is None:
		show_title = ''
	else:
		show_title = show_title_tmp[0].decode('utf-8').encode('utf-8');

	menulist=[]
	items=[]

	dialog = xbmcgui.Dialog()
	
	if(not plugin.get_setting('username')) or (not plugin.get_setting('password')):
		dialog.ok(__lang__(30003), __lang__(30005))
		return

	signin = login(
		plugin.get_setting('username'), 
		plugin.get_setting('password'),
		url
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
				tvPlay(signin.data['quality_urls'][ret]['key'], title, show_title, getTrackingKey(signin.data['quality_urls'][ret]))
				return
			tvPlay(signin.data['key'], title, show_title, getTrackingKey(signin.data))
			return

	else:
		menulist = signin.data['menu']
		_show_title = signin.data.get('title_prev', ' ').encode('utf-8')
		
		if not menulist:
			dialog.ok(__lang__(30003), __lang__(30004))
		if menulist:
			for (key, val) in enumerate(menulist):

				if val['type'] == 'item':
					items.append({
						'label': u"{0}".format(val['title']),
						'key': u"{0}".format(key),
						'url': plugin.url_for('tvPlay', url=val['key'], tracking_key=getTrackingKey(val)),
						'thumb': "{0}".format(val["thumb"])})
				elif val['type'] == 'menu':
					label = val['title'].encode('utf-8')
					items.append({
						'label': label,
						'key': u"{0}".format(key),
						'url': plugin.url_for('tvList', url=val['key'], title=label, show_title=_show_title),
						'thumb': "{0}".format(val["thumb"])})



	return plugin.add_items(items, False, [xbmcplugin.SORT_METHOD_VIDEO_SORT_TITLE, xbmcplugin.SORT_METHOD_VIDEO_TITLE])

def getTrackingKey(val):
	if 'tracking_key' in val:
		return val['tracking_key']
	return None

@plugin.route('/tvPlay/<url>')
def tvPlay(url, title, show_title, tracking_key):
	player = Player()
	if title:
		li = xbmcgui.ListItem(label=show_title + ' ' + title)
		player.play(url, li)
	else:
		player.play(url)
	player.is_playing = True
	
	player.tracking_key = tracking_key
	now = datetime.datetime.today()
	str_time = int(time.mktime(now.timetuple()))
	counter = 0

	while(player.is_playing):

		if player.isPlaying():
			player.info = {
				'key'			: tracking_key,
				'stream_started': str_time,
				'current_time'	: int(player.getTime()),
			}
			if counter == 120 and tracking_key is not None:
				counter = 0
				player.reportPlaybackProgress(player.info, 'progress')
		counter += 1
		xbmc.sleep(1000)

	del player
	return


# START # 
class Player(xbmc.Player):
	info 			= None
	tracking_key 	= None
	is_live 		= None
	is_playing 		= False

	def __init__(self):
		xbmc.Player.__init__(self)

	def onPlayBackStarted(self):
		if self.tracking_key is not None:
			now = datetime.datetime.today()
			str_time = int(time.mktime(now.timetuple()))
			self.info = {
				'key'			: self.tracking_key,
				'stream_started': str_time,
				'current_time'	: int(self.getTime()),
			}
			self.reportPlaybackProgress(self.info, 'start')

	def onPlayBackResumed(self):
		pass 

	def onPlayBackPaused(self):
		pass
		
	def onPlayBackStopped(self):
		if self.info is not None:
			self.reportPlaybackProgress(self.info, 'stop')
		self.is_playing = False

	def onPlayBackSeek(self, time, seekOffset):
		pass
		
	def reportPlaybackProgress(self, info, action):
		if info is None: return
		if self.tracking_key is not None:
			
			res = login(
					plugin.get_setting('username'), 
					plugin.get_setting('password'),
					'tracking/report_playback',
					{'key'				: self.tracking_key, 
					'stream_started'	: str(int(info['stream_started'])),
					'current_time'		: str(int(info['current_time'])),
					'action' 			: action
				})

# END # 



# START # Login and using token for getting data.
class login:

	token = ""
	data = ""
	request = ""
	login_iteration = 0
	
	def __init__(self, username, password, url, send = None):
		self.usr = username
		self.pas = password
		self.url = url
		
		self.openReadFile()
		
		if not self.token:
			self.logIN()
			if not self.token:
				return
		
		self.data=self.getLive()

		if send is not None: 
			self.data.update(send)		
		self.data=self.getData(SITE_PATH + url)

	def logIN(self):
		self.data = self.makeUserPass()
		self.token = self.getData(SITE_LOGIN_PAGE)
		if self.token:
			self.writeInFile()
		
		return
	
	def getData(self, url):
		send = urllib.urlencode(self.data)
		self.request = urllib2.Request(url, send, headers={"User-Agent" : "XBMC/Kodi BGTime.TV Addon " + str(__version__)})
		
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
			"access_type": "xbmc_kodi",
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
				if arr[2] and arr[2] != plugin.get_setting('username'):
					self.token = '';
				temp_token = ''
		else:
			self.writeInFile()
		
		

# END # LOGIN


# LOG Method
def __log(text):
    xbmc.log('%s addon: %s' % (__addon_name__, text))
    

if __name__ == '__main__':
    plugin.run()
