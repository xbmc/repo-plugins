import json
import os
import xbmcvfs


class VFS:
    def __init__(self, path):
        self.path = path
        if not xbmcvfs.exists(self.path):
            xbmcvfs.mkdir(self.path)

    def read(self, filename):
        filepath = os.path.join(self.path, filename)
        if xbmcvfs.exists(filepath):
            file = xbmcvfs.File(filepath)
            string = file.read()
            file.close()
            return string
        else:
            return None

    def write(self, filename, string):
        filepath = os.path.join(self.path, filename)
        file = xbmcvfs.File(filepath, "w")
        success = file.write(string)
        file.close()
        return success

    def get_mtime(self, filename):
        """
        Returns last modification time.
        :rtype: int Timestamp
        """
        filepath = os.path.join(self.path, filename)
        stat = xbmcvfs.Stat(filepath)
        return stat.st_mtime()

    def get_json_as_obj(self, filename, default=None):
        string = self.read(filename)
        if string:
            return json.loads(string)
        else:
            return default if default else {}

    def save_obj_to_json(self, filename, obj):
        string = json.dumps(obj)
        return self.write(filename, string)
