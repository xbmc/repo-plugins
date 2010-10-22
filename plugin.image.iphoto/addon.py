"""
    Plugin for importing iPhoto library
"""

__plugin__ = "iPhoto"
__author__ = "jingai <jingai@floatingpenguins.com>"
__credits__ = "Anoop Menon, Nuka1195, JMarshal, jingai"
__url__ = "git://github.com/jingai/plugin.image.iphoto.git"

import sys
import time
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

apple_epoch = 978307200

def render_media(media):
    sort_date = False
    n = 0
    for (caption, mediapath, thumbpath, originalpath, rating, mediadate, mediasize) in media:
	if (not mediapath):
	    mediapath = originalpath
	if (not thumbpath):
	    thumbpath = mediapath
	if (not caption):
	    caption = mediapath

	if (caption):
	    # < r34717 doesn't support unicode thumbnail paths
	    try:
		item = gui.ListItem(caption, thumbnailImage=thumbpath)
	    except:
		item = gui.ListItem(caption)

	    try:
		item_date = time.strftime("%d.%m.%Y", time.localtime(apple_epoch + float(mediadate)))
		#item.setInfo(type="pictures", infoLabels={ "size": mediasize, "date": item_date })
		#sort_date = True
	    except:
		pass

	    plugin.addDirectoryItem(handle = int(sys.argv[1]), url = mediapath, listitem = item, isFolder = False)
	    n += 1

    plugin.addSortMethod(int(sys.argv[1]), plugin.SORT_METHOD_UNSORTED)
    plugin.addSortMethod(int(sys.argv[1]), plugin.SORT_METHOD_LABEL)
    if sort_date == True:
	plugin.addSortMethod(int(sys.argv[1]), plugin.SORT_METHOD_DATE)
    return n

def list_photos_in_album(params):
    global db

    albumid = params['albumid']
    media = db.GetMediaInAlbum(albumid)
    return render_media(media)

def list_albums(params, ign_empty):
    global db, BASE_URL

    albumid = 0
    try:
	albumid = params['albumid']
	return list_photos_in_album(params)
    except Exception, e:
	print to_str(e)
	pass

    albums = db.GetAlbums()
    if (not albums):
	return

    n = 0
    for (albumid, name, count) in albums:
	if (name == "Photos"):
	    continue

	if (not count and ign_empty == "true"):
	    continue

	item = gui.ListItem(name)
	if (count):
	    item.setInfo(type="pictures", infoLabels={ "count": count })
	plugin.addDirectoryItem(handle = int(sys.argv[1]), url=BASE_URL+"?action=albums&albumid=%s" % (albumid), listitem = item, isFolder = True)
	n += 1

    plugin.addSortMethod(int(sys.argv[1]), plugin.SORT_METHOD_UNSORTED)
    plugin.addSortMethod(int(sys.argv[1]), plugin.SORT_METHOD_LABEL)
    return n

def list_photos_in_event(params):
    global db

    rollid = params['rollid']
    media = db.GetMediaInRoll(rollid)
    return render_media(media)

def list_events(params, ign_empty):
    global db, BASE_URL

    rollid = 0
    try:
	rollid = params['rollid']
	return list_photos_in_event(params)
    except Exception, e:
	print to_str(e)
	pass

    rolls = db.GetRolls()
    if (not rolls):
	return

    sort_date = False
    n = 0
    for (rollid, name, thumbpath, rolldate, count) in rolls:
	if (not count and ign_empty == "true"):
	    continue

	# < r34717 doesn't support unicode thumbnail paths
	try:
	    item = gui.ListItem(name, thumbnailImage=thumbpath)
	except:
	    item = gui.ListItem(name)

	try:
	    item_date = time.strftime("%d.%m.%Y", time.localtime(apple_epoch + float(rolldate)))
	    item.setInfo(type="pictures", infoLabels={ "date": item_date })
	    sort_date = True
	except:
	    pass

	if (count):
	    item.setInfo(type="pictures", infoLabels={ "count": count })
	plugin.addDirectoryItem(handle = int(sys.argv[1]), url=BASE_URL+"?action=events&rollid=%s" % (rollid), listitem = item, isFolder = True)
	n += 1

    plugin.addSortMethod(int(sys.argv[1]), plugin.SORT_METHOD_UNSORTED)
    plugin.addSortMethod(int(sys.argv[1]), plugin.SORT_METHOD_LABEL)
    if (sort_date == True):
	plugin.addSortMethod(int(sys.argv[1]), plugin.SORT_METHOD_DATE)
    return n

