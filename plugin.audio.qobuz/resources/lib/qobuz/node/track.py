#     Copyright 2011 Joachim Basmaison, Cyril Leclerc
#
#     This file is part of xbmc-qobuz.
#
#     xbmc-qobuz is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
#
#     xbmc-qobuz is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.   See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with xbmc-qobuz.   If not, see <http://www.gnu.org/licenses/>.
import qobuz
from constants import Mode
from flag import NodeFlag as Flag
from inode import INode
from debug import warn
from gui.util import lang, getImage, runPlugin
from gui.contextmenu import contextMenu
from api import api

'''
    NODE TRACK
'''


class Node_track(INode):

    def __init__(self, parent=None, parameters=None):
        super(Node_track, self).__init__(parent, parameters)
        self.type = Flag.TRACK
        self.content_type = 'songs'
        self.qobuz_context_type = 'playlist'
        self.is_folder = False
        self.status = None
        self.image = getImage('song')

    def pre_build_down(self, Dir, lvl, whiteFlag, blackFlag):
        if blackFlag & Flag.STOPBUILD == Flag.STOPBUILD:
            return False
        data = qobuz.registry.get(name='track', id=self.id)
        if not data:
            return False
        self.data = data['data']
        return True
    
    def _build_down(self, Dir, lvl, whiteFlag, blackFlag):
        Dir.add_node(self)
        return True

    def make_url(self, **ka):
        if 'asLocalURL' in ka and ka['asLocalURL']:
            import pprint
            # print pprint.pformat(self.data)
            return 'http://127.0.0.1:33574/qobuz/%s/%s/%s.mpc' % (
                    str(self.get_artist_id()),
                    str(self.parent.id),
                    str(self.id))
        if not 'mode' in ka: 
            ka['mode'] = Mode.PLAY 
        return super(Node_track, self).make_url(**ka)

    def get_label(self, sFormat="%a - %t"):
        sFormat = sFormat.replace("%a", self.get_artist())
        sFormat = sFormat.replace("%t", self.get_title())
        sFormat = sFormat.replace("%A", self.get_album())
        sFormat = sFormat.replace("%n", str(self.get_track_number()))
        sFormat = sFormat.replace("%g", self.get_genre())
        return sFormat

    def get_composer(self):
        try:
            return self.get_property('composer/name')
        except:
            return -1

    def get_interpreter(self):
        try:
            return self.get_property('performer/name')
        except:
            return -1

    def get_album(self):
        try:
            album = self.get_property('album/title')
        except:
            return -1
        if album:
            return album
        if not self.parent:
            return ''
        if self.parent.type & Flag.PRODUCT:
            return self.parent.get_title()
        return ''

    def get_image(self):
        image = self.get_property(['album/image/large', 'image/large', 
                                      'image/small',
                                      'image/thumbnail', 'image'])
        if image:
            return image.replace('_230.', '_600.')
        if not self.parent:
            return self.image
        if self.parent.type & (Flag.PRODUCT | Flag.PLAYLIST):
            return self.parent.get_image()

    def get_playlist_track_id(self):
        return self.get_property('playlist_track_id')

    def get_position(self):
        return self.get_property('position')

    def get_title(self):
        return self.get_property('title')

    def get_genre(self):
        genre = self.get_property('album/genre/name')
        if genre:
            return genre
        if not self.parent:
            return ''
        if self.parent.type & Flag.PRODUCT:
            return self.parent.get_genre()
        return ''

    def get_streaming_url(self):
        data = qobuz.registry.get(name='user-stream-url', 
                                  id=self.id)
        if not data:
            return ''
        if not 'data' in data or not 'url' in data['data']:
            warn(self, 
                 "streaming_url, no url returned\n" +  
                 "API Error: %s" % (api.error)) 
            return ''
        return data['data']['url']

    def get_artist(self):
        return self.get_property(['artist/name',
                               'composer/name',
                               'performer/name',
                               'interpreter/name',
                               'composer/name',
                               'album/artist/name'])

    def get_artist_id(self):
        s = self.get_property(['artist/id',
                               'composer/id',
                               'performer/id',
                               'interpreter/id'])
        if s:
            return int(s)
        return None

    def get_track_number(self):
        return self.get_property('track_number')

    def get_media_number(self):
        return self.get_property('media_number')

    def get_duration(self):
        duration = self.get_property('duration')
        if duration and int(duration) != 0:
            return duration
        else:
            return -1

    def get_year(self):
        import time
        try:
            date = self.get_property('album/released_at')
            if not date and self.parent and self.parent.type & Flag.PRODUCT:
                return self.parent.get_year()
        except:
            pass
        year = 0
        try:
            year = time.strftime("%Y", time.localtime(date))
        except:
            pass

        return year

    def get_description(self):
        if self.parent:
            return self.parent.get_description()
        return ''

    def is_sample(self):
        nid = self.id or self.parameters['nid']
        data = qobuz.registry.get(name='user-stream-url', id=nid)
        if not data:
            warn(self, "Cannot get stream type for track (network problem?)")
            return ''
        try:
            return data['data']['sample']
        except:
            return ''

    def get_mimetype(self):
        nid = self.id or self.parameters['nid']
        data = qobuz.registry.get(name='user-stream-url', id=nid)
        formatId = None
        if not data:
            warn(self, "Cannot get mime/type for track (network problem?)")
            return ''
        try:
            formatId = int(data['data']['format_id'])
        except:
            warn(self, "Cannot get mime/type for track (restricted track?)")
            return ''
        mime = ''
        if formatId == 6:
            mime = 'audio/flac'
        elif formatId == 5:
            mime = 'audio/mpeg'
        else:
            warn(self, "Unknow format " + str(formatId))
            mime = 'audio/mpeg'
        return mime
    
    """ We add this information only when playing item because it require
        use to fetch data from Qobuz
    """
    def item_add_playing_property(self, item):
        mime = self.get_mimetype()
        if not mime:
            warn(self, "Cannot set item streaming url")
            return False
        item.setProperty('mimetype', mime)
        item.setPath(self.get_streaming_url())
        return True
    
    def makeListItem(self, replaceItems=False):
        import xbmcgui
        media_number = self.get_media_number()
        if not media_number:
            media_number = 1
        else:
            media_number = int(media_number)
        duration = self.get_duration()
        if duration == -1:
            import pprint
            print "Error: no duration\n%s" % (pprint.pformat(self.data))
        label = self.get_label()
        isplayable = 'true'

        # Disable free account checking here, purchased track are
        # still playable even with free account, but we don't know yet.
        # if qobuz.gui.is_free_account():
        #    duration = 60
        # label = '[COLOR=FF555555]' + label + '[/COLOR]
        # [[COLOR=55FF0000]Sample[/COLOR]]'
