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
import glob

import xbmc
import xbmcgui as gui
import xbmcplugin as plugin
import xbmcaddon

try:
    import xbmcvfs
except ImportError:
    import shutil
    copyfile = shutil.copyfile
else:
    copyfile = xbmcvfs.copy

try:
    from hashlib import md5
except ImportError:
    import md5

addon = xbmcaddon.Addon(id="plugin.image.iphoto")
ALBUM_DATA_XML = "AlbumData.xml"
BASE_URL = "%s" % (sys.argv[0])
PLUGIN_PATH = addon.getAddonInfo("path")
RESOURCE_PATH = os.path.join(PLUGIN_PATH, "resources")
ICONS_PATH = os.path.join(RESOURCE_PATH, "icons")
LIB_PATH = os.path.join(RESOURCE_PATH, "lib")
sys.path.append(LIB_PATH)

from resources.lib.iphoto_parser import *
db_file = xbmc.translatePath(os.path.join(addon.getAddonInfo("Profile"), "iphoto.db"))
db = None

apple_epoch = 978307200

view_mode = 0

# ignore empty albums if configured to do so
album_ign_empty = addon.getSetting('album_ignore_empty')
if (album_ign_empty == ""):
    album_ign_empty = "true"
    addon.setSetting('album_ignore_empty', album_ign_empty)

# force configured sort method when set to "DEFAULT".
# XBMC sorts by file date when user selects "DATE" as the sort method,
# so we have no way to sort by the date stored in the XML or the EXIF
# data without providing an override to "DEFAULT".
# this works out well because I don't believe iPhoto stores the photos
# in the XML in any meaningful order anyway.
media_sort_col = addon.getSetting('default_sort_photo')
if (media_sort_col == ""):
    media_sort_col = "NULL"
    addon.setSetting('default_sort_photo', '0')
elif (media_sort_col == "1"):
    media_sort_col = "mediadate"
else:
    media_sort_col = "NULL"


def md5sum(filename):
    try:
	m = md5()
    except:
	m = md5.new()
    with open(filename, 'rb') as f:
	for chunk in iter(lambda: f.read(128 * m.block_size), ''):
	    m.update(chunk)
    return m.hexdigest()

def render_media(media):
    global view_mode

    # default view in Confluence
    view_mode = addon.getSetting('view_mode')
    if (view_mode == ""):
	view_mode = "0"
	addon.setSetting('view_mode', view_mode)
    view_mode = int(view_mode)

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
	    item = gui.ListItem(caption, thumbnailImage=thumbpath)

	    try:
		item_date = time.strftime("%d.%m.%Y", time.localtime(apple_epoch + float(mediadate)))
		#JSL: setting the date here to enable sorting prevents XBMC
		#JSL: from scanning the EXIF/IPTC info
		#item.setInfo(type="pictures", infoLabels={ "date": item_date })
		#sort_date = True
	    except:
		pass

	    plugin.addDirectoryItem(handle = int(sys.argv[1]), url = mediapath, listitem = item, isFolder = False)
	    n += 1

    plugin.addSortMethod(int(sys.argv[1]), plugin.SORT_METHOD_UNSORTED)
    plugin.addSortMethod(int(sys.argv[1]), plugin.SORT_METHOD_LABEL)
    if (sort_date == True):
	plugin.addSortMethod(int(sys.argv[1]), plugin.SORT_METHOD_DATE)

    return n

def list_photos_in_album(params):
    global db, media_sort_col

    albumid = params['albumid']
    media = db.GetMediaInAlbum(albumid, media_sort_col)
    return render_media(media)

