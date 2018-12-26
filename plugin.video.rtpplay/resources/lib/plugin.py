# -*- coding: utf-8 -*-

import routing
import logging
import requests
import inputstreamhelper
import re
import urllib
import xbmcaddon
from sys import exit, version_info
from resources.lib import kodiutils
from resources.lib import kodilogging
from xbmcgui import ListItem
from xbmcplugin import addDirectoryItem, endOfDirectory, setResolvedUrl
from channels import RTP_CHANNELS, HEADERS 


ADDON = xbmcaddon.Addon()
ICON = ADDON.getAddonInfo("icon")
logger = logging.getLogger(ADDON.getAddonInfo('id'))
kodilogging.config()
plugin = routing.Plugin()

@plugin.route('/')
def index():
	# Request dvr
    try:
		req = requests.get("http://www.rtp.pt/play/direto", headers=HEADERS).text
    except:
		pass

    match = re.compile('href="/play/direto/(.+?)".*?\n.+?\n.+?src="(.+?)".+?\n.+?\n.+?\n.+?\n.+?\n.+?\n.+?<h4>(.+?)</h4>').findall(req)
    
    for rtp_channel in RTP_CHANNELS:
		dvr = "Not available"
		progimg = ""
		for key, img, prog in match:
			if key.lower() == rtp_channel["id"]:
				dvr = prog
				if img.startswith("/"):
					img = "http:{}".format(img)
				progimg = img
				break

		liz = ListItem("[B][COLOR blue]{}[/B][/COLOR] ({})".format(kodiutils.smart_str(rtp_channel["name"]), kodiutils.smart_str(dvr)))
		liz.setArt({"thumb": progimg, "icon": progimg, "fanart": kodiutils.FANART})
		liz.setProperty('IsPlayable', 'true')
		liz.setInfo("Video", infoLabels={"plot": kodiutils.smart_str(dvr)})
		addDirectoryItem(
			plugin.handle,
			plugin.url_for(
				play,
				label=kodiutils.smart_str(rtp_channel["name"]),
				channel=kodiutils.smart_str(rtp_channel["id"]),
				img=kodiutils.smart_str(progimg),
				prog=kodiutils.smart_str(dvr)
			), liz, False)

    endOfDirectory(plugin.handle)


@plugin.route('/play')
def play():
	channel = plugin.args["channel"][0]
	name = plugin.args["label"][0]
	prog = plugin.args["prog"][0]

	icon = ICON
	if "img" in plugin.args:
		icon = plugin.args["img"][0]
	
	
	for rtp_channel in RTP_CHANNELS:
		if rtp_channel["id"] == channel:
			streams = rtp_channel["streams"]
			for stream in streams:
				if stream["type"] == "hls":
					if requests.head(stream["url"], headers=HEADERS).status_code == 200:
						liz = ListItem("[B][COLOR blue]{}[/B][/COLOR] ({})".format(kodiutils.smart_str(name), kodiutils.smart_str(prog)))
						liz.setArt({"thumb": icon, "icon": icon})
						liz.setProperty('IsPlayable', 'true')
						liz.setPath("{}|{}".format(stream["url"], urllib.urlencode(HEADERS)))
						setResolvedUrl(plugin.handle, True, liz)
						break
					else:
						continue
				elif stream["type"] == "dashwv":
					is_helper = inputstreamhelper.Helper('mpd', drm='com.widevine.alpha')
					if is_helper.check_inputstream():
						# Grab token
						src = requests.get(stream["tk"], headers=HEADERS).text
						tk = re.compile('k: \"(.+?)\"', re.DOTALL).findall(src)
						if tk:
							payload = '{"drm_info":[D{SSM}], "kid": "E13506F7439BEAE7DDF0489FCDDF7481", "token":"' + tk[0] + '"}'
							liz = ListItem("[B][COLOR blue]{}[/B][/COLOR] ({})".format(kodiutils.smart_str(name), kodiutils.smart_str(prog)))
							liz.setPath(stream["url"])
							liz.setProperty('inputstream.adaptive.license_type', 'com.widevine.alpha')
							liz.setProperty('inputstream.adaptive.manifest_type', 'mpd')
							liz.setProperty('inputstreamaddon', 'inputstream.adaptive')
							liz.setProperty('inputstream.adaptive.stream_headers', urllib.urlencode(HEADERS))
							liz.setMimeType('application/dash+xml')
							liz.setProperty('inputstream.adaptive.license_key', '{}|{}|{}|'.format(stream["license"], "Content-Type=application/json", urllib.quote(payload)))
							liz.setContentLookup(False)
							setResolvedUrl(plugin.handle, True, liz)

def raise_notification():
	kodiutils.ok(kodiutils.get_string(32000),kodiutils.get_string(32002))
	exit(0)

def run():
    plugin.run()
