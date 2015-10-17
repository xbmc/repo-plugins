'''
    qobuz.renderer.irenderer
    ~~~~~~~~~~~~~~~~~~~~~~~~

    :part_of: xbmc-qobuz
    :copyright: (c) 2012 by Joachim Basmaison, Cyril Leclerc
    :license: GPLv3, see LICENSE for more details.
'''
from debug import log
from node import Flag
from node import getNode


class IRenderer(object):
    """Base class for our renderer
        Parameters:
        node_type: int, type of node (see node.NodeFlag)
        parameters: dictionary, parameters passed to our plugin
    """

    def __init__(self, node_type, parameters={}):
        self.node_type = node_type
        self.parameters = parameters
        self.root = None
        self.whiteFlag = Flag.ALL
        self.blackFlag = Flag.STOPBUILD
        self.depth = 1
        self.asList = False
        self.nodes = []
        self.enable_progress = True

    def set_root_node(self):
        """Import correct node object based on node_type parameter, setting
        self.root
        """
        if self.root:
            return self.root
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

    def run(self):
        raise NotImplemented()