def list_photos_with_face(params):
    global db

    faceid = params['faceid']
    media = db.GetMediaWithFace(faceid)
    return render_media(media)

def list_faces(params, ign_empty):
    global db, BASE_URL

    faceid = 0
    try:
	faceid = params['faceid']
	return list_photos_with_face(params)
    except Exception, e:
	print to_str(e)
	pass

    faces = db.GetFaces()
    if (not faces):
	return

    n = 0
    for (faceid, name, thumbpath, count) in faces:
	if (not count and ign_empty == "true"):
	    continue

	# < r34717 doesn't support unicode thumbnail paths
	try:
	    item = gui.ListItem(name, thumbnailImage=thumbpath)
	except:
	    item = gui.ListItem(name)

	if (count):
	    item.setInfo(type="pictures", infoLabels={ "count": count })
	plugin.addDirectoryItem(handle = int(sys.argv[1]), url=BASE_URL+"?action=faces&faceid=%s" % (faceid), listitem = item, isFolder = True)
	n += 1

    plugin.addSortMethod(int(sys.argv[1]), plugin.SORT_METHOD_UNSORTED)
    plugin.addSortMethod(int(sys.argv[1]), plugin.SORT_METHOD_LABEL)
    return n

def list_photos_with_keyword(params):
    global db

    keywordid = params['keywordid']
    media = db.GetMediaWithKeyword(keywordid)
    return render_media(media)

def list_keywords(params, ign_empty):
    global db, BASE_URL

    keywordid = 0
    try:
	keywordid = params['keywordid']
	return list_photos_with_keyword(params)
    except Exception, e:
	print to_str(e)
	pass

    keywords = db.GetKeywords()
    if (not keywords):
	return

    hidden_keywords = addon.getSetting('hidden_keywords')

    n = 0
    for (keywordid, name, count) in keywords:
	if (name in hidden_keywords):
	    continue

	if (not count and ign_empty == "true"):
	    continue

	item = gui.ListItem(name)
	item.addContextMenuItems([(addon.getLocalizedString(30214), "XBMC.RunPlugin(\""+BASE_URL+"?action=hidekeyword&keyword=%s\")" % (name),)])
	if (count):
	    item.setInfo(type="pictures", infoLabels={ "count": count })
	plugin.addDirectoryItem(handle = int(sys.argv[1]), url=BASE_URL+"?action=keywords&keywordid=%s" % (keywordid), listitem = item, isFolder = True)
	n += 1

    if (n > 0):
	plugin.addSortMethod(int(sys.argv[1]), plugin.SORT_METHOD_UNSORTED)
	plugin.addSortMethod(int(sys.argv[1]), plugin.SORT_METHOD_LABEL)
    return n

def list_photos_with_rating(params):
    global db

    rating = params['rating']
    media = db.GetMediaWithRating(rating)
    return render_media(media)

def list_ratings(params):
    global db, BASE_URL, ICONS_PATH

    albumid = 0
    try:
	rating = params['rating']
	return list_photos_with_rating(params)
    except Exception, e:
	print to_str(e)
	pass

    n = 0
    for a in range(1,6):
	rating = addon.getLocalizedString(30200) % (a)
	item = gui.ListItem(rating, thumbnailImage=ICONS_PATH+"/star%d.png" % (a))
	plugin.addDirectoryItem(handle = int(sys.argv[1]), url=BASE_URL+"?action=ratings&rating=%d" % (a), listitem = item, isFolder = True)
	n += 1

    plugin.addSortMethod(int(sys.argv[1]), plugin.SORT_METHOD_UNSORTED)
    plugin.addSortMethod(int(sys.argv[1]), plugin.SORT_METHOD_LABEL)
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
    global db

    db.ResetDB()

    # always ignore Books and currently selected album
    album_ign = []
    album_ign.append("Book")
    album_ign.append("Selected Event Album")

    # ignore albums published to MobileMe if configured to do so
    album_ign_publ = addon.getSetting('album_ignore_published')
    if (album_ign_publ == ""):
	addon.setSetting('album_ignore_published', 'true')
	album_ign_publ = "true"
    if (album_ign_publ == "true"):
	album_ign.append("Published")

    # ignore flagged albums if configured to do so
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
    else:
	iparser = IPhotoParser(xmlfile, db.AddAlbumNew, album_ign, db.AddRollNew, db.AddFaceNew, db.AddKeywordNew, db.AddMediaNew, progress_callback, progress_dialog)

	progress_dialog.update(0, addon.getLocalizedString(30212))
	try:
	    iparser.Parse()
	    db.UpdateLastImport()
	except:
	    print traceback.print_exc()

    progress_dialog.close()

