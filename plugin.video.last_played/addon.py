import sys
import json
import urllib
import urlparse
import xbmc
import xbmcplugin
import xbmcaddon
import xbmcvfs
from xbmcgui import ListItem
from xbmcplugin import addDirectoryItem, endOfDirectory

addon = xbmcaddon.Addon()
addon_handle = int(sys.argv[1])
args = urlparse.parse_qs(sys.argv[2][1:])
menu = args.get('menu', None)
try: list_size = int(addon.getSetting('list_size'))
except Exception: list_size=0
try: top_size = int(addon.getSetting('top_size'))
except Exception: top_size=0
single_list = addon.getSetting('single_list')
group_by = addon.getSetting('group_by')
show_date = addon.getSetting('show_date')
show_time = addon.getSetting('show_time')
enable_debug = addon.getSetting('enable_debug')
lang = addon.getLocalizedString
if addon.getSetting('custom_path_enable') == "true" and addon.getSetting('custom_path') != "":
	txtpath = addon.getSetting('custom_path').decode("utf-8")
else:
	txtpath = xbmc.translatePath(addon.getAddonInfo('profile')).decode("utf-8")
txtfile = txtpath + "lastPlayed.json"
oldfile = txtpath + "list.txt"
imgPath=xbmc.translatePath(xbmcaddon.Addon().getAddonInfo('path')).decode('utf-8')
group_by_type=lang(30018)

def url(pQuery):
	return sys.argv[0] + '?' + urllib.urlencode(pQuery)

def list_items(selGroup, nbrLines):
	xbmcplugin.setContent(addon_handle, "movies")
	if xbmcvfs.exists(txtfile):
		f = xbmcvfs.File(txtfile)
		nbr=1
		idx=0
		for line in json.load(f):
			if nbr>nbrLines: break
			if group_by == group_by_type: group = line["type"]
			else: group = line["source"]
			if len(line)>3 and (group==selGroup or selGroup=='*'):
				nbr=nbr+1
				desc=''
				if show_date == "true": desc = desc + line["date"].strip() + ' '
				if show_time == "true": desc = desc + line["time"].strip() + ' '
				desc=desc + line["title"]
				li = ListItem(label=desc)
				li.setInfo(type="Video", infoLabels={ "Title": desc})
				li.setProperty('IsPlayable', 'true')
				command = []
				command.append((lang(30008), "XBMC.RunPlugin(plugin://plugin.video.last_played?menu=remove&id="+str(idx)+")"))
				li.addContextMenuItems(command)
				li.setArt({ "poster" : line["thumbnail"].strip() })
				li.setArt({ "thumbnail" : line["thumbnail"].strip() })
				li.setArt({ "fanart" : line["fanart"].strip() })
				addDirectoryItem(addon_handle, line["file"].strip(), li, False)
			idx = idx + 1
		f.close()

def list_groups():
	if xbmcvfs.exists(txtfile):
		groups = []
		f = xbmcvfs.File(txtfile)
		try:
			lines = json.load(f);
		except Exception:
			lines = []
		for line in lines:
			if len(line)>5:
				if group_by == group_by_type:
					group = line["type"]
				else:
					group = line["source"]
				if group not in groups:
					groups.append(group)
					if group_by == group_by_type:
						nm = group
						ic = imgPath+'/resources/' + group + '.png'
					else:
						nm = group
						ads = group.split("/")
						if len(ads) > 2: nm = ads[2]
						try:
							la = xbmcaddon.Addon(nm)
							nm = la.getAddonInfo('name')
							ic = la.getAddonInfo('icon')
						except Exception:
							if group==lang(30002): ic = imgPath+'/resources/movie.png'
							elif group==lang(30003): ic = imgPath+'/resources/episode.png'
							elif group==lang(30004): ic = imgPath+'/resources/musicvideo.png'
							else: ic = imgPath+'/resources/addons.png'
					addDirectoryItem(addon_handle, url({'menu': group.encode("utf-8")}), ListItem(nm, iconImage=ic), True)
		f.close()
	if xbmcvfs.exists(oldfile):
		addDirectoryItem(addon_handle, url({'menu': 'oldlist'}), ListItem(lang(30019)), True)

def list_old_items(nbrLines):
	xbmcplugin.setContent(addon_handle, "movies")
	if xbmcvfs.exists(oldfile):
		f = xbmcvfs.File(oldfile)
		lines = f.readBytes().decode("utf-8")
		f.close()
		nbr=1
		for line in lines.split(chr(10)):
			if nbr>nbrLines: break
			item = line.split(chr(9))
			if len(item)>3:
				nbr=nbr+1
				desc=''
				if show_date == "true" and len(item)>4 : desc = desc + item[4].strip() + ' '
				if show_time == "true" and len(item)>5: desc = desc + item[5].strip() + ' '
				desc=desc + item[0]
				li = ListItem(label=desc)
				li.setProperty('IsPlayable', 'true')
				li.setInfo(type="Video", infoLabels={ "Title": desc})
				li.setArt({ "poster" : item[2].strip() })
				addDirectoryItem(addon_handle, item[1].strip(), li, False)

if menu is None or menu[0]=="top":
	if single_list == "true":
		list_items("*", list_size)
		list_old_items(list_size)
	else:
		xbmcplugin.setContent(addon_handle, "menu")
		list_items("*", top_size)
		list_groups()
	if enable_debug	== "true":
		addDirectoryItem(addon_handle, url({'menu': 'showlist'}), ListItem(lang(30014)), True)
		if xbmcvfs.exists(txtfile):
			addDirectoryItem(addon_handle, url({'menu': 'deletelist'}), ListItem(lang(30015)), True)
		else:
			addDirectoryItem(addon_handle, url({'menu': 'deletelist'}), ListItem(lang(30016)), True)
	endOfDirectory(addon_handle)
elif menu[0] == 'remove':
	lid = args.get('id', None)
	if xbmcvfs.exists(txtfile) and lid is not None:
		f = xbmcvfs.File(txtfile)
		lines = json.load(f)
		f.close()
		osz = len(lines)
		lines.remove(lines[int(lid[0])])
		# to avoid accidental cleaning, update empty file only it had only one line before
		if len(lines)>0 or osz==1:
			f = xbmcvfs.File(txtfile, 'w')
			json.dump(lines, f)
			f.close()
		xbmc.executebuiltin("ActivateWindow(Videos,plugin://plugin.video.last_played?menu=top)")
elif menu[0] == 'showlist':
	if xbmcvfs.exists(txtfile):
		f = xbmcvfs.File(txtfile)
		lines = json.load(f)
		f.close()
		for line in lines:
			addDirectoryItem(addon_handle, url({}), ListItem(str(line)), False)
		endOfDirectory(addon_handle)
elif menu[0] == 'deletelist':
	if xbmcvfs.exists(txtfile):
		lines = []
		f = xbmcvfs.File(txtfile, 'w')
		json.dump(lines, f)
		f.close()
elif menu[0] == 'oldlist':
	list_old_items(list_size)
	endOfDirectory(addon_handle)
else:
	list_items(menu[0], list_size)
	endOfDirectory(addon_handle)
