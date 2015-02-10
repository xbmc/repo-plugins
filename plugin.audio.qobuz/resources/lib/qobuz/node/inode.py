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

import sys, os
import weakref

import qobuz
from constants import Mode
from node import Flag
from exception import QobuzXbmcError as Qerror
from gui.util import color, lang, runPlugin, containerUpdate, \
    getSetting
from debug import log, warn
from gui.contextmenu import contextMenu
from node import getNode
from renderer import renderer
import urllib
from time import time
from cache import cache
from storage import _Storage
from api import api

class INode(object):
    '''Our base node, every node must inherit or mimic is behaviour
        Parameters:
            parent: object, does this node have a parent
            parameters: dictionary, system argument parsed as dictionary
        
        Calling build_down on a node start the building process
            - pre_build_down: Retrieve data (disk, internet...) and store
                result in self.data
            - _build_down: If pre_build_down return true, parse data
                and populate our node with child
        The main buil_down method is responsible for the logic flow (recursive,
            depth, whiteFlag, blackFlag...)
    '''
    def __init__(self, parent=None, parameters={}):
        self.data = None
        self.parameters = parameters
        self.nt = None
        self.nid = self.get_parameter('nid')
        self.parent = parent
        self.content_type = "files"
        self.image = None
        self.childs = []
        self.label = ''
        self.label2 = None
        self.is_folder = True
        self.pagination_next = None
        self.pagination_prev = None
        self.offset = None
        self.hasWidget = False
        self.user_storage = None

    ''' Id '''
    @property
    def nid(self):
        return self._nid

    @nid.setter
    def nid(self, value):
        self._nid = value

    @nid.getter
    def nid(self):
        if self._data and 'id' in self._data:
            return self._data['id']
        return self._nid

    ''' Parent '''
    @property
    def parent(self):
        return self._parent

    @parent.setter
    def parent(self, parent):
        if not parent:
            self._parent = None
            return
        self._parent = weakref.proxy(parent)

    @parent.getter
    def parent(self):
        return self._parent

    def delete_tree(self):
        for child in self.childs:
            child.delete_tree()
        self.childs = None
        self.parent = None
        self.parameters = None

    ''' content_type '''
    @property
    def content_type(self):
        return self._content_type

    @content_type.getter
    def content_type(self):
        return self._content_type

    @content_type.setter
    def content_type(self, type):
        if type not in ['songs', 'albums', 'files', 'artists']:
            raise Qerror(
                who=self, what='invalid_type', additional=type)
        self._content_type = type

    ''' data '''
    @property
    def data(self):
        return self._data

    @data.getter
    def data(self):
        return self._data

    @data.setter
    def data(self, value):
        self._data = value
        self.hook_post_data()

    ''' Called after node data is set '''
    def hook_post_data(self):
        pass

    def get_property(self, pathList):
        """Property are just a easy way to access JSON data (self.data)
            Parameters:
            pathList: a string or a list of string, each string can be
                a path like 'album/image/large'
            Return:
                string (empty string when all fail or when there's no data)
            * When passing array of string the method return the first
            path returning data
            
            Example:
                image = self.get_property(['image/extralarge', 
                                       'image/mega', 
                                       'picture'])
        """
        if isinstance(pathList, basestring):
            return self.__get_property(pathList)
        for path in pathList:
            data = self.__get_property(path)
            if data:
                return data
        return ''

    def __get_property(self, path):
        """Helper used by get_property method
        """
        if not self.data:
            return ''
        xPath = path.split('/')
        root = self.data
        for i in range(0, len(xPath)):
            if not xPath[i] in root:
                return ''
            root = root[xPath[i]]
        if root and root != 'None':
            return root
        return ''

    def __add_pagination(self, data):
        """build_down helper: Add pagination data when needed
        """
        if not data:
            return False
        paginated = ['albums', 'labels', 'tracks', 'artists',
                     'playlists', 'playlist']
        items = None
        need_pagination = False
        for p in paginated:
            if p in data:
                items = data[p]
                if items['limit'] is None:
                    continue
                if items['total'] > (items['offset'] + items['limit']):
                    need_pagination = True
                    break
        if not need_pagination:
            return False
        url = self.make_url(offset=items['offset'] + items['limit'])
        self.pagination_next = url
        self.pagination_total = items['total']
        self.pagination_offset = items['offset']
        self.pagination_limit = items['limit']
        self.pagination_next_offset = items['offset'] + items['limit']

    '''
        Parameters
        A hash for storing script parameter, each node have a copy of them.
        TODO: each node don't need to copy parameter
    '''
    def set_parameters(self, parameters):
        """Setting parameters property
            Parameter:
                parameters: Dictionary
        """
        self.parameters = parameters

    def set_parameter(self, name, value, **ka):
        """Setting a parameter
            Parameters:
                name: parameter name
                value: parameter value
            
            * Optional quote=True/False, when quote=True we are using
            urllib.quote_plus befoer setting value
        """
        if 'quote' in ka and ka['quote'] == True:
            value = urllib.quote_plus(value)
        self.parameters[name] = value

    def get_parameter(self, name, **ka):
        if not self.parameters:
            return None
        if not name in self.parameters:
            return None
        if 'unQuote' in ka and ka['unQuote'] == True:
            return urllib.unquote_plus(self.parameters[name])
        return self.parameters[name]

    def del_parameter(self, name):
        if not name in self.parameters:
            return False
        del self.parameters[name]
        return True

    def make_url(self, **ka):
        '''Generate URL to navigate between nodes
            Nodes with custom parameters must override this method
            @todo: Ugly need rewrite =]
        '''
        if not 'mode' in ka:
            ka['mode'] = Mode.VIEW
        else:
            ka['mode'] = int(ka['mode'])
        if not 'nt' in ka:
            ka['nt'] = self.nt
        if not 'nid' in ka and self.nid:
            ka['nid'] = self.nid
     
        url = sys.argv[0] + '?mode=' + str(ka['mode']) + '&nt=' + \
            str(ka['nt'])
        if 'nid' in ka:
            url += "&nid=" + str(ka['nid'])
        offset = self.offset
        if 'offset' in ka: offset = ka['offset']
        if offset != None:
            url += '&offset=' + str(offset)
        if 'nm' in ka:
            url += '&nm=' + ka['nm']
        qnt = self.get_parameter('qnt')
        if 'qnt' in ka:
            qnt = ka['qnt']
        if qnt:
            url+= '&qnt=' + str(qnt)
        qid = self.get_parameter('qid')
        if 'qid' in ka:
            qid = ka['qid']
        if qid:
            url+= '&qid=' + str(qid)
        if 'query' in ka:
            url+= '&query=' + ka['query']
        return url

    '''
        Make Xbmc List Item
        return  a xbml list item
        Class can overload this method
    '''
    def makeListItem(self, **ka):
        import xbmcgui
        if not 'url' in ka:
            ka['url'] = self.make_url()
        if not 'label' in ka:
            ka['label'] = self.get_label()
        if not 'label2' in ka:
            ka['label2'] = self.get_label()
        if not 'image' in ka:
            ka['image'] = self.get_image()
        item = xbmcgui.ListItem(
            ka['label'],
            ka['label2'],
            ka['image'],
            ka['image'],
            ka['url']
        )
        ctxMenu = contextMenu()
        self.attach_context_menu(item, ctxMenu)
        item.addContextMenuItems(ctxMenu.getTuples(), ka['replaceItems'])
        item.addContextMenuItems(ctxMenu.getTuples(), ka['replaceItems'])
        return item

    def add_child(self, child):
        child.parent = self
        child.set_parameters(self.parameters)
        self.childs.append(child)
        return self

    def get_childs(self):
        return self.childs

    def set_label(self, label):
        self.label = label #label.encode('utf8', 'replace')
        return self

    def get_image(self):
        if self.image:
            return self.image
        if self.parent:
            return self.parent.get_image()
        return self.get_property('image')

    def set_image(self, image):
        self.image = image
        return self

    def get_label(self):
        return self.label

    def get_label2(self):
        return self.label2

    def render_nodes(self, nt, parameters, lvl = 1, whiteFlag = Flag.ALL, 
                     blackFlag = Flag.TRACK & Flag.STOPBUILD):
        render = renderer(nt, parameters)
        render.depth = -1
        render.whiteFlag = whiteFlag
        render.blackFlag = blackFlag
        render.asList = True
        render.run()
        return render

    # When returning False we are not displaying directory content
    def fetch(self, Dir, lvl=1, whiteFlag=None, blackFlag=None):
        '''This method fetch data from cache
        '''
        return True

    def populating(self, Dir, lvl=1, whiteFlag=None, blackFlag=None, 
                   gData=None):
        if Dir.Progress.iscanceled():
            return False
        if not gData:
            gData = {'count': 0,
                     'total': 100,
                     'startedOn': time()}
        if lvl != -1 and lvl < 1:
            return False
        Dir.update(gData, 'Fetching', '', '')
        if not (self.nt & blackFlag == self.nt):
            if not self.fetch(Dir, lvl, whiteFlag, blackFlag):
                return False
            else:
                self.__add_pagination(self.data)
        self.populate(Dir, lvl, whiteFlag, blackFlag)
        """ Recursive mode dont't decrement level """
        if lvl != -1:
            lvl -= 1
        label = self.get_label()
        gData['count'] = 0
        gData['total'] = len(self.childs)
        self.__add_pagination_node(Dir, lvl, whiteFlag)
        Dir.update(gData, 'Working', label, '')
        for child in self.childs:
            if Dir.is_canceled():
                return False
            """ Only white Flagged added to the listing """
            if child.nt & whiteFlag == child.nt:
                if not Dir.add_node(child):
                    warn(self, "Something went wrong... aborting")
                    self.childs = []
                    raise Qerror(who=self, what='build_down_abort')
                gData['count'] += 1
                Dir.update(gData, "Working", label, child.get_label())
            else:
                log(self, "Skipping node: %s" % ( Flag.to_s(child.nt)) )
            """ Calling builiding down on child """
            child.populating(Dir, lvl, whiteFlag, blackFlag, gData)
        return gData['count']

    def populate(self, xbmc_directory, lvl, Flag):
        """Hook/_build_down:
        This method is called by build_down, each object who
        inherit from Inode can overide it. Lot of object
        simply fetch data from qobuz (cached data)
        """
        pass
    
    def __add_pagination_node(self, Dir, lvl=1, whiteFlag=Flag.NODE):
        """Helper/Called by build_down to add special node when pagination is
        required
        """
        if self.pagination_next:
            colorItem = getSetting('color_item')
            params = qobuz.boot.params
            params['offset'] = self.pagination_next_offset
            params['nid'] = self.nid
            node = getNode(self.nt, params)
            node.data = self.data
            label = self.get_label()
            if not label and self.parent:
                label = self.parent.get_label()
            if self.label2: label = self.label2
            nextLabel = (
                '[ %s  %s / %s ]') % (color(colorItem, label),
                                      self.pagination_next_offset,
                                      self.pagination_total)
            node.label = nextLabel
            node.label2 = label
            self.add_child(node)

    def attach_context_menu(self, item, menu):
        """
            Note: Url made with make_url must set mode (like mode=Mode.VIEW)
            else we are copying current mode (for track it's Mode.PLAY ...)
        """
        ''' HOME '''
        colorCaution = getSetting('item_caution_color')

        url = self.make_url(nt=Flag.ROOT, mode=Mode.VIEW, nm='')
        menu.add(path='qobuz', label="Qobuz", cmd=containerUpdate(url, False),
                 id='', pos = -5)     
        ''' ARTIST '''
        if self.nt & (Flag.ALBUM | Flag.TRACK | Flag.ARTIST):
            artist_id = self.get_artist_id()
            #if not artist_id:
            #    import pprint
            #    print pprint.pformat(self.data)
            artist_name = self.get_artist()
            urlArtist = self.make_url(nt=Flag.ARTIST, nid=artist_id, 
                                      mode=Mode.VIEW)
            menu.add(path='artist/all_album', 
                          label="%s %s" % (lang(39001), artist_name), 
                          cmd=containerUpdate(urlArtist), pos=-10)

            ''' Similar artist '''
            url = self.make_url(nt=Flag.SIMILAR_ARTIST, 
                                nid=artist_id, mode=Mode.VIEW)
            menu.add(path='artist/similar', 
                          label=lang(39004), 
                          cmd=containerUpdate(url))
        ''' FAVORITES '''
        wf = self.nt & (~Flag.FAVORITES)
        if self.parent:
            wf = wf and self.parent.nt & ~Flag.FAVORITES
        if wf:
            ''' ADD TO FAVORITES / TRACKS'''
            url = self.make_url(nt=Flag.FAVORITES,
                                nm='', mode=Mode.VIEW)
            menu.add(path='favorites', label="Favorites", 
                     cmd=containerUpdate(url, True),pos=-9)   
            url = self.make_url(nt=Flag.FAVORITES, 
                                          nm='gui_add_tracks', 
                                          qid=self.nid, 
                                          qnt=self.nt, 
                                          mode=Mode.VIEW)
            menu.add(path='favorites/add_tracks', 
                          label=lang(39011) + ' tracks', cmd=runPlugin(url))
            ''' ADD TO FAVORITES / Albums'''
            url = self.make_url(nt=Flag.FAVORITES, 
                                          nm='gui_add_albums', 
                                          qid=self.nid, 
                                          qnt=self.nt, 
                                          mode=Mode.VIEW)
            menu.add(path='favorites/add_albums', 
                          label=lang(39011) + ' albums', cmd=runPlugin(url))
            ''' ADD TO FAVORITES / Artists'''
            url = self.make_url(nt=Flag.FAVORITES, 
                                          nm='gui_add_artists', 
                                          qid=self.nid, 
                                          qnt=self.nt, 
                                          mode=Mode.VIEW)
            menu.add(path='favorites/add_artists', 
                          label=lang(39011) + ' artists', cmd=runPlugin(url))

        if self.parent and (self.parent.nt & Flag.FAVORITES):
            url = self.make_url(nt=Flag.FAVORITES,
                                nm='', mode=Mode.VIEW)
            menu.add(path='favorites', label="Favorites", 
                     cmd=containerUpdate(url, True),pos=-9)  
            url = self.make_url(nt=Flag.FAVORITES, nm='gui_remove',
                                qid=self.nid, qnt=self.nt,
                                mode=Mode.VIEW)
            menu.add(path='favorites/remove', 
                     label='Remove %s' % (self.get_label()), 
                     cmd=runPlugin(url), color=colorCaution)
        wf = ~Flag.USERPLAYLISTS
