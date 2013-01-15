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
from debug import log
from node.flag import NodeFlag as Flag
from util import getNode

class IRenderer(object):
    """Base class for our renderer
        Parameters:
        node_type: int, type of node (see node.NodeFlag)
        parameters: dictionary, parameters passed to our plugin
    """
    def __init__(self, node_type, parameters=None):
        self.node_type = node_type
        self.parameters = parameters
        self.root = None
        self.whiteFlag = Flag.ALL
        self.blackFlag = Flag.STOPBUILD
        self.depth = 1
        self.asList = False
        self.nodes = []
        self.enable_progress = True

    def to_s(self):
        import pprint
        """Return this object as a string
        """
        return pprint.pformat(self)

    def set_root_node(self):
        """Import correct node object based on node_type parameter, setting
        self.root
        """
        if self.root: return self.root
        self.root = getNode(self.node_type, self.parameters)
        return self.root

    def has_method_parameter(self):
        """Return true if our plugin has been called with a node method
        parameter (nm=foo)
        """
        if 'nm' in self.parameters:
            return True
        return False

    def execute_method_parameter(self):
        """Excute node method (nm=foo) if present and delete nm key
        from parameter
        """
        if 'nm' in self.parameters:
            methodName = self.parameters['nm']
            del self.parameters['nm']
            log(self, "Executing method on node: " + repr(methodName))
            if getattr(self.root, methodName)():
                return True
            return False