#        print "MakeItem %s" % (self.get_image())
        mode = Mode.PLAY
        url = self.make_url(mode=mode)
        image = self.get_image()
        item = xbmcgui.ListItem(label,
                                label,
                                image,
                                image,
                                url)
        item.setIconImage(image)
        item.setThumbnailImage(image)
        if not item:
            warn(self, "Cannot create xbmc list item")
            return None
        item.setPath(url)
        track_number = self.get_track_number()
        if not track_number:
            track_number = 0
        else:
            track_number = int(track_number)
        mlabel = self.get_property('label/name')
        description = self.get_description()
        comment = ''
        if mlabel:
            comment = mlabel
        if description:
            comment += ' - ' + description
        item.setInfo(type='music', infoLabels={
                     'count': self.id,
                     'title': self.get_title(),
                     'album': self.get_album(),
                     'genre': self.get_genre(),
                     'artist': self.get_artist(),
                     'tracknumber': track_number,
                     'duration': duration,
                     'year': self.get_year(),
                     'comment': 'Qobuz Music Streaming',
                     'lyrics': "Chant down babylon lalalala" 
                     })
        item.setProperty('DiscNumber', str(media_number))
        item.setProperty('IsPlayable', isplayable)
        item.setProperty('IsInternetStream', isplayable)
        item.setProperty('Music', isplayable)
#        item.setProperty('mimetype', 'audio/mpeg')
        ctxMenu = contextMenu()
        self.attach_context_menu(item, ctxMenu)
        item.addContextMenuItems(ctxMenu.getTuples(), replaceItems)
        return item

    def attach_context_menu(self, item, menu):
        if self.parent and (self.parent.type & Flag.PLAYLIST == Flag.PLAYLIST):
            url = self.parent.make_url(type=Flag.PLAYLIST,
                id=self.parent.id,
                qid=self.get_playlist_track_id(),
                nm='gui_remove_track',
                mode=Mode.VIEW)
            # print "URL %s" % (url)
            menu.add(path='playlist/remove', 
                     label=lang(30073),
                     cmd=runPlugin(url))

        ''' Calling base class '''
        super(Node_track, self).attach_context_menu(item, menu)
