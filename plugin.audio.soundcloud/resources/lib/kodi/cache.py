import time


class Cache:
    def __init__(self, settings, vfs):
        self.settings = settings
        self.vfs = vfs

    def get(self, filename, age=60):
        """
        Get a cached file.
        :param filename: str
        :type age: int Minutes
        """
        file = self.vfs.read(filename)

        if file:
            mtime = self.vfs.get_mtime(filename)
            if (int(time.time()) - age * 60) > mtime:
                return None

        return file

    def add(self, filename, data):
        return self.vfs.write(filename, data)
