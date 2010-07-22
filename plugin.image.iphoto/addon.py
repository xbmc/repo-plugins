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
db = IPhotoDB(xbmc.translatePath(os.path.join(addon.getAddonInfo("Profile"), "iphoto.db")))

def list_photos_in_event(params):
    global db
    rollid = params['rollid']
    media = db.GetMediaInRoll(rollid)
    for (caption, mediapath, thumbpath, originalpath, rating) in media:
	if (not mediapath):
	    mediapath = originalpath
	if (not thumbpath):
	    thumbpath = originalpath
	if (not caption):
	    caption = originalpath
	item = gui.ListItem(caption, thumbnailImage=thumbpath)
	plugin.addDirectoryItem(handle = int(sys.argv[1]), url=mediapath, listitem = item, isFolder = False)

def list_events(params):
    global db,BASE_URL
    rollid = 0
    try:
	# if we have an album id, only list tracks in the album
	rollid = params['rollid']
	return list_photos_in_event(params)
    except Exception, e:
	print str(e)
	pass
    rolls = db.GetRolls()
    if (not rolls):
	return
    for (rollid, name, thumb, rolldate, count) in rolls:
	item = gui.ListItem(name, thumbnailImage=thumb)
	item.setInfo(type="pictures", infoLabels={ "count": count })
	plugin.addDirectoryItem(handle = int(sys.argv[1]), url=BASE_URL+"?action=events&rollid=%s" % (rollid), listitem = item, isFolder = True)

def list_photos_in_album(params):
    global db
    albumid = params['albumid']
    media = db.GetMediaInAlbum(albumid)
    render_media(media)

def list_albums(params):
    global db,BASE_URL
    albumid = 0
    try:
	# if we have an album id, only list tracks in the album
	albumid = params['albumid']
	return list_photos_in_album(params)
    except Exception, e:
	print str(e)
	pass
    albums = db.GetAlbums()
    if (not albums):
	return
    for (albumid, name) in albums:
	if name == "Photos":
	    continue
	item = gui.ListItem(name)
	plugin.addDirectoryItem(handle = int(sys.argv[1]), url=BASE_URL+"?action=albums&albumid=%s" % (albumid), listitem = item, isFolder = True)

def list_photos_with_rating(params):
    global db
    rating = params['rating']
    media = db.GetMediaWithRating(rating)
    render_media(media)

def list_ratings(params):
    global db,BASE_URL,ICONS_PATH
    albumid = 0
    try:
	# if we have an album id, only list tracks in the album
	rating = params['rating']
	return list_photos_with_rating(params)
    except Exception, e:
	print str(e)
	pass
    for a in range(1,6):
	rating = addon.getLocalizedString(30200) % (a)
	item = gui.ListItem(rating, thumbnailImage=ICONS_PATH+"/star%d.png" % (a))
	plugin.addDirectoryItem(handle = int(sys.argv[1]), url=BASE_URL+"?action=ratings&rating=%d" % (a), listitem = item, isFolder = True)

def render_media(media):
    for (caption, mediapath, thumbpath, originalpath, rating) in media:
        if (not mediapath):
            mediapath = originalpath
        if (not thumbpath):
            thumbpath = originalpath
        if (not caption):
            caption = originalpath
        item = gui.ListItem(caption, thumbnailImage=thumbpath)
        plugin.addDirectoryItem(handle = int(sys.argv[1]), url=mediapath, listitem = item, isFolder = False)

def progress_callback(current, max):
    global BASE_URL
    item = gui.ListItem( ">>" )
    plugin.addDirectoryItem(handle = int(sys.argv[1]), url=BASE_URL, listitem = item, isFolder = False)

def import_library(filename):
    global db
    db.ResetDB()

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

    iparser = IPhotoParser(filename, db.AddAlbumNew, album_ign, db.AddRollNew, db.AddKeywordNew, db.AddMediaNew, progress_callback)
    try:
	iparser.Parse()
	db.UpdateLastImport()
    except:
	print traceback.print_exc()

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

def root_directory():
    global addon,ICONS_PATH,BASE_URL
    item = gui.ListItem(addon.getLocalizedString(30100), thumbnailImage=ICONS_PATH+"/events.png")
    item.setInfo( type="Picture", infoLabels={ "Title": "Events" })
    plugin.addDirectoryItem(handle = int(sys.argv[1]), url=BASE_URL+"?action=events", listitem = item, isFolder = True)

    item = gui.ListItem(addon.getLocalizedString(30101), thumbnailImage=ICONS_PATH+"/albums.png")
    item.setInfo( type="Picture", infoLabels={ "Title": "Albums" })
    plugin.addDirectoryItem(handle = int(sys.argv[1]), url=BASE_URL+"?action=albums", listitem = item, isFolder = True)

    item = gui.ListItem(addon.getLocalizedString(30102), thumbnailImage=ICONS_PATH+"/star.png")
    item.setInfo( type="Picture", infoLabels={ "Title": "Ratings" })
    plugin.addDirectoryItem(handle = int(sys.argv[1]), url=BASE_URL+"?action=ratings", listitem = item, isFolder = True)

    item = gui.ListItem(addon.getLocalizedString(30103), thumbnailImage=PLUGIN_PATH+"/icon.png")
    plugin.addDirectoryItem(handle = int(sys.argv[1]), url=BASE_URL+"?action=rescan", listitem = item, isFolder = True, totalItems=100)

def process_params(params):
    global os
    try:
	action = params['action']
    except:
	return root_directory()

    if (action == "events"):
	return list_events(params)
    elif (action == "albums"):
	return list_albums(params)
    elif (action == "ratings"):
	return list_ratings(params)
    elif (action == "rescan"):
	lib_filename = addon.getSetting('albumdata_xml_path')
	if (lib_filename == ""):
	    lib_filename = os.getenv("HOME") + "/Pictures/iPhoto Library/AlbumData.xml"
	    addon.setSetting('albumdata_xml_path', lib_filename)
	import_library(lib_filename)
	plugin.endOfDirectory(handle = int(sys.argv[1]), succeeded = False)
	sys.exit(0)

    root_directory()

if (__name__ == "__main__"):
    process_params(get_params(sys.argv[2]))
    plugin.endOfDirectory( handle = int(sys.argv[1]), succeeded = True)