def list_albums(params):
    global db, BASE_URL, album_ign_empty

    albumid = 0
    try:
	albumid = params['albumid']
	return list_photos_in_album(params)
    except Exception, e:
	print to_str(e)
	pass

    albums = db.GetAlbums()
    if (not albums):
	dialog = gui.Dialog()
	dialog.ok(addon.getLocalizedString(30240), addon.getLocalizedString(30241))
	return

    n = 0
    for (albumid, name, count) in albums:
	if (name == "Photos"):
	    continue

	if (not count and album_ign_empty == "true"):
	    continue

	item = gui.ListItem(name, thumbnailImage="DefaultFolder.png")
	plugin.addDirectoryItem(handle = int(sys.argv[1]), url=BASE_URL+"?action=albums&albumid=%s" % (albumid), listitem = item, isFolder = True, totalItems = count)
	n += 1

    plugin.addSortMethod(int(sys.argv[1]), plugin.SORT_METHOD_UNSORTED)
    plugin.addSortMethod(int(sys.argv[1]), plugin.SORT_METHOD_LABEL)
    return n

def list_photos_in_event(params):
    global db, media_sort_col

    rollid = params['rollid']
    media = db.GetMediaInRoll(rollid, media_sort_col)
    return render_media(media)

def list_events(params):
    global db, BASE_URL, album_ign_empty

    rollid = 0
    try:
	rollid = params['rollid']
	return list_photos_in_event(params)
    except Exception, e:
	print to_str(e)
	pass

    rolls = db.GetRolls()
    if (not rolls):
	dialog = gui.Dialog()
	dialog.ok(addon.getLocalizedString(30240), addon.getLocalizedString(30241))
	return

    sort_date = False
    n = 0
    for (rollid, name, thumbpath, rolldate, count) in rolls:
	if (not count and album_ign_empty == "true"):
	    continue

	item = gui.ListItem(name, thumbnailImage=thumbpath)

	try:
	    item_date = time.strftime("%d.%m.%Y", time.localtime(apple_epoch + float(rolldate)))
	    item.setInfo(type="pictures", infoLabels={ "date": item_date })
	    sort_date = True
	except:
	    pass

	plugin.addDirectoryItem(handle = int(sys.argv[1]), url=BASE_URL+"?action=events&rollid=%s" % (rollid), listitem = item, isFolder = True, totalItems = count)
	n += 1

    plugin.addSortMethod(int(sys.argv[1]), plugin.SORT_METHOD_UNSORTED)
    plugin.addSortMethod(int(sys.argv[1]), plugin.SORT_METHOD_LABEL)
    if (sort_date == True):
	plugin.addSortMethod(int(sys.argv[1]), plugin.SORT_METHOD_DATE)
    return n

def list_photos_with_face(params):
    global db, media_sort_col

    faceid = params['faceid']
    media = db.GetMediaWithFace(faceid, media_sort_col)
    return render_media(media)

def list_faces(params):
    global db, BASE_URL, album_ign_empty

    faceid = 0
    try:
	faceid = params['faceid']
	return list_photos_with_face(params)
    except Exception, e:
	print to_str(e)
	pass

    faces = db.GetFaces()
    if (not faces):
	dialog = gui.Dialog()
	dialog.ok(addon.getLocalizedString(30240), addon.getLocalizedString(30241))
	return

    n = 0
    for (faceid, name, thumbpath, count) in faces:
	if (not count and album_ign_empty == "true"):
	    continue

	item = gui.ListItem(name, thumbnailImage=thumbpath)

	plugin.addDirectoryItem(handle = int(sys.argv[1]), url=BASE_URL+"?action=faces&faceid=%s" % (faceid), listitem = item, isFolder = True, totalItems = count)
	n += 1

    plugin.addSortMethod(int(sys.argv[1]), plugin.SORT_METHOD_UNSORTED)
    plugin.addSortMethod(int(sys.argv[1]), plugin.SORT_METHOD_LABEL)
    return n

def list_photos_with_place(params):
    global db, media_sort_col

    placeid = params['placeid']
    media = db.GetMediaWithPlace(placeid, media_sort_col)
    return render_media(media)

