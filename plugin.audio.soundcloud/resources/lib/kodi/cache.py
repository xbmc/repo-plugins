import os
import time


class Cache:

    path = ""

    def __init__(self, settings, vfs):
        self.settings = settings
        self.vfs = vfs

    def get(self, filename, age=60):
        """
        Get a cached file.
        :param filename: str
        :type age: int Minutes
        """
        filepath = os.path.join(self.path, filename)
        file = self.vfs.read(filepath)

        if file:
            mtime = self.vfs.get_mtime(filepath)
            if (int(time.time()) - age * 60) > mtime:
                return None

        return file

    def add(self, filename, data):
        filepath = os.path.join(self.path, filename)
        return self.vfs.write(filepath, data)
