'''
     StorageServer override.
     Version: 1.0
'''
import xbmc
try:
    import hashlib
except:
    import md5

import xbmcvfs
import os
import time
import sys

if hasattr(sys.modules["__main__"], "settings"):
    settings = sys.modules["__main__"].settings
else:
    settings = False


class StorageServer:
    def __init__(self, table=False):
        self.table = table
        if settings:
            temporary_path = xbmc.translatePath(settings.getAddonInfo("profile"))
            if not xbmcvfs.exists(temporary_path):
                os.makedirs(temporary_path)

        return None

    def cacheFunction(self, funct=False, *args):
        result = ""
        if not settings:
            return funct(*args)
        elif funct and self.table:
            name = repr(funct)
            if name.find(" of ") > -1:
                name = name[name.find("method") + 7:name.find(" of ")]
            elif name.find(" at ") > -1:
                name = name[name.find("function") + 9:name.find(" at ")]

            # Build unique name
            if "hashlib" in globals():
                keyhash = hashlib.md5()
            else:
                keyhash = md5.new()

            for params in args:
                if isinstance(params, dict):
                    for key in sorted(params.iterkeys()):
                        if key not in ["new_results_function"]:
                            keyhash.update("'%s'='%s'" % (key, params[key]))
                elif isinstance(params, list):
                    keyhash.update(",".join(["%s" % el for el in params]))
                else:
                    try:
                        keyhash.update(params)
                    except:
                        keyhash.update(str(params))

            name += "-" + keyhash.hexdigest() + ".cache"

            path = os.path.join(xbmc.translatePath(settings.getAddonInfo("profile")).decode("utf-8"), name)
            if xbmcvfs.exists(path) and os.path.getmtime(path) > time.time() - 3600:
                print "Getting cache : " + repr(path)
                temp = open(path)
                result = eval(temp.read())
                temp.close()
            else:
                print "Setting cache: " + repr(path)
                result = funct(*args)
                if len(result) > 0:
                    temp = open(path, "w")
                    temp.write(repr(result))
                    temp.close()

        return result

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
