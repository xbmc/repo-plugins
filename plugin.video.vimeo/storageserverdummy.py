'''
     StorageServer override.
     Version: 1.0
'''


class StorageServer():
    def __init__(self, table=False):
        return None

    def cacheFunction(self, funct=False, *args):
        return funct(*args)

    def set(self, name, data):
        return ""

    def get(self, name):
        return ""

    def setMulti(self, name, data):
        return ""

    def getMulti(self, name, items):
        return ""

    def lock(self, name):
        return False

    def unlock(self, name):
        return False
