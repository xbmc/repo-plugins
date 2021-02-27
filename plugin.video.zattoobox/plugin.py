# coding=utf-8

##################################
# ZattooBox v1.0.8
# Kodi Addon for Zattoo
# (c) 2014-2021 Pascal Nançoz
# nancpasc@gmail.com
##################################

import sys, urlparse
import xbmcgui, xbmcaddon

#import ZBcore
from resources.lib.core.zapisession import ZapiSession
from resources.lib.core.zbaddonproxy import ZBAddonProxy

#import Extensions
ext_dict = {}
from resources.lib.extensions.livetv import LiveTV
ext_dict['LiveTV'] = LiveTV
from resources.lib.extensions.recordings import Recordings
ext_dict['Recordings'] = Recordings

#Main
kodi_addon = xbmcaddon.Addon()
args = dict(urlparse.parse_qsl(sys.argv[2][1:]))

zbAddonProxy = ZBAddonProxy(kodi_addon, sys.argv[0], int(sys.argv[1]))
zapiSession = ZapiSession(zbAddonProxy.StoragePath)

if zapiSession.init_session(kodi_addon.getSetting('username'), kodi_addon.getSetting('password')):

	if not 'ext' in args:
		#collect content from all extensions
		content = []
		for key, ext_class in ext_dict.items():
			instance = ext_class(zapiSession, zbAddonProxy)
			content.extend(instance.get_items())
		zbAddonProxy.add_directoryItems(content)

	else:
		#item activated
		ext_class = ext_dict[args['ext']](zapiSession, zbAddonProxy)
		ext_class.activate_item(args)
else:
	xbmcgui.Dialog().ok(kodi_addon.getAddonInfo('name'), kodi_addon.getLocalizedString(30902))