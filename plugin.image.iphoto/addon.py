"""
    Plugin for importing iPhoto library
"""

__plugin__ = "iPhoto"
__author__ = "jingai <jingai@floatingpenguins.com>"
__credits__ = "Anoop Menon, Nuka1195, JMarshal, jingai, brsev (http://brsev.com#licensing)"
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
    file_copy = shutil.copyfile
    file_exists = os.path.exists
else:
    file_copy = xbmcvfs.copy
    file_exists = xbmcvfs.exists

try:
    from hashlib import md5
except ImportError:
    import md5

from resources.lib.iphoto_parser import *

addon = xbmcaddon.Addon(id="plugin.image.iphoto")
DB_FILE = xbmc.translatePath(os.path.join(addon.getAddonInfo("Profile"), "iphoto.db"))

IPHOTO_ALBUM_DATA_XML = "AlbumData.xml"
APERTURE_ALBUM_DATA_XML = "ApertureData.xml"
APPLE_EPOCH = 978307200
BASE_URL = "%s" % (sys.argv[0])

PLUGIN_PATH = addon.getAddonInfo("path")
RESOURCE_PATH = os.path.join(PLUGIN_PATH, "resources")
LIB_PATH = os.path.join(RESOURCE_PATH, "lib")
sys.path.append(LIB_PATH)

ICONS_THEME = "token_light"
ICONS_PATH = os.path.join(RESOURCE_PATH, "icons", ICONS_THEME)
ICON_FOLDER = ICONS_PATH+"/folder.png"
ICON_EVENTS = ICONS_PATH+"/events.png"
ICON_ALBUMS = ICONS_PATH+"/albums.png"
ICON_FACES = ICONS_PATH+"/faces.png"
ICON_PLACES = ICONS_PATH+"/places.png"
ICON_KEYWORDS = ICONS_PATH+"/keywords.png"
ICON_STARS = ICONS_PATH+"/star.png"
ICON_UPDATE = ICONS_PATH+"/update.png"
ICON_HELP = ICONS_PATH+"/help.png"
ICON_STAR = ICONS_PATH+"/star%d.png"

# we do special things for these skins
SKIN_DIR = xbmc.getSkinDir()
if (SKIN_DIR == "skin.confluence"):
    SKIN_NAME = "confluence"
elif (SKIN_DIR == "skin.metropolis"):
    SKIN_NAME = "metropolis"
else:
    SKIN_NAME = ""

import_progress_dialog = None


def textview(file):
    WINDOW = 10147
    CONTROL_LABEL = 1
    CONTROL_TEXTBOX = 5

    xbmc.executebuiltin("ActivateWindow(%d)" % (WINDOW))
    retries = 5
    while (gui.getCurrentWindowDialogId() != WINDOW and retries):
	retries -= 1
	xbmc.sleep(100)

    window = gui.Window(WINDOW)

    try:
	heading = os.path.splitext(os.path.basename(file))[0]
	text = open(os.path.join(PLUGIN_PATH, file)).read()
    except:
	print traceback.print_exc()
    else:
	try:
	    window.getControl(CONTROL_LABEL).setLabel("%s - %s" % (heading, __plugin__))
	except:
	    pass
	window.getControl(CONTROL_TEXTBOX).setText(text)

def md5sum(filename):
    try:
	m = md5()
    except:
	m = md5.new()
    with open(filename, 'rb') as f:
	for chunk in iter(lambda: f.read(128 * m.block_size), ''):
	    m.update(chunk)
    return m.hexdigest()

def import_progress_callback(altinfo="", nphotos=0, ntotal=100):
    global import_progress_dialog

    if (not import_progress_dialog):
	# try to get progress dialog actually on-screen before we do work
	retries = 10
	import_progress_dialog = None
	while (gui.getCurrentWindowDialogId() != 10101 and retries):
	    if (not import_progress_dialog):
		import_progress_dialog = gui.DialogProgress()
		import_progress_dialog.create(addon.getLocalizedString(30210))
	    retries -= 1
	    xbmc.sleep(100)
    if (not import_progress_dialog):
	return 0
    if (import_progress_dialog.iscanceled()):
	return

    percent = int(float(nphotos * 100) / ntotal)
    import_progress_dialog.update(percent, addon.getLocalizedString(30211) % (nphotos), altinfo)
    return nphotos

