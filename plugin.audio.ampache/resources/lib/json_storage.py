from builtins import object
from future.utils import PY2
import json
import os
import xbmc
import xbmcaddon
import xbmcvfs
from copy import deepcopy

#main plugin library

class JsonStorage(object):

    def __init__(self,filename):
        ampache = xbmcaddon.Addon("plugin.audio.ampache")
        if PY2:
            base_dir = xbmc.translatePath( ampache.getAddonInfo('profile'))
            base_dir = base_dir.decode('utf-8')
        else:
            base_dir = xbmcvfs.translatePath( ampache.getAddonInfo('profile'))
        self._filename = os.path.join(base_dir, filename)
        self._data = dict()
        self.load()

    def load(self):
        if xbmcvfs.exists(self._filename):
            with open(self._filename, 'r') as fd:
                self._data = json.load(fd)

    def save(self,data):
        if data != self._data:
            self._data = deepcopy(data)
            with open(self._filename, 'w') as fd:
                json.dump(self._data, fd, indent=4, sort_keys=True)

    def getData(self):
        return deepcopy(self._data)
