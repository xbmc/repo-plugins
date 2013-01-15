# -*- coding: UTF-8 -*-
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
from debug import warn
from irenderer import IRenderer
from gui.util import notifyH, getSetting
from exception import QobuzXbmcError as Qerror

class QobuzXbmcRenderer(IRenderer):
    """Specific renderer for Xbmc
        Parameter:
            node_type: int, node type (node.NodeFlag)
            params: dictionary, parameters passed to our plugin
        * You can set parameter after init (see renderer.Irenderer)
    """
    def __init__(self, node_type, params=None):
        super(QobuzXbmcRenderer, self).__init__(node_type, params)

    def add_directory_item(self, **ka):
        """Add item to directory
            Named parameter:
                is_folder: bool (default: True)
                image: string (default: '') 
        """
        if not 'is_folder' in ka or ka['is_folder']:
            ka['is_folder'] = 1
        else:
            ka['is_folder'] = 0
        if not 'image' in ka:
            ka['image'] = ''
        item = ka['dir']._xbmc_item(**ka)
        ka['dir'].add_item(url=ka['url'], item=item, 
                           is_folder=ka['is_folder'])

    def run(self):
        """Building our tree, creating root node based on our node_type
        """
        if not self.set_root_node():
            warn(self, 
                 ("Cannot set root node (%s, %s)") % 
                 (str(self.node_type), str(self.root.get_parameter('nid'))))
            return False
        if self.root.hasWidget:
            return self.root.displayWidget()
        if self.has_method_parameter():
            return self.execute_method_parameter()
        from gui.directory import Directory
        Dir = Directory(self.root, self.nodes, 
                        withProgress=self.enable_progress)
        Dir.asList = self.asList
        Dir.handle = qobuz.boot.handle
        if getSetting('contextmenu_replaceitems', isBool=True):
            Dir.replaceItems = True
        try:
            ret = self.root.build_down(Dir, self.depth, 
                                       self.whiteFlag, self.blackFlag)
        except Qerror as e:
            Dir.end_of_directory(False)
            Dir = None
            warn(self, 
                 "Error while populating our directory: %s" % (repr(e)))
            return False
        if not self.asList:
            import xbmcplugin
            Dir.set_content(self.root.content_type)
            methods = [
                       xbmcplugin.SORT_METHOD_UNSORTED,
                       xbmcplugin.SORT_METHOD_LABEL,
                       xbmcplugin.SORT_METHOD_DATE,
                       xbmcplugin.SORT_METHOD_TITLE,
                       xbmcplugin.SORT_METHOD_VIDEO_YEAR,
                       xbmcplugin.SORT_METHOD_GENRE,
                       xbmcplugin.SORT_METHOD_ARTIST,
                       xbmcplugin.SORT_METHOD_ALBUM,
                       xbmcplugin.SORT_METHOD_PLAYLIST_ORDER,
                       xbmcplugin.SORT_METHOD_TRACKNUM, ]
            [xbmcplugin.addSortMethod(handle=qobuz.boot.handle,
                                  sortMethod=method) for method in methods]
        return Dir.end_of_directory()

    def scan(self):
        import sys
        """Building tree when using Xbmc library scanning 
        feature
        """
        from gui.directory import Directory
        if not self.set_root_node():
            warn(self, "Cannot set root node ('%s')" % ( str(
                self.node_type)))
            return False
        handle = qobuz.boot.handle
        # print "Handle: %s" % (handle)
        Dir = Directory(self.root, self.nodes, withProgress=False)
        Dir.handle = int(sys.argv[1])
        Dir.asList = False
        Dir.asLocalURL = True
        ret = self.root.build_down(Dir, self.depth, 
                                       self.whiteFlag, self.blackFlag)
        Dir.set_content(self.root.content_type)
        Dir.end_of_directory()
        notifyH('Scanning results', str(Dir.total_put) +
                ' items where scanned', 3000)
        return True
