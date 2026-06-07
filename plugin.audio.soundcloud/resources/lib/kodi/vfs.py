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
            with xbmcvfs.File(filepath) as file:
                return file.read()
        else:
            return None

    def write(self, filename, string):
        filepath = os.path.join(self.path, filename)
        with xbmcvfs.File(filepath, "w") as file:
            return filepath if file.write(string) else False

    def delete(self, filename):
        filepath = os.path.join(self.path, filename)
        return xbmcvfs.delete(filepath)

    def remove_dir(self, path):
        dir_list, file_list = xbmcvfs.listdir(path)

        for file in file_list:
            xbmcvfs.delete(os.path.join(path, file))

        for directory in dir_list:
            self.remove_dir(os.path.join(path, directory))

        xbmcvfs.rmdir(path)

    def destroy(self):
        """
        Deletes the VFS folder and all files in it.
        """
        self.remove_dir(self.path)

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
