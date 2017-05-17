# -*- coding: utf-8 -*-
import os, sys, string, random, platform, datetime
import urllib, urlparse, json
import xbmc, xbmcaddon, xbmcplugin, xbmcgui
import requests
import mechanize
from mechanize import Browser
from simplecache import SimpleCache

class initCheck(object):
	'''on very first run it will register kodi (device) with the CARNet Meduza (CM) service. On every subseq run or >12h it  will check connectivity with the CM servise
	when device is registered, api key will be stored for a year
	
	Attributes:
		addon_name: A string represnting plugin name
	'''
	
	def __init__(self, addon_name):
		'''Return plugin name'''
		self.addon_name = addon_name 

	def gen_key(self):
		'''Returns unique 140 char long string that emulates device id - api key'''
		# ex: Linux
		os_name = platform.system()
		# generate 140 char device id (a.k.a. api key)
		rnd_str = ''.join(random.choice(string.ascii_letters+string.digits) for x in range(140))
		combo_str = 'kodi' + os_name + rnd_str
		# remove non alpha-numeric chars and truncate to 140 
		uniq_key = ''.join(char for char in combo_str if char.isalnum())[:140]
		return uniq_key

	def store_key(self):
		'''Persistently keep api key and registration status (not/is) in userdata/storage.pcl file
		and return stored key and the status'''
		#gen/set/get uniq key == device_id == api_key
		key_store = simplecache.get(addon_name + '.key_store')
		#check if key is stored in simplecache db 
		if not key_store:
			uniq_key = self.gen_key() # gen key only if key_store empty (once)
			simplecache.set(addon_name + '.key_store', uniq_key, expiration=datetime.timedelta(hours=8760)) # store the key and keep it for a year
			reg_dev_status_flag = 'not_reg'
			simplecache.set(addon_name + '.reg_dev_status', reg_dev_status_flag, expiration=datetime.timedelta(hours=8760))
		reg_dev_status = simplecache.get(addon_name + '.reg_dev_status')
		key = simplecache.get(addon_name + '.key_store')
		return (key, reg_dev_status)

	# register device
	def dev_reg(self, device_id):
		'''Returns the url that server responded with after registration attempt'''
		# get user info from settings
		aai_password = self.get_pwd()
		api_base_url = 'https://meduza.carnet.hr/index.php/login/mobile/?device='
		# for some reason, it start at 2 {'Tablet':'2', 'Smartphone':'3', 'SmartTV':'4'}
		device_type = int(addon.getSetting('device_type')) + 2
		# request target resource, discover IdP and redirect to SSO service
		request_url = api_base_url + str(device_type) + '&uid=' + device_id
		r = requests.get(request_url)
		redirect_cookies = r.cookies

		# identify the user from requested SSO service (login)
		form_open = r.url.encode('utf-8')

		# set browser
		br = mechanize.Browser()
		br.set_cookiejar(redirect_cookies)
		br.set_handle_equiv(True)
		br.set_handle_redirect(True)
		br.set_handle_referer(True)
		br.set_handle_robots(False)
		br.set_handle_refresh(mechanize._http.HTTPRefreshProcessor(), max_time=1)
		# open login page
		br.open(form_open)
		br.select_form(name='f')
		br['username'] = aai_username 
		br['password'] = aai_password
		br.method = 'POST'
		br.submit()

		# submit using responded XHTML form, redirect to requested target resource and get response code
		submit = br.open(form_open, timeout=5.0)
		submit.geturl()
		br.select_form(nr=0)
		br.method = 'POST'
		response = br.submit()
		response_url = response.geturl()
		return response_url

	# check device registration status
	def check_reg(self, response, device_id):
		'''Takes response from reg_dev, along with api key'''
		response_parsed = urlparse.urlparse(response)
		# if reponse doesn't return proper status reponse due to wrong usually username/password entry 
		# catch keyError and pop custom message
		try:
			response_code = urlparse.parse_qs(response_parsed.query)['status'][0]
			# 200 means that 'device' was successfully registered with SP and device UID can be stored in the settings
			if response_code == '200':
				addon.setSetting('apikey',device_id)
				self.user_info(device_id)
				info_dialog_msg = addon.getLocalizedString(30209) 
				dialog.notification('CARNet Meduza', info_dialog_msg, xbmcgui.NOTIFICATION_INFO, 4000)
				userdata_path_special = xbmcaddon.Addon().getAddonInfo('profile').decode('utf-8')
				userdata_path = xbmc.translatePath(userdata_path_special)
				reg_dev_status_flag = 'is_reg'
				simplecache.set(addon_name + '.reg_dev_status', reg_dev_status_flag, expiration=datetime.timedelta(hours=8760))
			else: 
				ret_codes = {'100':30215, '300':30216, '400':30217, '401':30218}
				ret_message = addon.getLocalizedString(ret_codes[response_code])
				dialog.notification('CARNet Meduza', ret_message, xbmcgui.NOTIFICATION_WARNING, 4000)
		except KeyError:
			sso_err_msg = addon.getLocalizedString(30219)
			dialog.notification('CARNet Meduza', sso_err_msg, xbmcgui.NOTIFICATION_ERROR, 4000)

	def get_pwd(self):
		'''Storing SSO password is not best way to go, so just get the it, when needed. Returns entered password.'''
		heading_msg = addon.getLocalizedString(30210) 
		keyboard = xbmc.Keyboard()
		keyboard.setHeading(heading_msg)
		keyboard.setHiddenInput(True) 
		keyboard.doModal()
		if (keyboard.isConfirmed()):
			enter_pwd = keyboard.getText()
			if enter_pwd is None or len(str(enter_pwd)) == 0:
				info_dialog_msg = addon.getLocalizedString(30211)
				dialog.notification('CARNet Meduza', info_dialog_msg, xbmcgui.NOTIFICATION_WARNING, 4000)
		del keyboard
		return enter_pwd

	# pre run check (make api requests for content) 
	def pre_run(self):
		'''When addon is started, checks if registration status is valid.'''
		# request target resource, discover IdP and redirect to SSO service
		request_url = 'https://meduza.carnet.hr/index.php/api/registered/?uid=' + api_key
		r = requests.get(request_url)
		registered_status = r.json()['code']
		if registered_status == 200:
			success_msg = addon.getLocalizedString(30212)
			dialog.notification('CARNet Meduza', r.json()['message'] + success_msg, xbmcgui.NOTIFICATION_INFO, 4000)
		else:
			error_msg = addon.getLocalizedString(30213)
			dialog.notification('CARNet Meduza', error_msg, xbmcgui.NOTIFICATION_ERROR, 4000)			

	# get user info and populate the settings.xml
	def user_info(self, api_key):
		'''Once more, it takes api key, gets user info from the CM server and stores it to settings.'''
		# request target resource, discover IdP and redirect to SSO service
		request_url = 'https://meduza.carnet.hr/index.php/api/user/?uid=' + api_key
		r = requests.get(request_url)
		user_details = r.json()
		first_name = user_details['ime'].encode('utf-8')
		last_name = user_details['prezime'].encode('utf-8')
		reg_date = user_details['datum_registracija'].encode('utf-8')
		addon.setSetting('first_name',first_name)
		addon.setSetting('last_name',last_name)
		addon.setSetting('reg_date',reg_date)

