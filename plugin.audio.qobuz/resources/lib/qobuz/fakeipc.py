'''
    qobuz.fakeipc
    ~~~~~~~~~~~~~

    :part_of: xbmc-qobuz
    :copyright: (c) 2012 by Joachim Basmaison, Cyril Leclerc
    :license: GPLv3, see LICENSE for more details.
'''
import xbmcgui  # @UnresolvedImport
import threading
import json
from time import time

lock = threading.Lock()


class FakeIPC:

    def __init__(self, key="Qobuz.IPC.Data"):
        self.key = key

    def acquire(self, callback):
        global lock
        if not lock.acquire(60):
            return False
        try:
            return callback()
        finally:
            lock.release()
        return None

    def read(self):
        def cb():
            data = xbmcgui.Window(10000).getProperty(self.key)
            if data:
                return json.loads(data)
            return None
        return self.acquire(cb)

    def write(self, v):
        def cb():
            v['updatedOn'] = time()
            xbmcgui.Window(10000).setProperty(self.key, json.dumps(v))
        self.acquire(cb)

    def delete(self):
        def cb():

            xbmcgui.Window(10000).setProperty(self.key, '')
        self.acquire(cb)
