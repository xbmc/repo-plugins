# -*- coding: utf-8 -*-
import requests
import xbmcgui
import xbmcaddon
import json
import libmediathek4utils as lm4utils

base = 'https://api.tenant-group.frontend.vod.filmwerte.de/v7/'
providerBase = 'https://api.tenant.frontend.vod.filmwerte.de/v11/'

def pick():
	j = requests.get(f'{base}fba2f8b5-6a3a-4da3-b555-21613a88d3ef/sign-in').json()
	l = []
	for item in j['tenants']:
		l.append(xbmcgui.ListItem(f'{item["displayCategory"]} - {item["displayName"]}'))
	i = xbmcgui.Dialog().select(lm4utils.getTranslation(30010), l) 

	domain = j['tenants'][int(i)]['clients']['web']['domain']
	tenant = j['tenants'][int(i)]['id']
	library = j['tenants'][int(i)]['displayName']

	username = xbmcgui.Dialog().input(lm4utils.getTranslation(30500)) 
	if username == '':
		lm4utils.displayMsg(lm4utils.getTranslation(30501), lm4utils.getTranslation(30502))
		return

	password = xbmcgui.Dialog().input(lm4utils.getTranslation(30503)) 
	if password == '':
		lm4utils.displayMsg(lm4utils.getTranslation(30504), lm4utils.getTranslation(30505))
		return

	r = requests.get(f'{providerBase}{tenant}/sign-in')
	if r.text == '':
		lm4utils.displayMsg(lm4utils.getTranslation(30506), lm4utils.getTranslation(30507))
		return

	j = r.json()
	provider = j['delegated'][0]['provider']
	client_id = f'tenant-{tenant}-filmwerte-vod-frontend'

	files = {'client_id':(None, client_id),'provider':(None, provider),'username':(None, username),'password':(None, password),'scope':(None, 'filmwerte-vod-api offline_access')}
	j = requests.post('http://api.vod.filmwerte.de/connect/authorize-external', files=files).json()
	if 'error' in j:
		if j['error'] == 'InvalidCredentials':
			lm4utils.displayMsg(lm4utils.getTranslation(30506), lm4utils.getTranslation(30508))
		else:
			lm4utils.displayMsg(lm4utils.getTranslation(30506), lm4utils.getTranslation(30507))
		return

	lm4utils.setSetting('domain', domain)
	lm4utils.setSetting('tenant', tenant)
	lm4utils.setSetting('library', library)
	lm4utils.setSetting('username', username)
	lm4utils.setSetting('access_token', j['access_token'])
	lm4utils.setSetting('refresh_token', j['refresh_token'])
	