#        if self.parent:
#            wf = wf and self.parent.nt & (~Flag.USERPLAYLISTS)
        if wf: 
            ''' PLAYLIST '''
            cmd = containerUpdate(self.make_url(nt=Flag.USERPLAYLISTS, 
                                    nid='', mode=Mode.VIEW))
            menu.add(path='playlist', pos = 1,
                          label="Playlist", cmd=cmd, mode=Mode.VIEW)

            ''' ADD TO CURRENT PLAYLIST '''
            cmd = runPlugin(self.make_url(nt=Flag.PLAYLIST, 
                                            nm='gui_add_to_current', 
                                            qnt=self.nt,
                                            mode=Mode.VIEW,
                                            qid=self.nid))
            menu.add(path='playlist/add_to_current', 
                          label=lang(39005), cmd=cmd)
            label = self.get_label()
            try:
                label = label.encode('utf8', 'replace')
            except:
                warn(self, "Cannot set query..." + repr(label))
                label = ''
            label = urllib.quote_plus(label)
            ''' ADD AS NEW '''
            cmd = runPlugin(self.make_url(nt=Flag.PLAYLIST,
                                            nm='gui_add_as_new', 
                                            qnt=self.nt,
                                            query=label,
                                            mode=Mode.VIEW,
                                            qid=self.nid))
            menu.add(path='playlist/add_as_new', 
                          label=lang(30080), cmd=cmd)

