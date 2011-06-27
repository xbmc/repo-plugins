'''
Created on 19 jun 2011

@author: Nick
'''
class BaseWindow:
    
    def __init__(self, addonHandle, addonPath):
        self._addonHandle = addonHandle
        self._addonPath = addonPath
