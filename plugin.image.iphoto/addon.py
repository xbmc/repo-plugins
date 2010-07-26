"""
    Plugin for importing iPhoto library
"""

__plugin__ = "iPhoto"
__author__ = "jingai <jingai@floatingpenguins.com>"
__credits__ = "Anoop Menon, Nuka1195, JMarshal, jingai"
__url__ = "git://github.com/jingai/plugin.image.iphoto.git"

import sys
import os
import os.path

BASE_URL = "%s" % (sys.argv[0])
PLUGIN_PATH = xbmc.translatePath(os.getcwd())
RESOURCE_PATH = os.path.join(PLUGIN_PATH, "resources")
ICONS_PATH = os.path.join(RESOURCE_PATH, "icons")
LIB_PATH = os.path.join(RESOURCE_PATH, "lib")
sys.path.append(LIB_PATH)

import xbmc
import xbmcgui as gui
import xbmcplugin as plugin
import xbmcaddon
addon = xbmcaddon.Addon(id=os.path.basename(os.getcwd()))

from resources.lib.iphoto_parser import *
db_file = xbmc.translatePath(os.path.join(addon.getAddonInfo("Profile"), "iphoto.db"))
db = IPhotoDB(db_file)

def list_photos_in_event(params):
    global db

    rollid = params['rollid']
    media = db.GetMediaInRoll(rollid)
    n = 0
    for (caption, mediapath, thumbpath, originalpath, rating) in media:
	if (not mediapath):
	    mediapath = originalpath
	if (not thumbpath):
	    thumbpath = originalpath
	if (not caption):
	    caption = originalpath
	item = gui.ListItem(caption, thumbnailImage=thumbpath)
	plugin.addDirectoryItem(handle = int(sys.argv[1]), url=mediapath, listitem = item, isFolder = False)
	n += 1

    return n

def list_events(params):
    global db,BASE_URL

    rollid = 0
    try:
	rollid = params['rollid']
	return list_photos_in_event(params)
    except Exception, e:
	print str(e)
	pass

    rolls = db.GetRolls()
    if (not rolls):
	return

    n = 0
    for (rollid, name, thumb, rolldate, count) in rolls:
	item = gui.ListItem(name, thumbnailImage=thumb)
	item.setInfo(type="pictures", infoLabels={ "count": count })
	plugin.addDirectoryItem(handle = int(sys.argv[1]), url=BASE_URL+"?action=events&rollid=%s" % (rollid), listitem = item, isFolder = True)
	n += 1

    return n

def render_media(media):
    n = 0
    for (caption, mediapath, thumbpath, originalpath, rating) in media:
	if (not mediapath):
	    mediapath = originalpath
	if (not thumbpath):
	    thumbpath = originalpath
	if (not caption):
	    caption = originalpath
	item = gui.ListItem(caption, thumbnailImage=thumbpath)
	plugin.addDirectoryItem(handle = int(sys.argv[1]), url=mediapath, listitem = item, isFolder = False)
	n += 1

    return n

def list_photos_in_album(params):
    global db

    albumid = params['albumid']
    media = db.GetMediaInAlbum(albumid)
    return render_media(media)

def list_albums(params):
    global db,BASE_URL

    albumid = 0
    try:
	albumid = params['albumid']
	return list_photos_in_album(params)
    except Exception, e:
	print str(e)
	pass

    albums = db.GetAlbums()
    if (not albums):
	return

    n = 0
    for (albumid, name) in albums:
	if name == "Photos":
	    continue
	item = gui.ListItem(name)
	plugin.addDirectoryItem(handle = int(sys.argv[1]), url=BASE_URL+"?action=albums&albumid=%s" % (albumid), listitem = item, isFolder = True)
	n += 1

    return n

def list_photos_with_rating(params):
    global db

    rating = params['rating']
    media = db.GetMediaWithRating(rating)
    return render_media(media)

def list_ratings(params):
    global db,BASE_URL,ICONS_PATH

    albumid = 0
    try:
	rating = params['rating']
	return list_photos_with_rating(params)
    except Exception, e:
	print str(e)
	pass

    n = 0
    for a in range(1,6):
	rating = addon.getLocalizedString(30200) % (a)
	item = gui.ListItem(rating, thumbnailImage=ICONS_PATH+"/star%d.png" % (a))
	plugin.addDirectoryItem(handle = int(sys.argv[1]), url=BASE_URL+"?action=ratings&rating=%d" % (a), listitem = item, isFolder = True)
	n += 1

    return n

def progress_callback(progress_dialog, nphotos, ntotal):
    if (not progress_dialog):
	return 0
    if (progress_dialog.iscanceled()):
	return

    nphotos += 1
    percent = int(float(nphotos * 100) / ntotal)
    progress_dialog.update(percent, addon.getLocalizedString(30211) % (nphotos))
    return nphotos

