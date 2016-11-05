"""
    Plugin for importing Photo App library
"""

__plugin__ = "Photo App"
__author__ = "Claude Marksteiner <PhotoApp.KodiPlugin@stonebug.com>"
__credits__ = ""
__url__ = ""

import sys
import time
import os
import glob
import urllib
import urlparse

import xbmc
import xbmcgui as gui
import xbmcplugin as plugin
import xbmcaddon

import xbmcvfs
file_copy = xbmcvfs.copy
file_exists = xbmcvfs.exists

from resources.lib.photo_app_db import *

addon = xbmcaddon.Addon()

plugin_path = addon.getAddonInfo("path")
resource_path = os.path.join(plugin_path, "resources")
lib_path = os.path.join(resource_path, "lib")
sys.path.append(lib_path)

base_url = sys.argv[0]
addon_handle = int(sys.argv[1])
args = urlparse.parse_qs(sys.argv[2][1:])

ICONS_PATH = os.path.join(resource_path, "icons")
ICON_FOLDER = ICONS_PATH+"/folder.png"
ICON_MOMENTS = ICONS_PATH+"/moments.png"
ICON_ALBUMS = ICONS_PATH+"/albums.png"
ICON_SLIDESHOWS = ICONS_PATH+"/slideshows.png"

def build_url(query):
    return base_url + '?' + urllib.urlencode(query)