def list_places(params):
    global db, BASE_URL, album_ign_empty

    # how to display Places labels:
    # 0 = Addresses
    # 1 = Latitude/Longitude Pairs
    places_labels = addon.getSetting('places_labels')
    if (places_labels == ""):
	places_labels = "0"
	addon.setSetting('places_labels', places_labels)
    places_labels = int(places_labels)

    # show big map of Place as fanart for each item?
    show_fanart = True
    e = addon.getSetting('places_show_fanart')
    if (e == ""):
	addon.setSetting('places_show_fanart', "true")
    elif (e == "false"):
	show_fanart = False

    placeid = 0
    try:
	placeid = params['placeid']
	return list_photos_with_place(params)
    except Exception, e:
	print to_str(e)
	pass

    places = db.GetPlaces()
    if (not places):
	dialog = gui.Dialog()
	dialog.ok(addon.getLocalizedString(30240), addon.getLocalizedString(30241))
	return

    n = 0
    for (placeid, latlon, address, thumbpath, fanartpath, count) in places:
	if (not count and album_ign_empty == "true"):
	    continue

	latlon = latlon.replace("+", " ")

	if (places_labels == 1):
	    item = gui.ListItem(latlon, address)
	else:
	    item = gui.ListItem(address, latlon)

	item.addContextMenuItems([(addon.getLocalizedString(30215), "XBMC.RunPlugin(\""+BASE_URL+"?action=rm_caches\")",)])

	if (thumbpath):
	    item.setThumbnailImage(thumbpath)
	if (show_fanart == True and fanartpath):
	    item.setProperty("Fanart_Image", fanartpath)

	plugin.addDirectoryItem(handle = int(sys.argv[1]), url=BASE_URL+"?action=places&placeid=%s" % (placeid), listitem = item, isFolder = True, totalItems = count)
	n += 1

    if (n > 0):
	plugin.addSortMethod(int(sys.argv[1]), plugin.SORT_METHOD_UNSORTED)
	plugin.addSortMethod(int(sys.argv[1]), plugin.SORT_METHOD_LABEL)
    return n

def list_photos_with_keyword(params):
    global db, media_sort_col

    keywordid = params['keywordid']
    media = db.GetMediaWithKeyword(keywordid, media_sort_col)
    return render_media(media)

def list_keywords(params):
    global db, BASE_URL, album_ign_empty

    keywordid = 0
    try:
	keywordid = params['keywordid']
	return list_photos_with_keyword(params)
    except Exception, e:
	print to_str(e)
	pass

    keywords = db.GetKeywords()
    if (not keywords):
	dialog = gui.Dialog()
	dialog.ok(addon.getLocalizedString(30240), addon.getLocalizedString(30241))
	return

    hidden_keywords = addon.getSetting('hidden_keywords')

    n = 0
    for (keywordid, name, count) in keywords:
	if (name in hidden_keywords):
	    continue

	if (not count and album_ign_empty == "true"):
	    continue

	item = gui.ListItem(name, thumbnailImage="DefaultFolder.png")
	item.addContextMenuItems([(addon.getLocalizedString(30214), "XBMC.RunPlugin(\""+BASE_URL+"?action=hidekeyword&keyword=%s\")" % (name),)])
	plugin.addDirectoryItem(handle = int(sys.argv[1]), url=BASE_URL+"?action=keywords&keywordid=%s" % (keywordid), listitem = item, isFolder = True, totalItems = count)
	n += 1

    if (n > 0):
	plugin.addSortMethod(int(sys.argv[1]), plugin.SORT_METHOD_UNSORTED)
	plugin.addSortMethod(int(sys.argv[1]), plugin.SORT_METHOD_LABEL)
    return n

def list_photos_with_rating(params):
    global db, media_sort_col

    rating = params['rating']
    media = db.GetMediaWithRating(rating, media_sort_col)
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