def build_url(query):
	'''Returns builds query url.'''
	return base_url + '?' + urllib.urlencode(query)

def categories():
	'''Returns list of categories.'''
	requestCategories = requests.get(api_base_url + 'categories/?lang=en&uid=' + api_key)
	categories = requestCategories.json()
	return categories

def channels():
	'''Returns list of channels.'''
	requestChannels = requests.get(api_base_url + 'channels/?uid=' + api_key)
	channels = requestChannels.json()
	return channels

def category_videos(name,current_page_number):
	'''Returns list of vidoes (25 per page) inside selected category.'''
	for category in categories:
		if category[lang_api_prop] == name:
			skip = int(current_page_number) * 25
			category_id = category['ID']
			request_category_videos = requests.get(api_base_url + 'category/?id=' + category_id + '&skip=' + str(skip) + '&uid=' + api_key)
			videos = request_category_videos.json()
        return videos 

def search_videos():
	'''Returns search results vidoes.'''
        search_heading = addon.getLocalizedString(30206)
	keyboard = xbmc.Keyboard()
        keyboard.setHeading(search_heading)
	keyboard.doModal()
	if (keyboard.isConfirmed()):
		query = keyboard.getText()
		if query is None or len(str(query)) == 0:
			return
	else:
		return
	sort_videos = addon.getSetting('sort_videos')
	asc_order = addon.getSetting('asc_order')	
	request_search_videos = requests.get(api_base_url + 'videos/?query=' + query + '&order=' + str(sort_videos) + '&uid=' + api_key + '&asc=' + str(int(bool(asc_order))))
	videos = request_search_videos.json()
	return videos 