def import_library(xmlfile):
    global db,db_file

    db_tmp_file = db_file + ".tmp"
    db_tmp = IPhotoDB(db_tmp_file)
    db_tmp.ResetDB()

    album_ign = []
    album_ign.append("Book")
    album_ign.append("Selected Event Album")

    album_ign_publ = addon.getSetting('album_ignore_published')
    if (album_ign_publ == ""):
	addon.setSetting('album_ignore_published', 'true')
	album_ign_publ = "true"
    if (album_ign_publ == "true"):
	album_ign.append("Published")

    album_ign_flagged = addon.getSetting('album_ignore_flagged')
    if (album_ign_flagged == ""):
	addon.setSetting('album_ignore_flagged', 'true')
	album_ign_flagged = "true"
    if (album_ign_flagged == "true"):
	album_ign.append("Shelf")

    progress_dialog = gui.DialogProgress()
    try:
	progress_dialog.create(addon.getLocalizedString(30210))
    except:
	print traceback.print_exc()
	os.remove(db_file_tmp)
	return

    progress_dialog.update(0, addon.getLocalizedString(30211) % (0))

    iparser = IPhotoParser(xmlfile, db_tmp.AddAlbumNew, album_ign, db_tmp.AddRollNew, db_tmp.AddKeywordNew, db_tmp.AddMediaNew, progress_callback, progress_dialog)
    try:
	iparser.Parse()
	db_tmp.UpdateLastImport()
    except:
	print traceback.print_exc()
    else:
	if (not progress_dialog.iscanceled()):
	    try:
		os.rename(db_tmp_file, db_file)
		db = db_tmp
	    except:
		print traceback.print_exc()

    try:
	os.remove(db_tmp_file)
    except:
	pass

    progress_dialog.close()

def get_params(paramstring):
    params = {}
    paramstring = str(paramstring).strip()
    paramstring = paramstring.lstrip("?")
    if (not paramstring):
	return params
    paramlist = paramstring.split("&")
    for param in paramlist:
	(k,v) = param.split("=")
	params[k] = v
    print params
    return params

if (__name__ == "__main__"):
    xmlfile = addon.getSetting('albumdata_xml_path')
    if (xmlfile == ""):
	xmlfile = os.getenv("HOME") + "/Pictures/iPhoto Library/AlbumData.xml"
	addon.setSetting('albumdata_xml_path', xmlfile)

    try:
	params = get_params(sys.argv[2])
	action = params['action']
    except:
	# main menu
	try:
	    item = gui.ListItem(addon.getLocalizedString(30100), thumbnailImage=ICONS_PATH+"/events.png")
	    item.setInfo("Picture", { "Title": "Events" })
	    plugin.addDirectoryItem(int(sys.argv[1]), BASE_URL+"?action=events", item, True)
	    item = gui.ListItem(addon.getLocalizedString(30101), thumbnailImage=ICONS_PATH+"/albums.png")
	    item.setInfo("Picture", { "Title": "Albums" })
	    plugin.addDirectoryItem(int(sys.argv[1]), BASE_URL+"?action=albums", item, True)
	    item = gui.ListItem(addon.getLocalizedString(30102), thumbnailImage=ICONS_PATH+"/star.png")
	    item.setInfo("Picture", { "Title": "Ratings" })
	    plugin.addDirectoryItem(int(sys.argv[1]), BASE_URL+"?action=ratings", item, True)
	    item = gui.ListItem(addon.getLocalizedString(30103), thumbnailImage=PLUGIN_PATH+"/icon.png")
	    plugin.addDirectoryItem(int(sys.argv[1]), BASE_URL+"?action=rescan", item, False)
	except:
	    plugin.endOfDirectory(int(sys.argv[1]), False)
	else:
	    plugin.endOfDirectory(int(sys.argv[1]), True)

	# automatically update library if desired
	auto_update_lib = addon.getSetting('auto_update_lib')
	if (auto_update_lib == ""):
	    addon.setSetting('auto_update_lib', 'false')
	    auto_update_lib = "false"
	if (auto_update_lib == "true"):
	    try:
		xml_mtime = os.path.getmtime(xmlfile)
		db_mtime = os.path.getmtime(db_file)
	    except Exception, e:
		print str(e)
		pass
	    else:
		if (xml_mtime > db_mtime):
		    import_library(xmlfile)
    else:
	if (action == "events"):
	    items = list_events(params)
	elif (action == "albums"):
	    items = list_albums(params)
	elif (action == "ratings"):
	    items = list_ratings(params)
	elif (action == "rescan"):
	    items = import_library(xmlfile)

	if (items):
	    plugin.endOfDirectory(int(sys.argv[1]), True)
