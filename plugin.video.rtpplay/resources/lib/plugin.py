# -*- coding: utf-8 -*-

import routing
import logging
import requests
import re
import xbmcaddon
from sys import exit, version_info
from resources.lib import kodiutils
from resources.lib import kodilogging
from xbmcgui import ListItem
from xbmcplugin import addDirectoryItem, endOfDirectory, setResolvedUrl


ADDON = xbmcaddon.Addon()
logger = logging.getLogger(ADDON.getAddonInfo('id'))
kodilogging.config()
plugin = routing.Plugin()

__headers__ = {"User-Agent": "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36"}
__base_url__ = "http://www.rtp.pt"
__session__ = requests.Session()

if version_info >= (3, 0):
	from html.parser import HTMLParser
else:
	from HTMLParser import HTMLParser
html_parser = HTMLParser()


@plugin.route('/')
def index():
	try:
		req = __session__.get("http://www.rtp.pt/play/", headers=__headers__).text
	except:
		kodiutils.ok(kodiutils.get_string(32000),kodiutils.get_string(32001))
		exit(0)

	match=re.compile('<a title=".+?direto (.+?)" href="(.+?)".+?img.+?src="(.+?)" class="img-responsive">.+?<span class="small"><b>(.+?)</b>').findall(req)
	if match:
		for channel,rel_url, img, prog in match:
			liz = ListItem("[B][COLOR blue]{}[/B][/COLOR] ({})".format(kodiutils.smart_str(channel), kodiutils.smart_str(prog)))
			if img.startswith("/"):
				img = "http:{}".format(img)
			
			liz.setArt({"thumb": img, "icon": img, "fanart": kodiutils.FANART})
			liz.setProperty('IsPlayable', 'true')
			liz.setInfo("Video", infoLabels={"plot": html_parser.unescape(kodiutils.smart_str(prog))})
			
			addDirectoryItem(plugin.handle, plugin.url_for(play, rel_url=kodiutils.smart_str(rel_url), channel=kodiutils.smart_str(channel), img=kodiutils.smart_str(img), prog=kodiutils.smart_str(prog) ), liz, False)
	
	endOfDirectory(plugin.handle)


@plugin.route('/play')
def play():
	rel_url = plugin.args["rel_url"][0]
	channel = plugin.args["channel"][0]
	prog = plugin.args["prog"][0]
	icon = plugin.args["img"][0]
	try:
		req = __session__.get("{}{}".format(__base_url__, rel_url)).text
	except:
		kodiutils.ok(kodiutils.get_string(32000),kodiutils.get_string(32002))
		exit(0)

	is_pseudo_aes = bool(re.findall("var aes = true", req))

	player = re.findall("liveMetadata.+?'(\d+)'\)", req) 
	player = player[0].strip() if player else ''

	streams = re.compile('{} =.+?RTPPlayer.+?file\:.+?"(.+?)"'.format(player),re.DOTALL).findall(req)

	if streams:
		final_stream_url = None
		for stream in streams:
			if ".m3u8" in stream.split('/')[-1]: 
				final_stream_url = stream
				break

	if is_pseudo_aes:
		try:
			req = __session__.post("http://www.rtp.pt/services/playRequest.php", headers={"RTPPlayUrl":	final_stream_url})
			final_stream_url = req.headers["RTPPlayWW"]
		except:
			kodiutils.ok(kodiutils.get_string(32000),kodiutils.get_string(32002))
			exit(0)		

	if final_stream_url:
		liz = ListItem("[B][COLOR blue]{}[/B][/COLOR] ({})".format(kodiutils.smart_str(channel), kodiutils.smart_str(prog)))
		liz.setArt({"thumb": icon, "icon": icon})
		liz.setProperty('IsPlayable', 'true')
		liz.setPath("{}|User-Agent=Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36&Referer=http://www.rtp.pt/play/".format(final_stream_url))
		setResolvedUrl(plugin.handle, True, liz)
	else:
		kodiutils.ok(kodiutils.get_string(32000),kodiutils.get_string(32002))
		exit(0)

def run():
    plugin.run()