def category_video_count(category_id):
	'''Returns total number of videos inside the category.'''
	request_category_video_count = requests.get(api_base_url + 'category/count/?id=' + category_id + '&uid=' + api_key)
	category_video_count = request_category_video_count.json()
	return category_video_count

def video_url_description(video_id):
	'''Returns video description.'''
	request_video_url_description = requests.get(api_base_url + 'video/?id=' + video_id + '&uid=' + api_key).json()
	extract_keys = ['stream_url', 'opis']
	video_url_description = dict((k, request_video_url_description[k]) for k in extract_keys if k in request_video_url_description)
	return video_url_description

def recommended_videos():
	'''Returns list of recommended videos. The number of videos can be defined inside settings. Default is 20.'''
	num_recommends = xbmcaddon.Addon(addon_name).getSetting('num_recommends')
	request_recommended_videos = requests.get(api_base_url + 'recommended/?number=' + str(num_recommends) + '&uid=' + api_key)
	videos = request_recommended_videos.json()
	return videos 

def list_search_or_recommended_videos(videos):
	if videos == None:
		return
	else:	
		for video in videos:
			category_id = video['ID_kategorija']
			name = video['naslov']
			video_id = video['ID']
			genre = video['kategorija']
			duration = reduce(lambda x, y: x*60+y, [int(i) for i in (video['trajanje'].replace(':',',')).split(',')])
			video_info = video_url_description(video_id)
			try:
				header = urllib.urlencode({'Referer':'https://meduza.carnet.hr'})
				url = video_info['stream_url'] +'|'+ header
				description = video_info['opis'].encode('utf-8')
			except KeyError:
				url = ''
				description = addon.getLocalizedString(30207)
				pass		
			image = video['slika']
			li = xbmcgui.ListItem(name)
			li.setArt({'icon':image})
			li.setInfo( type='Video', infoLabels={ 
							'Plot': description, 
							'Genre': genre,
							'Duration': duration,
							'mediatype':'video'
								})
			xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li)
		xbmcplugin.endOfDirectory(addon_handle)