def import_progress_callback(progress_dialog, altinfo, nphotos, ntotal):
    if (not progress_dialog):
	return 0
    if (progress_dialog.iscanceled()):
	return

    percent = int(float(nphotos * 100) / ntotal)
    progress_dialog.update(percent, addon.getLocalizedString(30211) % (nphotos), altinfo)
    return nphotos

def import_library(xmlpath, xmlfile, masterspath, masters_realpath, enable_places):
    global db

    # always ignore Books and currently selected album
    album_ign = []
    album_ign.append("Book")
    album_ign.append("Selected Event Album")

    # ignore albums published to MobileMe if configured to do so
    album_ign_publ = addon.getSetting('album_ignore_published')
    if (album_ign_publ == ""):
	album_ign_publ = "true"
	addon.setSetting('album_ignore_published', album_ign_publ)
    if (album_ign_publ == "true"):
	album_ign.append("Published")

    # ignore flagged albums if configured to do so
    album_ign_flagged = addon.getSetting('album_ignore_flagged')
    if (album_ign_flagged == ""):
	album_ign_flagged = "true"
	addon.setSetting('album_ignore_flagged', album_ign_flagged)
    if (album_ign_flagged == "true"):
	album_ign.append("Shelf")

    # download maps from Google?
    enable_maps = True
    e = addon.getSetting('places_enable_maps')
    if (e == ""):
	addon.setSetting('places_enable_maps', "true")
    elif (e == "false"):
	enable_maps = False

    db.ResetDB()

    progress_dialog = gui.DialogProgress()
    try:
	progress_dialog.create(addon.getLocalizedString(30210))
	progress_dialog.update(0, addon.getLocalizedString(30212))
    except:
	print traceback.print_exc()
    else:
	map_aspect = 0.0
	if (enable_maps == True):
	    res_x = float(xbmc.getInfoLabel("System.ScreenWidth"))
	    res_y = float(xbmc.getInfoLabel("System.ScreenHeight"))
	    map_aspect = res_x / res_y

	iparser = IPhotoParser(xmlpath, xmlfile, masterspath, masters_realpath, album_ign, enable_places, map_aspect, db.AddAlbumNew, db.AddRollNew, db.AddFaceNew, db.AddKeywordNew, db.AddMediaNew, import_progress_callback, progress_dialog)

	try:
	    iparser.Parse()
	except:
	    print traceback.print_exc()
	    progress_dialog.close()
	    xbmc.executebuiltin("XBMC.RunPlugin(%s?action=resetdb&corrupted=1)" % (BASE_URL))
	else:
	    print "iPhoto Library imported successfully."

	    progress_dialog.close()

	    xbmc.sleep(1000)
	    try:
		# this is non-critical
		db.UpdateLastImport()
	    except:
		pass

def reset_db(params):
    try:
	if (params['noconfirm']):
	    confirm = False
    except:
	confirm = True

    try:
	if (params['corrupted']):
	    corrupted = True
    except:
	corrupted = False

    confirmed = True
    if (confirm):
	dialog = gui.Dialog()
	if (corrupted):
	    confirmed = dialog.yesno(addon.getLocalizedString(30230), addon.getLocalizedString(30231), addon.getLocalizedString(30232), addon.getLocalizedString(30233))
	else:
	    confirmed = dialog.yesno(addon.getLocalizedString(30230), addon.getLocalizedString(30232), addon.getLocalizedString(30233))

    if (confirmed):
	remove_tries = 3
	while (remove_tries and os.path.isfile(db_file)):
	    try:
		os.remove(db_file)
	    except:
		remove_tries -= 1
		xbmc.sleep(1000)
	    else:
		print "iPhoto addon database deleted."

def hide_keyword(params):
    try:
	keyword = params['keyword']
	hidden_keywords = addon.getSetting('hidden_keywords')
	if (hidden_keywords != ""):
	    hidden_keywords += " "
	hidden_keywords += keyword
	addon.setSetting('hidden_keywords', hidden_keywords)
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

