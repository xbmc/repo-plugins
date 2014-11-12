'''
    qobuz.node.album
    ~~~~~~~~~~~~~~~~

    :copyright: (c) 2012 by Joachim Basmaison, Cyril Leclerc
    :license: GPLv3, see LICENSE for more details.
'''
import os
from inode import INode
from debug import warn
from gui.util import getImage, getSetting, htm2xbmc
from gui.contextmenu import contextMenu
from api import api
from node import getNode, Flag
from sys import platform as _platform
import simplejson as json
import urllib, urllib2
import xbmc
import time
try:
	import commands
except:
	pass
try:
	import win32com.client
except:
	pass
from sys import platform as _platform



SPECIAL_PURCHASES = ['0000020110926', '0000201011300', '0000020120220',
                     '0000020120221']


class Node_album(INode):
    '''
        @class Node_product:
    '''
    def __init__(self, parent, params):
        super(Node_album, self).__init__(parent, params)
        self.nt = Flag.ALBUM
        self.image = getImage('album')
        self.content_type = 'songs'
        self.is_special_purchase = False
        self.offset = None
        self.imageDefaultSize = 'large'
        self.label = 'Album'
        try:
            self.imageDefaultSize = getSetting('image_default_size')
        except:
            pass

        @property
        def nid(self):
            return self._nid
        @nid.getter
        def nid(self):
            return self._nid
        @nid.setter
        def nid(self, value):
            self._id = value
            if value in SPECIAL_PURCHASES:
                self.is_special_purchase = True

    def fetch(self, Dir, lvl, whiteFlag, blackFlag):
        data = api.get('/album/get', album_id=self.nid)
        if not data:
            warn(self, "Cannot fetch product data")
            return False
        self.data = data
        return True

    def populate(self, Dir, lvl, whiteFlag, blackFlag):
    	theUrls = ''
    	launchApp = False
    	interlude = 0
        for track in self.data['tracks']['items']:
            node = getNode(Flag.TRACK)
            if not 'image' in track:
                track['image'] = self.get_image()
            node.data = track
            track_id = track.get('id')
            track_duration = track.get('duration')
            format_id = 6 if getSetting('streamtype') == 'flac' else 5
            data = api.get('/track/getFileUrl', format_id=format_id,
            	track_id=track_id, user_id=api.user_id)
            if not data:
            	theUrls += "Cannot get stream type for track (network problem?)"
            else:
            	if (not 'sample' in (data['url'])):
            		theUrls += str(data['url'])
            		theUrls += '\n'
            		if getSetting('audiophile') == 'true':
    					launchApp = True
            self.add_child(node)
            if getSetting('gapless') == 'false' and launchApp:
            	node.get_streaming_url()
            	interlude = int(getSetting('interlude'))
            	time.sleep(int(track_duration)+interlude)
        if getSetting('gapless') == 'true' and launchApp:
        	qobuzPlaylist = str(os.path.expanduser('~'))
        	qobuzPlaylist += '/Music/QobuzNow.m3u8'
        	completeName = os.path.abspath(qobuzPlaylist)
        	file1 = open(completeName,"w")
        	toFile = theUrls
        	file1.write(toFile)
        	file1.close
        	if _platform == "darwin":
        		#if __name__ == '__main__':
        			#theUrls += str(earth_coords())
        			#theUrls += '\n'
        		try:          
        			cmd = """osascript -e 'tell app "HQPlayerDesktop" to quit'"""
        			os.system(cmd)
        			os.system("/Applications/HQPlayerDesktop.app/Contents/MacOS/HQPlayerDesktop "+completeName+"&")
        			#cmd = """osascript<<END
        				#launch application "System Events"
        					#tell application "System Events"
        						#set frontmost of process "HQPlayerDesktop3" to true
        					#end tell
        			#END"""
        			os.system(cmd)
        		except:
        			os.system("open "+completeName)
        	elif _platform == "win32":
        		os.system('TASKKILL /F /IM HQPlayer-desktop.exe')
        		os.startfile(completeName, 'open')
        return len(self.data['tracks']['items'])
	
	#def earth_coords():
		#cmd = """arch -i386 osascript -e 'tell application "Google Earth"
				#set viewInf to GetViewInfo
            	#set coords to {latitude of viewInf, longitude of viewInf}
            #end tell
            #return coords'"""
    	#return [float(c) for c in commands.getoutput(cmd).split(", ")]
	
    def make_url(self, **ka):
        if 'asLocalURL' in ka and ka['asLocalURL']:
            from constants import Mode
            ka['mode'] = Mode.SCAN
        return super(Node_album, self).make_url(**ka)
    
    def makeListItem(self, replaceItems=False):
        import xbmc, xbmcgui
        image = self.get_image()
        thumb = xbmc.getCacheThumbName(image)
        item = xbmcgui.ListItem(
            label=self.get_label(),
            label2=self.get_label(),
            iconImage=image,
            thumbnailImage=image,
            path=self.make_url(),
        )
        item.setInfo('music', infoLabels={
            'genre': self.get_genre(),
            'year': self.get_year(),
            'artist': self.get_artist(),
            'title': self.get_title(),
            'album': self.get_title(),
            'comment': self.get_description()
        })
        ctxMenu = contextMenu()
        self.attach_context_menu(item, ctxMenu)
        item.addContextMenuItems(ctxMenu.getTuples(), replaceItems)
        return item

    '''
    PROPERTIES
    '''
    def get_artist(self):
        return self.get_property(['artist/name',
                               'interpreter/name', 
                               'composer/name'])

    def get_album(self):
        album = self.get_property('name')
        if not album:
            return ''
        return album

    def get_artist_id(self):
        return self.get_property(['artist/id',
                               'interpreter/id',
                              'composer/id'])

    def get_title(self):
        return self.get_property('title')

    def get_image(self, size = None):
        if not size:
            size = self.imageDefaultSize
        return self.get_property(['image/%s' % (size),
                                   'image/large', 
                                   'image/small',
                                   'image/thumbnail'])

    def get_label(self):
        artist = self.get_artist() or 'VA'
        label = '%s - %s' % (artist, self.get_title())
        return label

    def get_genre(self):
        return self.get_property('genre/name')

    def get_year(self):
        import time
        date = self.get_property('released_at')
        year = 0
        try:
            year = time.strftime("%Y", time.localtime(date))
        except:
            pass
        return year

    def get_description(self):
        return htm2xbmc(self.get_property('description'))