class PhotoAppGUI:
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

        self.photo_app_path = addon.getSetting('photo_library_path')
        if (self.photo_app_path == ""):
            self.photo_app_path = os.getenv("HOME") + '/Pictures/Fotos Library.photoslibrary/'
        elif (self.photo_app_path[-1:] <> '/'):
            self.photo_app_path = self.photo_app_path + '/'
        addon.setSetting('photo_library_path', self.photo_app_path)

        self.photo_app_db_file = self.photo_app_path + 'Database/Library.apdb'
        self.photo_app_picture_path = self.photo_app_path + '/Masters'

        self.use_local_copy = addon.getSetting('use_local_copy')
        if (self.use_local_copy == ""):
            self.use_local_copy = "false"
            addon.setSetting('use_local_copy', self.use_local_copy)

	if (self.use_local_copy == "true"):
	    database_copy = xbmc.translatePath(os.path.join(addon.getAddonInfo("Profile"), "Library.apdb"))
            #if ((not file_exists(database_copy)) or
            #    (os.stat(self.photo_app_db_file).st_mtime > os.stat(database_copy).st_mtime)):
	    print "photoapp.gui: Copy Photo Library Database..."
	    print "photoapp.gui: from %s to %s" % (self.photo_app_db_file, database_copy)
	    file_copy(self.photo_app_db_file, database_copy)

	    self.photo_app_db_file = database_copy

	self.db = None
	self.view_mode = 0
	self.sort_method = 0
	self.sort_direction = 0

    def open_db(self):
	if (self.db is None):
            if (not file_exists(self.photo_app_db_file)):
	        print "photoapp.gui: Photo App DB not found: %s" % (self.photo_app_db_file)
	    else:
	        self.db = PhotoAppDB(self.photo_app_db_file)

    def close_db(self):
	try:
	    self.db.CloseDB()
	except:
	    pass

    def list_moments(self, year, month):
	n = 0
	ntotal = 0

	moments = self.db.GetMomentList(year, month)
	if (not moments):
	    print "photoapp.gui: No moments to display"

	ntotal = ntotal + len(moments)
	for (name, uuid) in moments:
	    print "photoapp.gui: moment: %s" % (name)
	    if year is None:
               url = build_url({'action': 'moments', 'year': name})
               item = gui.ListItem('%s' % (int(name)), iconImage=ICON_MOMENTS, thumbnailImage=ICON_MOMENTS)
	    elif month is None:
               url = build_url({'action': 'moments', 'year': year[0], 'month': name})
               item = gui.ListItem('%s-%s' % (int(year[0]), name), iconImage=ICON_MOMENTS, thumbnailImage=ICON_MOMENTS)
            else:
               url = build_url({'action': 'moments', 'year': year[0], 'month': month[0], 'day': name, 'uuid': uuid})
               item = gui.ListItem('%s-%s-%s' % (int(year[0]), month[0], name), iconImage=ICON_MOMENTS, thumbnailImage=ICON_MOMENTS)
	    plugin.addDirectoryItem(addon_handle, url, item, True)
	    n += 1

	if (n > 0):
	    plugin.addSortMethod(addon_handle, plugin.SORT_METHOD_UNSORTED)
	    plugin.addSortMethod(addon_handle, plugin.SORT_METHOD_LABEL)

	    sort_method = addon.getSetting('sort_method')
	    if (sort_method == ""):
	        sort_method = "0"
	        addon.setSetting('sort_method', sort_method)

	    sort_method = int(sort_method)
	    if (sort_method == 1):
	        self.sort_method = plugin.SORT_METHOD_LABEL

	return n

    def list_albums(self, folderUuid):
	n = 0
	ntotal = 0

	folders = self.db.GetFolderList(folderUuid)
	if (not folders):
	    print "photoapp.gui: No folders to display"

	ntotal = ntotal + len(folders)
	for (name, uuid) in folders:
	    print "photoapp.gui: folder: %s" % (name)
            url = build_url({'action': 'albums', 'folderUuid': uuid})
            item = gui.ListItem('%s' % (name), iconImage=ICON_FOLDER, thumbnailImage=ICON_FOLDER)
	    plugin.addDirectoryItem(addon_handle, url, item, True)
	    n += 1

	albums = self.db.GetAlbumList(folderUuid)
	if (not albums):
	    print "photoapp.gui: No albums to display"

	ntotal = ntotal + len(albums)
	for (name, uuid) in albums:
	    name = smart_utf8(name)
	    print "photoapp.gui: album: %s" % (name)
            url = build_url({'action': 'albums', 'uuid': uuid})
            item = gui.ListItem('%s' % (name), iconImage=ICON_ALBUMS, thumbnailImage=ICON_ALBUMS)
	    plugin.addDirectoryItem(addon_handle, url, item, True)
	    n += 1

	if (n > 0):
	    plugin.addSortMethod(addon_handle, plugin.SORT_METHOD_UNSORTED)
	    plugin.addSortMethod(addon_handle, plugin.SORT_METHOD_LABEL)

	    sort_method = addon.getSetting('sort_method')
	    if (sort_method == ""):
	        sort_method = "0"
	        addon.setSetting('sort_method', sort_method)

	    sort_method = int(sort_method)
	    if (sort_method == 1):
	        self.sort_method = plugin.SORT_METHOD_LABEL

	return n

    def list_slideshows(self, folderUuid):
	slideshows = self.db.GetAlbumList(folderUuid)
	if (not slideshows):
	    print "photoapp.gui: No Slideshow to display"
	    return 0

	n = 0
	ntotal = len(slideshows)
	for (slideshow, uuid) in slideshows:
	    slideshow = smart_utf8(slideshow)
	    print "photoapp.gui: slideshow: %s" % (slideshow)
            url = build_url({'action': 'slideshows', 'folderUuid': folderUuid, 'uuid': uuid})
            item = gui.ListItem('%s' % (slideshow), iconImage=ICON_SLIDESHOWS, thumbnailImage=ICON_SLIDESHOWS)
	    plugin.addDirectoryItem(addon_handle, url, item, True)
	    n += 1

	if (n > 0):
	    plugin.addSortMethod(addon_handle, plugin.SORT_METHOD_UNSORTED)
	    plugin.addSortMethod(addon_handle, plugin.SORT_METHOD_LABEL)

	    sort_method = addon.getSetting('sort_method')
	    if (sort_method == ""):
	        sort_method = "0"
	        addon.setSetting('sort_method', sort_method)

	    sort_method = int(sort_method)
	    if (sort_method == 1):
	        self.sort_method = plugin.SORT_METHOD_LABEL

	return n

    def list_photos(self, uuid, action):
	pictures = self.db.GetPictureList(uuid, action)
	if (not pictures):
	    print "photoapp.gui: No pictures to display"
	    return 0

	n = 0
	ntotal = len(pictures)
	for (filename, imagePath) in pictures:
	    filename = smart_utf8(filename)
	    imagePath = self.photo_app_picture_path + '/' + smart_utf8(imagePath)
            url = build_url({'action': 'showPicture', 'imagePath': imagePath})
            item = gui.ListItem('%s' % (filename), iconImage=imagePath, thumbnailImage=imagePath)
	    plugin.addDirectoryItem(addon_handle, imagePath, item, False)
	    n += 1

	if (n > 0):
	    plugin.addSortMethod(addon_handle, plugin.SORT_METHOD_UNSORTED)
	    plugin.addSortMethod(addon_handle, plugin.SORT_METHOD_LABEL)

	    sort_method = addon.getSetting('sort_method')
	    if (sort_method == ""):
	        sort_method = "0"
	        addon.setSetting('sort_method', sort_method)

	    sort_method = int(sort_method)
	    if (sort_method == 1):
	        self.sort_method = plugin.SORT_METHOD_LABEL

        view_mode = addon.getSetting('view_mode')
        if (view_mode == ""):
            view_mode = "0"
            addon.setSetting('view_mode', view_mode)

        view_mode = int(view_mode)
        if (view_mode == 1):
            self.view_mode = 514	    # PictureThumbView
        elif (view_mode == 2):
            self.view_mode = 510	    # PictureWrapView
        else:
            self.view_mode = 50  	    # List

	return n

    def main_menu(self):
        url = build_url({'action': 'moments'})
        item = gui.ListItem(addon.getLocalizedString(30000), iconImage=ICON_MOMENTS, thumbnailImage=ICON_MOMENTS)
	plugin.addDirectoryItem(addon_handle, url, item, True)

        url = build_url({'action': 'albums', 'folderUuid': 'TopLevelAlbums'})
        item = gui.ListItem(addon.getLocalizedString(30001), iconImage=ICON_ALBUMS, thumbnailImage=ICON_ALBUMS)
	plugin.addDirectoryItem(addon_handle, url, item, True)

        url = build_url({'action': 'slideshows', 'folderUuid': 'TopLevelSlideshows'})
        item = gui.ListItem(addon.getLocalizedString(30002), iconImage=ICON_SLIDESHOWS, thumbnailImage=ICON_SLIDESHOWS)
	plugin.addDirectoryItem(addon_handle, url, item, True)

	plugin.addSortMethod(addon_handle, plugin.SORT_METHOD_NONE)

        self.view_mode = 500	    # Preview View

	return 3