class IPhotoGUI:
    def __init__(self):
	self.params = {}
	paramstring = str(sys.argv[2]).strip()
	paramstring = paramstring.lstrip("?")
	if (paramstring):
	    paramlist = paramstring.split("&")
	    for param in paramlist:
		(k,v) = param.split("=")
		self.params[k] = v
	    print self.params

	# automatically update library if desired
	self.auto_update_lib = addon.getSetting('auto_update_lib')
	if (self.auto_update_lib == ""):
	    self.auto_update_lib = "false"
	    addon.setSetting('auto_update_lib', self.auto_update_lib)

	# library items are referenced or managed?
	self.enable_managed_lib = True
	e = addon.getSetting('managed_lib_enable')
	if (e == ""):
	    addon.setSetting('managed_lib_enable', "true")
	elif (e == "false"):
	    self.enable_managed_lib = False

	self.xmlpath = addon.getSetting('albumdata_xml_path')
	if (self.xmlpath == ""):
	    try:
		self.xmlpath = os.getenv("HOME") + "/Pictures/iPhoto Library/"
		addon.setSetting('albumdata_xml_path', self.xmlpath)
	    except:
		pass
	    addon.openSettings(BASE_URL)

	# used to store the file path to the XML instead of the iPhoto Library directory.
	if (os.path.basename(self.xmlpath) == IPHOTO_ALBUM_DATA_XML):
	    self.xmlpath = os.path.dirname(self.xmlpath)
	    addon.setSetting('albumdata_xml_path', self.xmlpath)

	# is this an iPhoto or Aperture library?
	self.origxml = os.path.join(self.xmlpath, IPHOTO_ALBUM_DATA_XML)
	if (not file_exists(self.origxml)):
	    self.xmlsrc = "Aperture"
	    self.origxml = os.path.join(self.xmlpath, APERTURE_ALBUM_DATA_XML)
	else:
	    self.xmlsrc = "iPhoto"
	# our local copy of the XML
	self.xmlfile = xbmc.translatePath(os.path.join(addon.getAddonInfo("Profile"), "iphoto.xml"))

	# for referenced libraries, iPhoto finds images using the mount point as seen by the host OS.
	# since the plugin can run on remote clients as well, it's possible that path is not the same.
	self.masterspath = ""
	self.masters_realpath = ""
	if (self.enable_managed_lib == False):
	    self.masterspath = addon.getSetting('masters_path')
	    self.masters_realpath = addon.getSetting('masters_real_path')
	    if (self.masterspath == "" or self.masters_realpath == ""):
		addon.setSetting('managed_lib_enable', "true")
		self.enable_managed_lib = True
		self.masterspath = ""
		self.masters_realpath = ""

	# ignore empty albums if configured to do so
	self.album_ign_empty = addon.getSetting('album_ignore_empty')
	if (self.album_ign_empty == ""):
	    self.album_ign_empty = "true"
	    addon.setSetting('album_ignore_empty', self.album_ign_empty)

	# ignore albums published to MobileMe/iCloud if configured to do so
	self.album_ign_publ = addon.getSetting('album_ignore_published')
	if (self.album_ign_publ == ""):
	    self.album_ign_publ = "true"
	    addon.setSetting('album_ignore_published', self.album_ign_publ)

	# ignore flagged albums if configured to do so
	self.album_ign_flagged = addon.getSetting('album_ignore_flagged')
	if (self.album_ign_flagged == ""):
	    self.album_ign_flagged = "true"
	    addon.setSetting('album_ignore_flagged', self.album_ign_flagged)

	# enable support for Places?
	self.enable_places = True
	e = addon.getSetting('places_enable')
	if (e == ""):
	    addon.setSetting('places_enable', "true")
	elif (e == "false"):
	    self.enable_places = False

	# how to display Places labels:
	# 0 = Addresses
	# 1 = Latitude/Longitude Pairs
	self.places_labels = addon.getSetting('places_labels')
	if (self.places_labels == ""):
	    self.places_labels = "0"
	    addon.setSetting('places_labels', self.places_labels)
	self.places_labels = int(self.places_labels)

	# show big map of Place as fanart for each item?
	self.places_fanart = True
	e = addon.getSetting('places_show_fanart')
	if (e == ""):
	    addon.setSetting('places_show_fanart', "true")
	elif (e == "false"):
	    self.places_fanart = False

	# download maps from Google?
	self.enable_maps = True
	e = addon.getSetting('places_enable_maps')
	if (e == ""):
	    addon.setSetting('places_enable_maps', "true")
	elif (e == "false"):
	    self.enable_maps = False

	self.context_menu_items = []
	self.view_mode = 0
	self.sort_method = 0
	self.sort_dir = ""
	self.db = None
	self.dbSrc = None
	self.dbVer = 0.0

    def open_db(self):
	if (self.db is None):
	    self.db = IPhotoDB(DB_FILE)
	self.dbSrc = self.db.GetLibrarySource()
	self.dbVer = self.db.GetLibraryVersion()

    def close_db(self):
	try:
	    self.db.CloseDB()
	except:
	    pass

    def reset_db(self):
	try:
	    if (self.params['noconfirm']):
		confirm = False
	except:
	    confirm = True

	try:
	    if (self.params['corrupted']):
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
	    if (xbmc.getInfoLabel("Window(10000).Property(iphoto_scanning)") == "True"):
		# refuse to delete database when import is in progress
		return addon.getLocalizedString(30300)

	    remove_tries = 10
	    while (remove_tries and os.path.isfile(DB_FILE)):
		try:
		    os.remove(DB_FILE)
		except:
		    remove_tries -= 1
		    xbmc.sleep(100)
		else:
		    return addon.getLocalizedString(30320)

	    return addon.getLocalizedString(30321)

    def import_library(self):
	global import_progress_dialog

	# crude locking to prevent multiple simultaneous library imports
	if (xbmc.getInfoLabel("Window(10000).Property(iphoto_scanning)") == "True"):
	    return addon.getLocalizedString(30300)
	else:
	    gui.Window(10000).setProperty("iphoto_scanning", "True")

	# Albums to completely ignore
	album_ign = []
	# iPhoto albums
	album_ign.append("Book")
	album_ign.append("Selected Event Album")
	album_ign.append("Event")
	if (self.xmlsrc == "Aperture"):
	    # Aperture albums (by AlbumType)
	    album_ign.append("5")
	    album_ign.append("97")
	    album_ign.append("98")
	    album_ign.append("99")
	    # Aperture albums (by uuid)
	    album_ign.append("fiveStarAlbum")
	    album_ign.append("oneStarAlbum")
	# Published albums
	if (self.album_ign_publ == "true"):
	    album_ign.append("Published")
	# Flagged albums
	if (self.album_ign_flagged == "true"):
	    album_ign.append("Shelf")
	    if (self.xmlsrc == "Aperture"):
		album_ign.append("95")

	if (self.enable_maps == True):
	    res_x = float(xbmc.getInfoLabel("System.ScreenWidth"))
	    res_y = float(xbmc.getInfoLabel("System.ScreenHeight"))
	    map_aspect = res_x / res_y
	else:
	    map_aspect = 0.0

	iparser = IPhotoParser(self.xmlsrc, self.xmlpath, self.xmlfile, self.masterspath, self.masters_realpath, album_ign, self.enable_places, map_aspect, self.db.SetConfig, self.db.AddAlbumNew, self.db.AddRollNew, self.db.AddFaceNew, self.db.AddKeywordNew, self.db.AddMediaNew, import_progress_callback)

	try:
	    import_progress_callback(addon.getLocalizedString(30219))
	    self.db.ResetDB()
	    self.db.InitDB()

	    import_progress_callback(addon.getLocalizedString(30212))
	    iparser.Parse()
	except Exception, e:
	    if (import_progress_dialog):
		import_progress_dialog.close()
	    gui.Window(10000).setProperty("iphoto_scanning", "False")
	    raise e
	else:
	    if (import_progress_dialog):
		import_progress_dialog.close()
	    gui.Window(10000).setProperty("iphoto_scanning", "False")
	    return addon.getLocalizedString(30301)

    def generic_context_menu_items(self):
	self.context_menu_items.append((addon.getLocalizedString(30217), "XBMC.RunPlugin(\""+BASE_URL+"?action=textview&file=README.txt\")",))
	self.context_menu_items.append((xbmc.getLocalizedString(1045), "XBMC.RunPlugin(\""+BASE_URL+"?action=settings\")",))

    def maintenance_context_menu_items(self):
	self.context_menu_items.append((addon.getLocalizedString(30213), "XBMC.RunPlugin(\""+BASE_URL+"?action=rescan\")",))
	self.context_menu_items.append((addon.getLocalizedString(30216), "XBMC.RunPlugin(\""+BASE_URL+"?action=resetdb\")",))
	self.context_menu_items.append((addon.getLocalizedString(30215), "XBMC.RunPlugin(\""+BASE_URL+"?action=rm_caches\")",))

    def render_media(self, media):
	# default view for select skins
	if (SKIN_NAME != ""):
	    vm = addon.getSetting(SKIN_NAME + '_view_default')
	    if (vm == ""):
		addon.setSetting(SKIN_NAME + '_view_default', "0")
	    else:
		vm = int(vm)
		if (SKIN_NAME == "confluence"):
		    if (vm == 1):
			self.view_mode = 514	    # Pic Thumbs
		    elif (vm == 2):
			self.view_mode = 510	    # Image Wrap
		elif (SKIN_NAME == "metropolis"):
		    if (vm == 1):
			self.view_mode = 500	    # Picture Grid
		    elif (vm == 2):
			self.view_mode = 59	    # Galary Fanart

	sort_date_avail = False
	n = 0
	ntotal = len(media)
	for (caption, mediapath, thumbpath, originalpath, rating, mediadate, mediasize) in media:
	    if ((self.dbSrc == "Aperture" and originalpath) or (not mediapath)):
		mediapath = originalpath
	    if (not thumbpath):
		thumbpath = mediapath
	    if (not caption):
		caption = mediapath

	    if (caption):
		item = gui.ListItem(caption, iconImage=thumbpath, thumbnailImage=mediapath)

		try:
		    item.setProperty('Fanart_Image', mediapath)
		    item_date = time.strftime("%d.%m.%Y", time.localtime(APPLE_EPOCH + float(mediadate)))
		    item.setInfo(type="pictures", infoLabels={ "date": item_date })
		    sort_date_avail = True
		except:
		    pass

		plugin.addDirectoryItem(handle=int(sys.argv[1]), url=mediapath, listitem=item, isFolder=False, totalItems=ntotal)
		n += 1

	plugin.addSortMethod(int(sys.argv[1]), plugin.SORT_METHOD_UNSORTED)
	plugin.addSortMethod(int(sys.argv[1]), plugin.SORT_METHOD_LABEL)
	if (sort_date_avail == True):
	    plugin.addSortMethod(int(sys.argv[1]), plugin.SORT_METHOD_DATE)
	plugin.addSortMethod(int(sys.argv[1]), plugin.SORT_METHOD_SIZE)

	# force configured sort method
	sm = addon.getSetting('default_sort_method')
	if (sm == ""):
	    addon.setSetting('default_sort_method', '0')
	else:
	    sm = int(sm)
	    if (sm == 1 and sort_date_avail):
		self.sort_method = plugin.SORT_METHOD_DATE
	    elif (sm == 2):
		self.sort_method = plugin.SORT_METHOD_LABEL
	    elif (sm == 3):
		self.sort_method = plugin.SORT_METHOD_SIZE

	# force configured sort direction
	sd = addon.getSetting('default_sort_dir')
	if (sd == ""):
	    addon.setSetting('default_sort_dir', '0')
	else:
	    if (sd == "1"):
		self.sort_dir = "Ascending"
	    elif (sd == "2"):
		self.sort_dir = "Descending"

	print "iphoto.gui: Displaying %d of %d media items" % (n, ntotal)
	return n

    def list_photos_in_album(self, albumid):
	media = self.db.GetMediaInAlbum(albumid)
	return self.render_media(media)

    def list_albums(self):
	try:
	    albumid = self.params['albumid']
	    return self.list_photos_in_album(albumid)
	except:
	    pass

	albums = self.db.GetAlbums()
	if (not albums):
	    print "iphoto.gui: No albums to display"
	    return 0

	self.generic_context_menu_items()

	n = 0
	ntotal = len(albums)
	for (albumid, name, count) in albums:
	    if (name == "Photos"):
		continue

	    if (not count and self.album_ign_empty == "true"):
		continue

	    item = gui.ListItem(name, iconImage=ICON_FOLDER, thumbnailImage=ICON_FOLDER)
	    item.addContextMenuItems(self.context_menu_items, True)
	    plugin.addDirectoryItem(handle=int(sys.argv[1]), url=BASE_URL+"?action=albums&albumid=%s" % (albumid), listitem=item, isFolder=True, totalItems=ntotal)
	    n += 1

	plugin.addSortMethod(int(sys.argv[1]), plugin.SORT_METHOD_UNSORTED)
	plugin.addSortMethod(int(sys.argv[1]), plugin.SORT_METHOD_LABEL)

	# default view for select skins
	if (SKIN_NAME != ""):
	    if (addon.getSetting(SKIN_NAME + '_view_albums') == ""):
		if (SKIN_NAME == "confluence"):
		    self.view_mode = 51			# Big List
		elif (SKIN_NAME == "metropolis"):
		    self.view_mode = 0
		addon.setSetting(SKIN_NAME + '_view_albums', str(self.view_mode))

	print "iphoto.gui: Displaying %d of %d albums" % (n, ntotal)
	return n

    def list_photos_in_event(self, rollid):
	if (self.dbSrc == "Aperture"):
	    # Aperture Projects are lists of Albums
	    media = self.db.GetMediaInAlbum(rollid)
	else:
	    media = self.db.GetMediaInRoll(rollid)
	return self.render_media(media)

    def list_events(self):
	try:
	    rollid = self.params['rollid']
	    return self.list_photos_in_event(rollid)
	except:
	    pass

	rolls = self.db.GetRolls()
	if (not rolls):
	    print "iphoto.gui: No events to display"
	    return 0

	self.generic_context_menu_items()

	sort_date_avail = False
	n = 0
	ntotal = len(rolls)
	for (rollid, name, thumbpath, rolldate, count) in rolls:
	    if (not count and self.album_ign_empty == "true"):
		continue

	    if (thumbpath != None):
		item = gui.ListItem(name, iconImage=thumbpath, thumbnailImage=thumbpath)
	    else:
		item = gui.ListItem(name)
	    item.addContextMenuItems(self.context_menu_items, True)

	    try:
		item_date = time.strftime("%d.%m.%Y", time.localtime(APPLE_EPOCH + float(rolldate)))
		item.setInfo(type="pictures", infoLabels={ "date": item_date })
		sort_date_avail = True
	    except:
		pass

	    plugin.addDirectoryItem(handle=int(sys.argv[1]), url=BASE_URL+"?action=events&rollid=%s" % (rollid), listitem=item, isFolder=True, totalItems=ntotal)
	    n += 1

	plugin.addSortMethod(int(sys.argv[1]), plugin.SORT_METHOD_UNSORTED)
	plugin.addSortMethod(int(sys.argv[1]), plugin.SORT_METHOD_LABEL)
	if (sort_date_avail == True):
	    plugin.addSortMethod(int(sys.argv[1]), plugin.SORT_METHOD_DATE)

	# default view for select skins
	if (SKIN_NAME != ""):
	    if (addon.getSetting(SKIN_NAME + '_view_events') == ""):
		if (SKIN_NAME == "confluence"):
		    self.view_mode = 0
		elif (SKIN_NAME == "metropolis"):
		    self.view_mode = 0
		addon.setSetting(SKIN_NAME + '_view_events', str(self.view_mode))

	print "iphoto.gui: Displaying %d of %d events" % (n, ntotal)
	return n

    def list_photos_with_face(self, faceid):
	media = self.db.GetMediaWithFace(faceid)
	return self.render_media(media)

    def list_faces(self):
	try:
	    faceid = self.params['faceid']
	    return self.list_photos_with_face(faceid)
	except:
	    pass

	faces = self.db.GetFaces()
	if (not faces):
	    print "iphoto.gui: No faces to display"
	    return 0

	self.generic_context_menu_items()

	n = 0
	ntotal = len(faces)
	for (faceid, name, thumbpath, count) in faces:
	    if (not count and self.album_ign_empty == "true"):
		continue

	    item = gui.ListItem(name, iconImage=thumbpath, thumbnailImage=thumbpath)
	    item.addContextMenuItems(self.context_menu_items, True)
	    plugin.addDirectoryItem(handle=int(sys.argv[1]), url=BASE_URL+"?action=faces&faceid=%s" % (faceid), listitem=item, isFolder=True, totalItems=ntotal)
	    n += 1

	plugin.addSortMethod(int(sys.argv[1]), plugin.SORT_METHOD_UNSORTED)
	plugin.addSortMethod(int(sys.argv[1]), plugin.SORT_METHOD_LABEL)

	# default view for select skins
	if (SKIN_NAME != ""):
	    if (addon.getSetting(SKIN_NAME + '_view_faces') == ""):
		if (SKIN_NAME == "confluence"):
		    self.view_mode = 500		# Thumbnails
		elif (SKIN_NAME == "metropolis"):
		    self.view_mode = 59			# Gallary Fanart
		addon.setSetting(SKIN_NAME + '_view_faces', str(self.view_mode))

	print "iphoto.gui: Displaying %d of %d faces" % (n, ntotal)
	return n

    def list_photos_with_place(self, placeid):
	media = self.db.GetMediaWithPlace(placeid)
	return self.render_media(media)

    def list_places(self):
	try:
	    placeid = self.params['placeid']
	    return self.list_photos_with_place(placeid)
	except:
	    pass

	places = self.db.GetPlaces()
	if (not places):
	    print "iphoto.gui: No places to display"
	    return 0

	self.generic_context_menu_items()

	n = 0
	ntotal = len(places)
	for (placeid, latlon, address, thumbpath, fanartpath, count) in places:
	    if (not count and self.album_ign_empty == "true"):
		continue

	    latlon = latlon.replace("+", " ")

	    if (self.places_labels == 1):
		item = gui.ListItem(latlon, address)
	    else:
		item = gui.ListItem(address, latlon)
	    item.addContextMenuItems(self.context_menu_items, True)

	    if (thumbpath):
		item.setIconImage(thumbpath)
		item.setThumbnailImage(thumbpath)
	    if (self.places_fanart == True and fanartpath):
		item.setProperty("Fanart_Image", fanartpath)

	    plugin.addDirectoryItem(handle=int(sys.argv[1]), url=BASE_URL+"?action=places&placeid=%s" % (placeid), listitem=item, isFolder=True, totalItems=ntotal)
	    n += 1

	if (n > 0):
	    plugin.addSortMethod(int(sys.argv[1]), plugin.SORT_METHOD_UNSORTED)
	    plugin.addSortMethod(int(sys.argv[1]), plugin.SORT_METHOD_LABEL)

	# default view for select skins
	if (SKIN_NAME != ""):
	    if (addon.getSetting(SKIN_NAME + '_view_places') == ""):
		if (SKIN_NAME == "confluence"):
		    self.view_mode = 500		# Thumbnails
		elif (SKIN_NAME == "metropolis"):
		    self.view_mode = 59			# Gallary Fanart
		addon.setSetting(SKIN_NAME + '_view_places', str(self.view_mode))

	print "iphoto.gui: Displaying %d of %d places" % (n, ntotal)
	return n

    def list_photos_with_keyword(self, keywordid):
	media = self.db.GetMediaWithKeyword(keywordid)
	return self.render_media(media)

    def list_keywords(self):
	if (self.dbSrc == "Aperture" or self.dbVer >= 9.4):
	    dialog = gui.Dialog()
	    dialog.ok(addon.getLocalizedString(30262), addon.getLocalizedString(30263) % ("in this version of", self.dbSrc))
	    return 0

	try:
	    keywordid = self.params['keywordid']
	    return self.list_photos_with_keyword(keywordid)
	except:
	    pass

	keywords = self.db.GetKeywords()
	if (not keywords):
	    print "iphoto.gui: No keywords to display"
	    return 0

	hidden_keywords = addon.getSetting('hidden_keywords')

	self.generic_context_menu_items()

	n = 0
	ntotal = len(keywords)
	for (keywordid, name, count) in keywords:
	    if (name in hidden_keywords):
		continue

	    if (not count and self.album_ign_empty == "true"):
		continue

	    item = gui.ListItem(name, iconImage=ICON_FOLDER, thumbnailImage=ICON_FOLDER)
	    self.context_menu_items.append((addon.getLocalizedString(30214), "XBMC.RunPlugin(\""+BASE_URL+"?action=hidekeyword&keyword=%s\")" % (name),))
	    item.addContextMenuItems(self.context_menu_items, True)
	    plugin.addDirectoryItem(handle=int(sys.argv[1]), url=BASE_URL+"?action=keywords&keywordid=%s" % (keywordid), listitem=item, isFolder=True, totalItems=ntotal)
	    n += 1

	if (n > 0):
	    plugin.addSortMethod(int(sys.argv[1]), plugin.SORT_METHOD_UNSORTED)
	    plugin.addSortMethod(int(sys.argv[1]), plugin.SORT_METHOD_LABEL)

	# default view for select skins
	if (SKIN_NAME != ""):
	    if (addon.getSetting(SKIN_NAME + '_view_keywords') == ""):
		if (SKIN_NAME == "confluence"):
		    self.view_mode = 51			# Big List
		elif (SKIN_NAME == "metropolis"):
		    self.view_mode = 0
		addon.setSetting(SKIN_NAME + '_view_keywords', str(self.view_mode))

	print "iphoto.gui: Displaying %d of %d keywords" % (n, ntotal)
	return n

    def list_photos_with_rating(self, rating):
	media = self.db.GetMediaWithRating(rating)
	return self.render_media(media)

    def list_ratings(self):
	if (self.dbSrc == "Aperture"):
	    dialog = gui.Dialog()
	    dialog.ok(addon.getLocalizedString(30262), addon.getLocalizedString(30263) % ("in", self.dbSrc))
	    return 0

	try:
	    rating = self.params['rating']
	    return self.list_photos_with_rating(rating)
	except:
	    pass

	self.generic_context_menu_items()

	n = 0
	for a in range(1,6):
	    rating = addon.getLocalizedString(30200) % (a)
	    item = gui.ListItem(rating, iconImage=ICON_STAR % (a), thumbnailImage=ICON_STAR % (a))
	    item.addContextMenuItems(self.context_menu_items, True)
	    plugin.addDirectoryItem(handle=int(sys.argv[1]), url=BASE_URL+"?action=ratings&rating=%d" % (a), listitem=item, isFolder=True, totalItems=5)
	    n += 1

	plugin.addSortMethod(int(sys.argv[1]), plugin.SORT_METHOD_UNSORTED)
	plugin.addSortMethod(int(sys.argv[1]), plugin.SORT_METHOD_LABEL)

	# default view for select skins
	if (SKIN_NAME != ""):
	    if (addon.getSetting(SKIN_NAME + '_view_ratings') == ""):
		if (SKIN_NAME == "confluence"):
		    self.view_mode = 51			# Big List
		elif (SKIN_NAME == "metropolis"):
		    self.view_mode = 0
		addon.setSetting(SKIN_NAME + '_view_ratings', str(self.view_mode))

	return n

    def main_menu(self):
	n = 0
	self.generic_context_menu_items()
	self.maintenance_context_menu_items()

	if (self.dbSrc):
	    if (self.dbSrc == "Aperture"):
		item = gui.ListItem(addon.getLocalizedString(30108), iconImage=ICON_EVENTS, thumbnailImage=ICON_EVENTS)
	    else:
		item = gui.ListItem(addon.getLocalizedString(30100), iconImage=ICON_EVENTS, thumbnailImage=ICON_EVENTS)
	    item.addContextMenuItems(self.context_menu_items, True)
	    plugin.addDirectoryItem(int(sys.argv[1]), BASE_URL+"?action=events", item, True)
	    n += 1

	    item = gui.ListItem(addon.getLocalizedString(30101), iconImage=ICON_ALBUMS, thumbnailImage=ICON_ALBUMS)
	    item.addContextMenuItems(self.context_menu_items, True)
	    plugin.addDirectoryItem(int(sys.argv[1]), BASE_URL+"?action=albums", item, True)
	    n += 1

	    item = gui.ListItem(addon.getLocalizedString(30105), iconImage=ICON_FACES, thumbnailImage=ICON_FACES)
	    item.addContextMenuItems(self.context_menu_items, True)
	    plugin.addDirectoryItem(int(sys.argv[1]), BASE_URL+"?action=faces", item, True)
	    n += 1

	    item = gui.ListItem(addon.getLocalizedString(30106), iconImage=ICON_PLACES, thumbnailImage=ICON_PLACES)
	    item.addContextMenuItems(self.context_menu_items, True)
	    plugin.addDirectoryItem(int(sys.argv[1]), BASE_URL+"?action=places", item, True)
	    n += 1

	    # Keywords not yet supported in Aperture or iPhoto >= 9.4
	    if (self.dbSrc == "iPhoto" and self.dbVer < 9.4):
		item = gui.ListItem(addon.getLocalizedString(30104), iconImage=ICON_KEYWORDS, thumbnailImage=ICON_KEYWORDS)
		item.addContextMenuItems(self.context_menu_items, True)
		plugin.addDirectoryItem(int(sys.argv[1]), BASE_URL+"?action=keywords", item, True)
		n += 1

	    # Ratings not yet supported in Aperture
	    if (self.dbSrc != "Aperture"):
		item = gui.ListItem(addon.getLocalizedString(30102), iconImage=ICON_STARS, thumbnailImage=ICON_STARS)
		item.addContextMenuItems(self.context_menu_items, True)
		plugin.addDirectoryItem(int(sys.argv[1]), BASE_URL+"?action=ratings", item, True)
		n += 1

	hide_item = addon.getSetting('hide_import_lib')
	if (hide_item == ""):
	    hide_item = "false"
	    addon.setSetting('hide_import_lib', hide_item)
	if (hide_item == "false"):
	    item = gui.ListItem(addon.getLocalizedString(30103), iconImage=ICON_UPDATE, thumbnailImage=ICON_UPDATE)
	    item.addContextMenuItems(self.context_menu_items, True)
	    plugin.addDirectoryItem(int(sys.argv[1]), BASE_URL+"?action=rescan", item, False)
	    n += 1

	hide_item = addon.getSetting('hide_view_readme')
	if (hide_item == ""):
	    hide_item = "false"
	    addon.setSetting('hide_view_readme', hide_item)
	if (hide_item == "false" or n == 0):
	    item = gui.ListItem(addon.getLocalizedString(30107), iconImage=ICON_HELP, thumbnailImage=ICON_HELP)
	    item.addContextMenuItems(self.context_menu_items, True)
	    plugin.addDirectoryItem(int(sys.argv[1]), BASE_URL+"?action=textview&file=README.txt", item, False)
	    n += 1

	plugin.addSortMethod(int(sys.argv[1]), plugin.SORT_METHOD_NONE)
	return n

