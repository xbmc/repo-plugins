'''
    qobuz.node
    ~~~~~~~~~~
    
    :copyright: (c) 2012 by Joachim Basmaison, Cyril Leclerc
    :license: GPLv3, see LICENSE for more details.
'''

__all__ = ['getNode', 'flag']

from node.flag import Flag
from debug import log

def getNode(qnt, params = {}, **ka):
        ''' Caching import ??? '''
        nodeName = Flag.to_s(qnt)
        modulePath = nodeName
        moduleName = 'Node_' + nodeName
        Module = module_import(modulePath, moduleName)
#        mixinPath = 'qobuzxbmc.node.%s_mixin' % nodeName
#        mixinName = 'Node_' + nodeName + '_mixin'
#        Final = Module
#        try:
#            Mixin = module_import(mixinPath, mixinName)
#            Final = mixin_factory(moduleName, Module, Mixin)
#        except Exception as e:
#            print repr(e)
#            pass
        """ 
            Initializing our new node 
            - no parent 
            - parameters 
            """
        parent = None
        if 'parent' in ka:
            parent = ka['parent']
        node = Module(parent, params)
        return node

def mixin_factory(name, base, mixin):
    return type(name, (base, mixin), {})

def module_import(path, name, **ka):
        """ from node.foo import Node_foo """
        modPackage = __import__(path, globals(), 
                                locals(), [name], -1)
        """ Getting Module from Package """
        Module = getattr(modPackage, name)
        return Module

class ErrorNoData(Exception):
    pass