# list videos from selected category	
def list_category_videos(videos,current_page_number,foldername):
	if not videos:
		#category level listitems
		li_translate = addon.getLocalizedString(30208)
		li = xbmcgui.ListItem(li_translate)
		li.setArt({'icon':'DefaultVideo.png'})
		xbmcplugin.addDirectoryItem(handle=addon_handle, url='', listitem=li)
		xbmcplugin.endOfDirectory(addon_handle)
	else:
		for video in videos:
			category_id = video['ID_kategorija']
			video_num = category_video_count(category_id)['count']
			name = video['naslov']
			video_id = video['ID']
			duration = reduce(lambda x, y: x*60+y, [int(i) for i in (video['trajanje'].replace(':',',')).split(',')])
			video_info = video_url_description(video_id)
			header = urllib.urlencode({'Referer':'https://meduza.carnet.hr'})
			url = video_info['stream_url'] +'|'+ header
			image = video['slika']
			description = video_info['opis'].encode('utf-8')
			li = xbmcgui.ListItem(name)
			li.setArt({'icon':image})
			li.setInfo( type='Video', infoLabels={ 
								'Plot': description, 
								'Duration': duration,
								'mediatype':'video'
								})
			xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li)
		pages_num = video_num / 25
		if int(current_page_number) < pages_num:
			int_current_page_number = int(current_page_number)
			int_current_page_number += 1
			current_page_number = str(int_current_page_number)
			url = build_url({'mode': 'folder', 'foldername': foldername, 'pagenumber': current_page_number})
			li = xbmcgui.ListItem('> Next Page (' + str(int_current_page_number + 1) + ')')
			li.setArt({'icon':'DefaultFolder.png'})
			li.setInfo('video', { 'mediatype': 'video' })
			xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)		
		xbmcplugin.endOfDirectory(addon_handle)

# play playlist of the selected channel with 'current video' + time offset (emulates tv channel) 		
def start_channel(channel_id,channel_video_count):
	playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
	player = xbmc.Player()
	playlist.clear()
	requestChannel = requests.get(api_base_url + 'channel/?id=' + channel_id + '&uid=' + api_key)
	channel = requestChannel.json()
	channel_index = channel['index']
	schedule = channel['raspored']
	channel_offset = channel['offset']
	schedule_gen = ((i, j) for i, j in enumerate(schedule))
	for i, j in schedule_gen:
	        li = xbmcgui.ListItem(j['naslov'])
		li.setArt({'thumb':j['slika']})
		itemArgs = {
                'title': j['naslov'].encode('utf-8'),
                'plot': j['opis'].encode('utf-8'),
		'mediatype':'video',
                'tracknumber': i 
            	}
		li.setInfo('video', itemArgs)
		playlist.add(url=j['stream_url'],listitem=li)
        player.play(item=playlist,startpos=channel_index)
	player.seekTime(channel_offset)

addon_name = 'plugin.video.carnet-meduza'
addon=xbmcaddon.Addon(addon_name)
# get username/apikey from settings
aai_username = addon.getSetting('aai_username')
#get some data from cache
simplecache = SimpleCache()
tmp_store = simplecache.get(addon_name + '.tmp_store')
dialog = xbmcgui.Dialog()

if not tmp_store:
	initcheck = initCheck(addon_name)
	api_key, dev_reg_status = initcheck.store_key()
	addon.setSetting('apikey',api_key)
	#if aai_username missing open settings, otherwise  start device registration
	if not aai_username and dev_reg_status == 'not_reg':
		info_dialog_msg = addon.getLocalizedString(30214)
		dialog.notification('CARNet Meduza', info_dialog_msg, xbmcgui.NOTIFICATION_INFO, 4000)
		xbmcaddon.Addon().openSettings()	
	elif dev_reg_status == 'not_reg':
		reg_response = initcheck.dev_reg(api_key)
		initcheck.check_reg(reg_response, api_key)
	else:
		initcheck.pre_run()
		tmp_store_flag = 1
		simplecache.set( addon_name + '.tmp_store', tmp_store_flag, expiration=datetime.timedelta(hours=12))

base_url = sys.argv[0]
addon_handle = int(sys.argv[1])
args = urlparse.parse_qs(sys.argv[2][1:])
#set as video addon
xbmcplugin.setContent(addon_handle, 'videos')

api_base_url = 'https://meduza.carnet.hr/index.php/api/'
category_image_base_url = 'https://meduza.carnet.hr/uploads/images/categories/'
# api_key == device_id from register (import) device == uid
api_key = addon.getSetting('apikey')

