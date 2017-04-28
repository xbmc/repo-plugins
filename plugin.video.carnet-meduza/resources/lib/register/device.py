# -*- coding: utf-8 -*-
import os, sys, string, random, platform
import urllib, urlparse, json
import requests
import xbmc, xbmcaddon,xbmcgui
import mechanize
from mechanize import Browser
from classes.memstorage import Storage
from classes.memstorage import MemStorage #tnx/credit: http://romanvm.github.io/script.module.simpleplugin/storage.html

def gen_key():
	"""Returns unique 140 char long string that emulates device id - api key"""
	# ex: Linux
	os_name = platform.system()
	# generate 140 char device id (a.k.a. api key)
	rnd_str = ''.join(random.choice(string.ascii_letters+string.digits) for x in range(140))
	combo_str = 'kodi' + os_name + rnd_str
	# remove non alpha-numeric chars and truncate to 140 
	uniq_key = ''.join(char for char in combo_str if char.isalnum())[:140]
	return uniq_key

def store_key():
	"""Persistently keep api key and registration status (not/is) in userdata/storage.pcl file
	and return stored key and the status"""
	#gen/set/get uniq key == device_id == api_key
	#get addon userdata special:// and then translate to full path
	userdata_path_special = xbmcaddon.Addon().getAddonInfo('profile').decode('utf-8')
	userdata_path = xbmc.translatePath(userdata_path_special)
	# Create a storage object
	with Storage(userdata_path) as key_store: 
		#check if file used as key storage exists
		if not key_store:
			#handle if file is deleted but not the userdata dir
			if not os.path.exists(userdata_path):
				os.mkdir(userdata_path) 
			uniq_key = gen_key() # gen key only if key_store empty (once)
			key_store['uniq_key'] = uniq_key # store object
			key_store['reg_dev_status'] = 'not_reg'
		key = key_store['uniq_key']
		reg_dev_status = key_store['reg_dev_status']
	return (key, reg_dev_status)

# register device
def dev_reg(device_id):
	"""Returns the url that server responded with after registration attempt"""
	# get user info from settings
	aai_password = get_pwd()
	api_base_url = 'https://meduza.carnet.hr/index.php/login/mobile/?device='
	# for some reason, it start at 2 {'Tablet':'2', 'Smartphone':'3', 'SmartTV':'4'}
	device_type = int(addon.getSetting('device_type')) + 2
	# get number corresponding to device type from settings
	#device_type_num = device_type_dict[device_type_name]
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
"""Takes response from reg_dev, along with api key"""
def check_reg(response, device_id):
	response_parsed = urlparse.urlparse(response)
	# if reponse doesn't return proper status reponse due to wrong usually username/password entry 
	# catch keyError and pop custom message
	try:
		response_code = urlparse.parse_qs(response_parsed.query)['status'][0]
		# 200 means that 'device' was successfully registered with SP and device UID can be stored in the settings
		if response_code == '200':
			addon.setSetting('apikey',device_id)
			user_info(device_id)
			info_dialog_msg = addon.getLocalizedString(30209) 
			xbmcgui.Dialog(info_dialog_msg)	
			#get addon userdata special:// and then translate to full path
			userdata_path_special = xbmcaddon.Addon().getAddonInfo('profile').decode('utf-8')
			userdata_path = xbmc.translatePath(userdata_path_special)
			# Create a storage object
			with Storage(userdata_path) as key_store: 
				key_store['reg_dev_status'] = 'is_reg'
		else: 
			ret_codes = {'100':30215, '300':30216, '400':30217, '401':30218}
			ret_message = addon.getLocalizedString(ret_codes[response_code])
			xbmcgui.Dialog(ret_message)
	except KeyError:
		sso_err_msg = addon.getLocalizedString(30219)
		xbmcgui.Dialog(sso_err_msg)

def get_pwd():
	"""Storing SSO password is not best way to go, so just get the it, when needed. Returns entered password."""
	heading_msg = addon.getLocalizedString(30210) 
	keyboard = xbmc.Keyboard()
	keyboard.setHeading(heading_msg)
	keyboard.setHiddenInput(True) 
	keyboard.doModal()
	if (keyboard.isConfirmed()):
		enter_pwd = keyboard.getText()
		if enter_pwd is None or len(str(enter_pwd)) == 0:
			info_dialog_msg = addon.getLocalizedString(30211)
			xbmcgui.Dialog(info_dialog_msg)
	del keyboard
	return enter_pwd

# pre run check (make api requests for content) 
def pre_run():
	"""When addon is started, checks if registration status is valid."""
	# request target resource, discover IdP and redirect to SSO service
	request_url = 'https://meduza.carnet.hr/index.php/api/registered/?uid=' + api_key
	r = requests.get(request_url)
	registered_status = r.json()['code']
	if registered_status == 200:
		success_msg = addon.getLocalizedString(30212)
		xbmcgui.Dialog(r.json()['message'] + success_msg)
	else:
		error_msg = addon.getLocalizedString(30213)
		xbmcgui.Dialog(error_msg)


# get user info and populate the settings.xml
def user_info(api_key):
	"""Once more, it takes api key, gets user info from the CM server and stores it to settings."""
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

addon=xbmcaddon.Addon('plugin.video.carnet-meduza')

#MemStorage does not allow to modify mutable objects in-place. You need to assign them to variables first, modify and then store them back to a MemStorage instance.
tmp_store = MemStorage('ts')

# get username/apikey from settings
aai_username = addon.getSetting('aai_username')

api_key, dev_reg_status = store_key()
addon.setSetting('apikey',api_key)

#if api_key  == '':
		# if aai_username missing open settings, otherwise  start device registration
if not aai_username and dev_reg_status == 'not_reg':
	info_dialog_msg = addon.getLocalizedString(30214)
	xbmcgui.Dialog(info_dialog_msg)
	xbmcgui.Dialog()	
	xbmcaddon.Addon().openSettings()	

elif dev_reg_status == 'not_reg':
	reg_response = dev_reg(api_key)
	check_reg(reg_response, api_key)

#check if device is registered (pre_run) only once
elif not tmp_store:
	pre_run()
	tmp_store['run_once'] = 1