if (__name__ == "__main__"):
    action_result = None
    items = 0

    action = args.get('action', None)
    folderUuid = args.get('folderUuid', None)
    uuid = args.get('uuid', None)
    year = args.get('year', None)
    month = args.get('month', None)

    photoApp = PhotoAppGUI()
    photoApp.open_db()

    if action is None:
        items = photoApp.main_menu()
    elif not (uuid is None):
        items = photoApp.list_photos(uuid[0], action[0])
    elif action[0] == 'moments':
        items = photoApp.list_moments(year, month)
    elif action[0] == 'albums':
        items = photoApp.list_albums(folderUuid[0])
    elif action[0] == 'slideshows':
        items = photoApp.list_slideshows(folderUuid[0])

    photoApp.close_db()

    if (items == 0):
        action_result = addon.getLocalizedString(30100)
    else:
        plugin.endOfDirectory(addon_handle, True)
	xbmc.sleep(300)

        if (photoApp.view_mode):
	    xbmc.executebuiltin("Container.SetViewMode(%d)" % (photoApp.view_mode))
	if (photoApp.sort_method):
	    xbmc.executebuiltin("Container.SetSortMethod(%d)" % (photoApp.sort_method))
	if (photoApp.sort_direction != ""):
	    xbmc.executebuiltin("Container.SortDirection(%s)" % (photoApp.sort_direction))

    if (action_result):
        print "photoapp.gui: " + smart_utf8(action_result)
        xbmc.executebuiltin('XBMC.Notification(%s,%s,3000)' % (smart_utf8(__plugin__), smart_utf8(action_result)))