#            ''' Show playlist '''
#            if not (self.nt ^ Flag.USERPLAYLISTS != Flag.USERPLAYLISTS):
#                cmd = containerUpdate(self.make_url(nt=Flag.USERPLAYLISTS, 
#                                    id='', mode=Mode.VIEW))
#                menu.add(path='playlist/show', 
#                          label=lang(39006), cmd=cmd)

        ''' PLAYLIST / CREATE '''
        cFlag = (Flag.PLAYLIST | Flag.USERPLAYLISTS)
        if self.nt | cFlag == cFlag:
            cmd = runPlugin(self.make_url(nt=Flag.PLAYLIST, 
                                          nm="gui_create", mode=Mode.VIEW))
            menu.add(path='playlist/create', 
                          label=lang(39008), cmd=cmd)
        ''' VIEW BIG DIR '''
        cmd = containerUpdate(self.make_url(mode=Mode.VIEW_BIG_DIR))
        menu.add(path='qobuz/big_dir', 
                          label=lang(39002), cmd=cmd)
        ''' SCAN '''
        if getSetting('enable_scan_feature', isBool=True):
            query = urllib.quote_plus(self.make_url(mode=Mode.SCAN))
            url = self.make_url(nt=Flag.ROOT, mode=Mode.VIEW,
                                nm='gui_scan', query=query)
            menu.add(path='qobuz/scan', 
                            cmd=runPlugin(url),
                            label='scan')
        if self.nt & (Flag.ALL & ~Flag.ALBUM & ~Flag.TRACK 
                        & ~Flag.PLAYLIST):
            ''' ERASE CACHE '''
            cmd = runPlugin(self.make_url(nt=Flag.ROOT, nm="cache_remove", 
                                      mode=Mode.VIEW))
            menu.add(path='qobuz/erase_cache', 
                          label=lang(31009), cmd=cmd, 
                          color=colorCaution, pos=10)

    def get_user_storage(self):
        if self.user_storage:
            return self.user_storage
        filename = os.path.join(cache.base_path, 'localuserdata-%s.local' %
                            str(api.user_id))
        self.user_storage = _Storage(filename)
        return self.user_storage

    def get_user_data(self):
        data = api.get('/user/login', username=api.username, 
                       password=api.password)
        if not data: 
            return None
        return data['user']