def hide_keyword(params):
    try:
	keyword = params['keyword']
	hidden_keywords = addon.getSetting('hidden_keywords')
	if (hidden_keywords != ""):
	    hidden_keywords += " "
	hidden_keywords += keyword
	addon.setSetting('hidden_keywords', hidden_keywords)
	print "JSL: HIDDEN KEYWORDS '%s'" % (hidden_keywords)
    except Exception, e:
	print to_str(e)
	pass

    xbmc.executebuiltin("Container.Refresh")

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

def add_import_lib_context_item(item):
    item.addContextMenuItems([(addon.getLocalizedString(30213), "XBMC.RunPlugin(\""+BASE_URL+"?action=rescan\")",)])

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
	    add_import_lib_context_item(item)
	    plugin.addDirectoryItem(int(sys.argv[1]), BASE_URL+"?action=events", item, True)

	    item = gui.ListItem(addon.getLocalizedString(30101), thumbnailImage=ICONS_PATH+"/albums.png")
	    item.setInfo("Picture", { "Title": "Albums" })
	    add_import_lib_context_item(item)
	    plugin.addDirectoryItem(int(sys.argv[1]), BASE_URL+"?action=albums", item, True)

	    item = gui.ListItem(addon.getLocalizedString(30105), thumbnailImage=ICONS_PATH+"/faces.png")
	    item.setInfo("Picture", { "Title": "Faces" })
	    add_import_lib_context_item(item)
	    plugin.addDirectoryItem(int(sys.argv[1]), BASE_URL+"?action=faces", item, True)

	    item = gui.ListItem(addon.getLocalizedString(30104), thumbnailImage=ICONS_PATH+"/keywords.png")
	    item.setInfo("Picture", { "Title": "Keywords" })
	    add_import_lib_context_item(item)
	    plugin.addDirectoryItem(int(sys.argv[1]), BASE_URL+"?action=keywords", item, True)

	    item = gui.ListItem(addon.getLocalizedString(30102), thumbnailImage=ICONS_PATH+"/star.png")
	    item.setInfo("Picture", { "Title": "Ratings" })
	    add_import_lib_context_item(item)
	    plugin.addDirectoryItem(int(sys.argv[1]), BASE_URL+"?action=ratings", item, True)

	    hide_import_lib = addon.getSetting('hide_import_lib')
	    if (hide_import_lib == ""):
		addon.setSetting('hide_import_lib', 'false')
		hide_import_lib = "false"
	    if (hide_import_lib == "false"):
		item = gui.ListItem(addon.getLocalizedString(30103), thumbnailImage=PLUGIN_PATH+"/icon.png")
		plugin.addDirectoryItem(int(sys.argv[1]), BASE_URL+"?action=rescan", item, False)
	except:
	    plugin.endOfDirectory(int(sys.argv[1]), False)
	else:
	    plugin.addSortMethod(int(sys.argv[1]), plugin.SORT_METHOD_NONE)
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
		print to_str(e)
		pass
	    else:
		if (xml_mtime > db_mtime):
		    import_library(xmlfile)
    else:
	# ignore empty albums if configured to do so
	album_ign_empty = addon.getSetting('album_ignore_empty')
	if (album_ign_empty == ""):
	    addon.setSetting('album_ignore_empty', 'true')
	    album_ign_empty = "true"

	if (action == "events"):
	    items = list_events(params, album_ign_empty)
	elif (action == "albums"):
	    items = list_albums(params, album_ign_empty)
	elif (action == "faces"):
	    items = list_faces(params, album_ign_empty)
	elif (action == "keywords"):
	    items = list_keywords(params, album_ign_empty)
	elif (action == "ratings"):
	    items = list_ratings(params)
	elif (action == "rescan"):
	    items = import_library(xmlfile)
	elif (action == "hidekeyword"):
	    items = hide_keyword(params)

	if (items):
	    plugin.endOfDirectory(int(sys.argv[1]), True)