if (__name__ == "__main__"):
    iphoto = IPhotoGUI()

    items = None
    refresh = False
    action_result = None
    update_lib = False
    try:
	action = iphoto.params['action']
    except:
	iphoto.open_db()
	items = iphoto.main_menu()

	if (iphoto.auto_update_lib == "true"):
	    try:
		tmpfile = iphoto.xmlfile + ".new"
		file_copy(iphoto.origxml, tmpfile)
		if (file_exists(iphoto.xmlfile) and md5sum(tmpfile) == md5sum(iphoto.xmlfile)):
		    os.remove(tmpfile)
		else:
		    os.rename(tmpfile, iphoto.xmlfile)
		    update_lib = True
	    except:
		pass
    else:
	# actions that don't require a database connection
	if (action == "resetdb"):
	    action_result = iphoto.reset_db()
	    refresh = True
	elif (action == "rm_caches"):
	    progress_dialog = gui.DialogProgress()
	    try:
		progress_dialog.create(addon.getLocalizedString(30250))
		progress_dialog.update(0, addon.getLocalizedString(30252))
	    except:
		print traceback.print_exc()
	    else:
		r = glob.glob(os.path.join(os.path.dirname(DB_FILE), "map_*"))
		ntotal = len(r)
		nfiles = 0
		for f in r:
		    if (progress_dialog.iscanceled()):
			break
		    nfiles += 1
		    percent = int(float(nfiles * 100) / ntotal)
		    progress_dialog.update(percent, addon.getLocalizedString(30322) % (nfiles), os.path.basename(f))
		    os.remove(f)
		progress_dialog.close()
		dialog = gui.Dialog()
		action_result = addon.getLocalizedString(30322) % (nfiles)
	elif (action == "textview"):
	    try:
		file = iphoto.params['file']
	    except Exception, e:
		print smart_utf8(e)
		pass
	    else:
		textview(file)
	elif (action == "settings"):
	    addon.openSettings(BASE_URL)
	elif (action == "hidekeyword"):
	    try:
		keyword = params['keyword']
		hidden_keywords = addon.getSetting('hidden_keywords')
		if (hidden_keywords != ""):
		    hidden_keywords += " "
		hidden_keywords += keyword
		addon.setSetting('hidden_keywords', hidden_keywords)
		action_result = addon.getLocalizedString(30330) % (keyword)
		refresh = True
	    except Exception, e:
		print smart_utf8(e)
		pass
	else:
	    # actions that do require a database connection
	    iphoto.open_db()
	    if (action == "rescan"):
		file_copy(iphoto.origxml, iphoto.xmlfile)
		update_lib = True
	    elif (action == "events"):
		items = iphoto.list_events()
	    elif (action == "albums"):
		items = iphoto.list_albums()
	    elif (action == "faces"):
		items = iphoto.list_faces()
	    elif (action == "places"):
		if (iphoto.enable_places == True):
		    items = iphoto.list_places()
		else:
		    dialog = gui.Dialog()
		    ret = dialog.yesno(addon.getLocalizedString(30220), addon.getLocalizedString(30221), addon.getLocalizedString(30222), addon.getLocalizedString(30223))
		    if (ret == True):
			iphoto.enable_places = True
			addon.setSetting('places_enable', "true")
	    elif (action == "keywords"):
		items = iphoto.list_keywords()
	    elif (action == "ratings"):
		items = iphoto.list_ratings()

    if (items > 0):
	plugin.endOfDirectory(int(sys.argv[1]), True)
	if (iphoto.view_mode or iphoto.sort_method):
	    xbmc.sleep(300)
	if (iphoto.view_mode):
	    print "iphoto.gui: Trying to set view mode in %s to %d" % (SKIN_NAME, iphoto.view_mode)
	    xbmc.executebuiltin("Container.SetViewMode(%d)" % (iphoto.view_mode))
	if (iphoto.sort_method):
	    print "iphoto.gui: Trying to set sort method to %d" % (iphoto.sort_method)
	    xbmc.executebuiltin("Container.SetSortMethod(%d)" % (iphoto.sort_method))
	if (iphoto.sort_dir != ""):
	    print "iphoto.gui: Trying to set sort direction to %s" % (iphoto.sort_dir)
	    xbmc.executebuiltin("Container.SortDirection(%s)" % (iphoto.sort_dir))
    elif (items == 0):
	action_result = addon.getLocalizedString(30310)

    if (update_lib):
	try:
	    action_result = iphoto.import_library()
	except:
	    print traceback.print_exc()
	    action_result = addon.getLocalizedString(30302)
	    xbmc.executebuiltin('XBMC.RunPlugin(%s?action=resetdb&noconfirm=1)' % BASE_URL)
	else:
	    refresh = True

    iphoto.close_db()

    if (refresh):
	xbmc.executebuiltin("Container.Refresh")

    if (action_result):
	print "iphoto.gui: " + smart_utf8(action_result)
	xbmc.executebuiltin('XBMC.Notification(%s,%s,3000)' % (smart_utf8(__plugin__), smart_utf8(action_result)))

# vim: tabstop=8 softtabstop=4 shiftwidth=4 noexpandtab:
