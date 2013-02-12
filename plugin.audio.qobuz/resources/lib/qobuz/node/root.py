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
from inode import INode
from gui.util import getSetting, executeBuiltin, lang
from cache import cache
from cache.cacheutil import clean_all
from node import getNode, Flag

class Node_root(INode):
    '''Our root node, we are displaying all qobuz nodes from here
    '''
    def __init__(self, parent=None, parameters=None):
        super(Node_root, self).__init__(parent, parameters)
        self.nt = Flag.ROOT
        self.content_type = 'files'
        self.label = "Qobuz"

    def populate(self, Dir, lvl, whiteFlag, blackFlag):
        self.add_child(getNode(Flag.USERPLAYLISTS))
        if getSetting('show_recommendations', isBool=True):
            self.add_child(getNode(Flag.RECOMMENDATION))
        self.add_child(getNode(Flag.PURCHASES))
        self.add_child(getNode(Flag.FAVORITES))
        if getSetting('search_enabled', isBool=True):
            search = getNode(Flag.SEARCH)
            search.search_type = 'albums'
            self.add_child(search)
            search = getNode(Flag.SEARCH)
            search.search_type = 'tracks'
            self.add_child(search)
            search = getNode(Flag.SEARCH)
            search.search_type = 'artists'
            self.add_child(search)
        self.add_child(getNode(Flag.FRIEND_LIST))
        self.add_child(getNode(Flag.GENRE))
        self.add_child(getNode(Flag.PUBLIC_PLAYLISTS))
        return True

    def cache_remove(self):
        '''GUI/Removing all cached data
        '''
        from gui.util import yesno, notifyH, getImage
        from debug import log
        if not yesno(lang(31102), lang(31103)):
            log(self, "Deleting cached data aborted")
            return False
        if clean_all(cache):
            notifyH(lang(31100), lang(31104))
        else:
            notifyH(lang(31100), lang(31101),
                    getImage('icon-error-256'))
        return True

    def gui_scan(self):
        '''Scanning directory specified in query parameter
        '''
        query = self.get_parameter('query', unQuote=True)
        print "Scanning folder: %s" % (query)
        executeBuiltin('XBMC.UpdateLibrary("music", "%s")' % (query))