mode = args.get('mode', None)

dir_recommends = addon.getLocalizedString(30201)
dir_categories = addon.getLocalizedString(30202)
dir_channels = addon.getLocalizedString(30203)
dir_search = addon.getLocalizedString(30204)
dir_settings = addon.getLocalizedString(30205)

# get api lang property (en|hr)
active_lang = xbmc.getLanguage()
if active_lang == 'Croatian':
	lang_api_prop = 'naziv'
else:
	lang_api_prop = 'naziv_en'

#category level listitems
if mode is None:
    url = build_url({'mode': 'folder', 'foldername': dir_recommends})
    li = xbmcgui.ListItem(dir_recommends)
    li.setArt({'icon':'DefaultVideo.png'})
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)

    url = build_url({'mode': 'folder', 'foldername': dir_categories})
    li = xbmcgui.ListItem(dir_categories) 
    li.setArt({'icon':'DefaultAddonVideo.png'})
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)

    url = build_url({'mode': 'folder', 'foldername': dir_channels})
    li = xbmcgui.ListItem(dir_channels) 
    li.setArt({'icon':'DefaultAddonTvInfo.png'})
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)

    url = build_url({'mode': dir_search, 'foldername': dir_search})
    li = xbmcgui.ListItem(dir_search) 
    li.setArt({'icon':'DefaultAddonsSearch.png'})
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)
	
    url = build_url({'mode': dir_settings, 'foldername': dir_settings})
    li = xbmcgui.ListItem(dir_settings)
    li.setArt({'icon':'DefaultAddonProgram.png'})
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li)
	
    xbmcplugin.endOfDirectory(addon_handle)

elif mode[0] == 'folder':
	if args['foldername'][0].decode('utf-8') == dir_recommends:
		videos =  recommended_videos()
		list_search_or_recommended_videos(videos)

	elif args['foldername'][0].decode('utf-8') == dir_categories:
		categories = categories()
		categoryGen = (category for category in categories if category['naziv'] != 'YouTube')
		for category in categoryGen:
			#category level listitems
			active_lang = xbmc.getLanguage()
			name = category[lang_api_prop].encode('utf-8')
			url = build_url({'mode': 'folder', 'foldername': name})
			categoryImage = category_image_base_url + category['slika']
			li = xbmcgui.ListItem(name)
			li.setArt({'icon':categoryImage})
			xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)
		xbmcplugin.endOfDirectory(addon_handle)

	elif args['foldername'][0].decode('utf-8') == dir_channels:
		channels = channels()
		for channel in channels:
			name = channel['naziv'].encode('utf-8')
			url = build_url({'mode': 'folder', 'foldername': name})
			channelImage = channel.get('slika','')
			li = xbmcgui.ListItem(name)
			li.setArt({'icon':channelImage})
			li.setInfo('video', { 'mediatype': 'video' })
			xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li)
		xbmcplugin.endOfDirectory(addon_handle)

	else:
		categories = categories()
		channels = channels()
		foldername = args['foldername'][0]
		#api response is 'list of dictionaries' so using lambda is nice way of checking for values
		if filter(lambda name: name[lang_api_prop] == foldername.decode('utf-8'), categories):
			current_page_number = args.get('pagenumber',['0'])[0]
			videos =  category_videos(foldername.decode('utf-8'),current_page_number)
			list_category_videos(videos,current_page_number,foldername.decode('utf-8'))
		else:
			channel = filter(lambda name: name['naziv'] == foldername.decode('utf-8'), channels)
			channel_id = channel[0]['ID'].encode('utf-8')
			channel_video_count = channel[0]['emisije'].encode('utf-8')
			start_channel(channel_id,channel_video_count)

elif mode[0] == dir_search:
	videos = search_videos()
	list_search_or_recommended_videos(videos)

elif mode[0] == dir_settings:		
	xbmcaddon.Addon().openSettings()	
else:
	pass

