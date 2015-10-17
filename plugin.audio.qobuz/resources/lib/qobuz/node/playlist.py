'''
    qobuz.node.playlist
    ~~~~~~~~~~~~~~~~~~

    :part_of: xbmc-qobuz
    :copyright: (c) 2012 by Joachim Basmaison, Cyril Leclerc
    :license: GPLv3, see LICENSE for more details.
'''
import xbmcgui  # @UnresolvedImport
from inode import INode
from node import getNode, Flag
from api import api
from cache import cache
from debug import warn, info
from renderer import renderer
from gui.util import notify_warn, notify_error, notify_log, getSetting
from gui.util import color, lang, getImage, runPlugin, executeBuiltin
from gui.util import containerRefresh, containerUpdate
from gui.contextmenu import contextMenu
from constants import Mode

dialogHeading = 'Qobuz playlist'


class Node_playlist(INode):
    """@class Node_playlist:
    """

    def __init__(self, parent=None, parameters=None):
        super(Node_playlist, self).__init__(parent, parameters)
        self.nt = Flag.PLAYLIST
        self.label = None
        self.current_playlist_id = None
        self.b_is_current = False
        self.is_my_playlist = False
        self.url = None
        self.is_folder = True
        self.packby = ''
        if self.packby == 'album':
            self.content_type = 'albums'
        else:
            self.content_type = 'songs'
        self.offset = self.get_parameter('offset') or 0
        self.image = getImage('song')

    def get_label(self):
        return self.label or self.get_name()

    def set_is_my_playlist(self, b):
        self.is_my_playlist = b

    def set_is_current(self, b):
        self.b_is_current = b

    def is_current(self):
        return self.b_is_current

    def fetch(self, Dir, lvl, whiteFlag, blackFlag):
        limit = getSetting('pagination_limit', isInt=True)
        data = api.get('/playlist/get', playlist_id=self.nid,
                       offset=self.offset, limit=limit, extra='tracks')
        if not data:
            warn(self, "Build-down: Cannot fetch playlist data")
            return False
        self.data = data
        return True

    def populate(self, Dir, lvl, whiteFlag, blackFlag):
        for track in self.data['tracks']['items']:
            node = getNode(Flag.TRACK)
            node.data = track
            self.add_child(node)
        return True

    def get_name(self):
        return self.get_property(['name', 'title'])

    def get_image(self):
        userdata = self.get_user_data()
        if userdata:
            if self.get_owner() == userdata['login']:
                return userdata['avatar']
        return getImage('song')

    def get_owner(self):
        return self.get_property('owner/name')

    def get_owner_id(self):
        return self.get_property('owner/id')

    def get_description(self):
        return self.get_property('description')

    def makeListItem(self, replaceItems=False):
        colorItem = getSetting('item_default_color')
        colorPl = getSetting('item_section_color')
        label = self.get_label()
        image = self.get_image()
        owner = self.get_owner()
        url = self.make_url()
        if not self.is_my_playlist:
            label = '%s - %s' % (color(colorItem, owner), label)
        if self.b_is_current:
            label = '-o] %s [o-' % (color(colorPl, label))
        item = xbmcgui.ListItem(label,
                                owner,
                                image,
                                image,
                                url)
        if not item:
            warn(self, "Error: Cannot make xbmc list item")
            return None
        item.setPath(url)
        ctxMenu = contextMenu()
        self.attach_context_menu(item, ctxMenu)
        item.addContextMenuItems(ctxMenu.getTuples(), replaceItems)
        return item

    def attach_context_menu(self, item, menu):
        colorCaution = getSetting('item_caution_color')
        login = getSetting('username')
        isOwner = True
        cmd = containerUpdate(self.make_url(nt=Flag.USERPLAYLISTS,
                                            id='', mode=Mode.VIEW))
        menu.add(path='playlist', pos=1,
                 label="Playlist", cmd=cmd, mode=Mode.VIEW)
        if login != self.get_property('owner/name'):
            isOwner = False

        if isOwner:
            url = self.make_url(nt=Flag.PLAYLIST, mode=Mode.VIEW,
                                nm='set_as_current')
            menu.add(path='playlist/set_as_current', label=lang(30163),
                     cmd=containerUpdate(url))

            url = self.make_url(nt=Flag.PLAYLIST, nm='gui_rename')
            menu.add(path='playlist/rename', label=lang(30165),
                     cmd=runPlugin(url))

        else:
            url = self.make_url(nt=Flag.PLAYLIST, nm='subscribe')
            menu.add(path='playlist/subscribe', label=lang(30168),
                     cmd=runPlugin(url))

        url = self.make_url(nt=Flag.PLAYLIST, nm='gui_remove')
        menu.add(path='playlist/remove', label=lang(30166),
                 cmd=runPlugin(url), color=colorCaution)
        super(Node_playlist, self).attach_context_menu(item, menu)

    def remove_tracks(self, tracks_id):
        if not api.playlist_deleteTracks(playlist_id=self.nid,
                                         playlist_track_ids=tracks_id):
            return False
        return True

    def gui_remove_track(self):
        qid = self.get_parameter('qid')
        print "Removing track %s from playlist %s" % (qid, self.nid)
        if not self.remove_tracks(qid):
            notify_error(dialogHeading, 'Cannot remove track!')
            return False
        self.delete_cache(self.nid)
        notify_log(dialogHeading, 'Track removed from playlist')
        executeBuiltin(containerRefresh())
        return True

    def gui_add_to_current(self):
        cid = self.get_current_playlist()
        qnt = int(self.get_parameter('qnt'))
        qid = self.get_parameter('qid')
        nodes = []
        if qnt & Flag.SEARCH == Flag.SEARCH:
            self.del_parameter('query')
        if qnt & Flag.TRACK == Flag.TRACK:
            node = getNode(qnt, {'nid': qid})
            node.fetch(None, None, None, Flag.NONE)
            nodes.append(node)
        else:
            render = renderer(qnt, self.parameters)
            render.depth = -1
            render.whiteFlag = Flag.TRACK
            render.asList = True
            render.run()
            nodes = render.nodes
        ret = xbmcgui.Dialog().select('Add to current playlist', [
            node.get_label() for node in nodes
        ])
        if ret == -1:
            return False
        ret = self._add_tracks(cid, nodes)
        if not ret:
            notif_warn('Qobuz', 'Failed to add tracks')
            return False
        self.delete_cache(cid)
        notify_log('Qobuz / Tracks added', '%s added' % (len(nodes)))
        return True

    def _add_tracks(self, playlist_id, nodes):
        if len(nodes) < 1:
            warn(self, 'Empty list...')
            return False
        step = 50
        start = 0
        numtracks = len(nodes)
        if numtracks > 1000:
            notify_error('Qobuz', 'Max tracks per playlist reached (1000)'
                         '\nSkipping %s tracks' % (numtracks - 1000))
            numtracks = 1000
        while start < numtracks:
            if (start + step) > numtracks:
                step = numtracks - start
            str_tracks = ''
            info(self, "Adding tracks start: %s, end: %s" %
                 (start, start + step))
            for i in range(start, start + step):
                node = nodes[i]
                if node.nt != Flag.TRACK:
                    warn(self, "Not a Node_track node")
                    continue
                str_tracks += '%s,' % (str(node.nid))
            if not api.playlist_addTracks(
                    playlist_id=playlist_id, track_ids=str_tracks):
                return False
            start += step
        return True

    def gui_add_as_new(self, name=None):
        nodes = []
        qnt = int(self.get_parameter('qnt'))
        qid = self.get_parameter('qid')
        if qnt & Flag.SEARCH:
            self.del_parameter('query')
        if qnt & Flag.TRACK == Flag.TRACK:
            node = getNode(qnt, {'nid': qid})
            node.fetch(None, None, None, Flag.NONE)
            nodes.append(node)
        else:
            render = renderer(qnt, self.parameters)
            render.depth = -1
            render.whiteFlag = Flag.TRACK
            render.asList = True
            render.run()
            nodes = render.nodes
            if not name and render.root.get_parameter('query', unQuote=True):
                name = render.root.get_parameter('query', unQuote=True)
        if not name:
            name = self.get_parameter('query',
                                      unQuote=True) or self.get_label()
        ret = xbmcgui.Dialog().select('Create playlist %s' % (name), [
            node.get_label() for node in nodes
        ])
        if ret == -1:
            return False
        playlist = self.create(name)
        if not playlist:
            notify_error('Qobuz', 'Playlist creationg failed')
            warn(self, "Cannot create playlist...")
            return False
        if not self._add_tracks(playlist['id'], nodes):
            notify_error('Qobuz / Cannot add tracks', "%s" % (name))
            return False
        self.delete_cache(playlist['id'])
        notify_log('Qobuz / Playlist added', '[%s] %s' % (len(nodes), name))
        return True

    def set_as_current(self, playlist_id=None):
        if not playlist_id:
            playlist_id = self.nid
        if not playlist_id:
            warn(self, 'Cannot set current playlist without id')
            return False
        userdata = self.get_user_storage()
        userdata['current_playlist'] = int(playlist_id)
        return userdata.sync()

    def get_current_playlist(self):
        userdata = self.get_user_storage()
        if not 'current_playlist' in userdata:
            return None
        return int(userdata['current_playlist'])

    def gui_rename(self, playlist_id=None):
        if not playlist_id:
            playlist_id = self.nid
        if not playlist_id:
            warn(self, "Can't rename playlist without id")
            return False
        from gui.util import Keyboard
        data = api.get('/playlist/get', playlist_id=playlist_id)
        if not data:
            warn(self, "Something went wrong while renaming playlist")
            return False
        self.data = data
        currentname = self.get_name()
        k = Keyboard(currentname, lang(30080))
        k.doModal()
        if not k.isConfirmed():
            return False
        newname = k.getText()
        newname = newname.strip()
        if not newname:
            notify_error(dialogHeading, "Don't u call ure child something?")
            return False
        if newname == currentname:
            return True
        res = api.playlist_update(playlist_id=playlist_id, name=newname)
        if not res:
            warn(self, "Cannot rename playlist with name %s" % (newname))
            return False
        self.delete_cache(playlist_id)
        notify_log(lang(30080), (u"%s: %s") % (lang(30165), currentname))
        executeBuiltin(containerRefresh())
        return True

    def create(self, name, isPublic="true", isCollaborative="false"):
        return api.playlist_create(name=name,
                                   is_public=isPublic,
                                   is_collaborative=isCollaborative)

    def gui_create(self):
        query = self.get_parameter('query', unQuote=True)
        if not query:
            from gui.util import Keyboard
            k = Keyboard('', lang(30182))
            k.doModal()
            if not k.isConfirmed():
                warn(self, 'Creating playlist aborted')
                return None
            query = k.getText()
        ret = self.create(query)
        if not ret:
            warn(self, "Cannot create playlist named '" + query + "'")
            return None
        self.set_as_current(ret['id'])
        self.delete_cache(ret['id'])
        url = self.make_url(nt=Flag.USERPLAYLISTS)
        executeBuiltin(containerUpdate(url))
        return ret['id']

    def gui_remove(self, playlist_id=None):
        if not playlist_id:
            playlist_id = self.nid
        if not playlist_id:
            notify_error(dialogHeading,
                         'Invalid playlist %s' % (str(playlist_id)))
            return False
        login = getSetting('username')
        offset = 0
        limit = getSetting('pagination_limit')
        data = api.get('/playlist/get', playlist_id=playlist_id, limit=limit,
                       offset=offset)
        name = ''
        if 'name' in data:
            name = data['name']
        ok = xbmcgui.Dialog().yesno(lang(30166),
                                    lang(30054),
                                    color('FFFF0000', name))
        if not ok:
            info(self, "Deleting playlist aborted...")
            return False
        res = False
        if data['owner']['name'] == login:
            info(self, "Deleting playlist: " + str(playlist_id))
            res = api.playlist_delete(playlist_id=playlist_id)
        else:
            info(self, 'Unsuscribe playlist' + str(playlist_id))
            res = api.playlist_unsubscribe(playlist_id=playlist_id)
        if not res:
            warn(self, "Cannot delete playlist with id " + str(playlist_id))
            notify_error(lang(30183), lang(30186) + name)
            return False
        self.delete_cache(playlist_id)
        notify_log(lang(30183), (lang(30184) + "%s" + lang(30185)) % (name))
        url = self.make_url(nt=Flag.USERPLAYLISTS, mode=Mode.VIEW, nm='',
                            nid='')
        executeBuiltin(containerUpdate(url, True))
        return False

    def subscribe(self):
        if api.playlist_subscribe(playlist_id=self.nid):
            notify_log(lang(30183), lang(30187))
            self.delete_cache(self.nid)
            return True
        else:
            return False

    def delete_cache(self, playlist_id):
        limit = getSetting('pagination_limit')
        upkey = cache.make_key('/playlist/getUserPlaylists', limit=limit,
                               offset=self.offset, user_id=api.user_id)
        pkey = cache.make_key('/playlist/get', playlist_id=playlist_id,
                              offset=self.offset, limit=limit, extra='tracks')
        cache.delete(upkey)
        cache.delete(pkey)