def add_generic_context_menu_items(item):
    item.addContextMenuItems([(addon.getLocalizedString(30213), "XBMC.RunPlugin(\""+BASE_URL+"?action=rescan\")",)])
    item.addContextMenuItems([(addon.getLocalizedString(30216), "XBMC.RunPlugin(\""+BASE_URL+"?action=resetdb\")",)])

if (__name__ == "__main__"):
    xmlpath = addon.getSetting('albumdata_xml_path')
    if (xmlpath == ""):
	try:
	    xmlpath = os.getenv("HOME") + "/Pictures/iPhoto Library/"
	    addon.setSetting('albumdata_xml_path', xmlpath)
	except:
	    pass

    # we used to store the file path to the XML instead of the iPhoto Library directory.
    if (os.path.basename(xmlpath) == ALBUM_DATA_XML):
	xmlpath = os.path.dirname(xmlpath)
	addon.setSetting('albumdata_xml_path', xmlpath)

    origxml = os.path.join(xmlpath, ALBUM_DATA_XML)
    xmlfile = xbmc.translatePath(os.path.join(addon.getAddonInfo("Profile"), "iphoto.xml"))

    enable_managed_lib = True
    e = addon.getSetting('managed_lib_enable')
    if (e == ""):
	addon.setSetting('managed_lib_enable', "true")
    elif (e == "false"):
	enable_managed_lib = False

    masterspath = ""
    masters_realpath = ""
    if (enable_managed_lib == False):
	masterspath = addon.getSetting('masters_path')
	masters_realpath = addon.getSetting('masters_real_path')
	if (masterspath == "" or masters_realpath == ""):
	    addon.setSetting('managed_lib_enable', "true")
	    enable_managed_lib = True
	    masterspath = ""
	    masters_realpath = ""

    enable_places = True
    e = addon.getSetting('places_enable')
    if (e == ""):
	addon.setSetting('places_enable', "true")
    elif (e == "false"):
	enable_places = False

    try:
	params = get_params(sys.argv[2])
	action = params['action']
    except:
	# main menu
	try:
	    item = gui.ListItem(addon.getLocalizedString(30100), thumbnailImage=ICONS_PATH+"/events.png")
	    add_generic_context_menu_items(item)
	    plugin.addDirectoryItem(int(sys.argv[1]), BASE_URL+"?action=events", item, True)

	    item = gui.ListItem(addon.getLocalizedString(30101), thumbnailImage=ICONS_PATH+"/albums.png")
	    add_generic_context_menu_items(item)
	    plugin.addDirectoryItem(int(sys.argv[1]), BASE_URL+"?action=albums", item, True)

	    item = gui.ListItem(addon.getLocalizedString(30105), thumbnailImage=ICONS_PATH+"/faces.png")
	    add_generic_context_menu_items(item)
	    plugin.addDirectoryItem(int(sys.argv[1]), BASE_URL+"?action=faces", item, True)

	    item = gui.ListItem(addon.getLocalizedString(30106), thumbnailImage=ICONS_PATH+"/places.png")
	    add_generic_context_menu_items(item)
	    item.addContextMenuItems([(addon.getLocalizedString(30215), "XBMC.RunPlugin(\""+BASE_URL+"?action=rm_caches\")",)])
	    plugin.addDirectoryItem(int(sys.argv[1]), BASE_URL+"?action=places", item, True)

	    item = gui.ListItem(addon.getLocalizedString(30104), thumbnailImage=ICONS_PATH+"/keywords.png")
	    add_generic_context_menu_items(item)
	    plugin.addDirectoryItem(int(sys.argv[1]), BASE_URL+"?action=keywords", item, True)

	    item = gui.ListItem(addon.getLocalizedString(30102), thumbnailImage=ICONS_PATH+"/star.png")
	    add_generic_context_menu_items(item)
	    plugin.addDirectoryItem(int(sys.argv[1]), BASE_URL+"?action=ratings", item, True)

	    hide_import_lib = addon.getSetting('hide_import_lib')
	    if (hide_import_lib == ""):
		hide_import_lib = "false"
		addon.setSetting('hide_import_lib', hide_import_lib)
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
	    auto_update_lib = "false"
	    addon.setSetting('auto_update_lib', auto_update_lib)
	if (auto_update_lib == "true"):
	    tmpfile = xmlfile + ".new"
	    copyfile(origxml, tmpfile)
	    if (os.path.isfile(xmlfile) and md5sum(tmpfile) == md5sum(xmlfile)):
		os.remove(tmpfile)
	    else:
		os.rename(tmpfile, xmlfile)
		try:
		    db = IPhotoDB(db_file)
		except:
		    dialog = gui.Dialog()
		    dialog.ok(addon.getLocalizedString(30240), addon.getLocalizedString(30241))
		    xbmc.executebuiltin('XBMC.RunPlugin(%s?action=resetdb&noconfirm=1)' % BASE_URL)
		else:
		    import_library(xmlpath, xmlfile, masterspath, masters_realpath, enable_places)
    else:
	items = None

	# actions that don't require a database connection
	if (action == "resetdb"):
	    reset_db(params)
	elif (action == "hidekeyword"):
	    items = hide_keyword(params)
	elif (action == "rm_caches"):
	    progress_dialog = gui.DialogProgress()
	    try:
		progress_dialog.create(addon.getLocalizedString(30250))
		progress_dialog.update(0, addon.getLocalizedString(30252))
	    except:
		print traceback.print_exc()
	    else:
		r = glob.glob(os.path.join(os.path.dirname(db_file), "map_*"))
		ntotal = len(r)
		nfiles = 0
		for f in r:
		    if (progress_dialog.iscanceled()):
			break
		    nfiles += 1
		    percent = int(float(nfiles * 100) / ntotal)
		    progress_dialog.update(percent, addon.getLocalizedString(30251) % (nfiles), os.path.basename(f))
		    os.remove(f)
		progress_dialog.close()
		dialog = gui.Dialog()
		dialog.ok(addon.getLocalizedString(30250), addon.getLocalizedString(30251) % (nfiles))
		print "iPhoto: deleted %d cached map image files." % (nfiles)
	else:
	    # actions that do require a database connection
	    try:
		db = IPhotoDB(db_file)
	    except:
		dialog = gui.Dialog()
		dialog.ok(addon.getLocalizedString(30240), addon.getLocalizedString(30241))
		xbmc.executebuiltin('XBMC.RunPlugin(%s?action=resetdb&noconfirm=1)' % BASE_URL)
	    else:
		if (action == "rescan"):
		    copyfile(origxml, xmlfile)
		    import_library(xmlpath, xmlfile, masterspath, masters_realpath, enable_places)
		elif (action == "events"):
		    items = list_events(params)
		elif (action == "albums"):
		    items = list_albums(params)
		elif (action == "faces"):
		    items = list_faces(params)
		elif (action == "places"):
		    if (enable_places == True):
			items = list_places(params)
		    else:
			dialog = gui.Dialog()
			ret = dialog.yesno(addon.getLocalizedString(30220), addon.getLocalizedString(30221), addon.getLocalizedString(30222), addon.getLocalizedString(30223))
			if (ret == True):
			    enable_places = True
			    addon.setSetting('places_enable', "true")
		elif (action == "keywords"):
		    items = list_keywords(params)
		elif (action == "ratings"):
		    items = list_ratings(params)

	if (items):
	    plugin.endOfDirectory(int(sys.argv[1]), True)
	    if (view_mode > 0):
		xbmc.sleep(300)
		if (view_mode == 1):
		    xbmc.executebuiltin("Container.SetViewMode(510)")
		elif (view_mode == 2):
		    xbmc.executebuiltin("Container.SetViewMode(514)")

# vim: tabstop=8 softtabstop=4 shiftwidth=4 noexpandtab:
