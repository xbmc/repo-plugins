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
            return None if (int(time.time()) - age * 60) > mtime else file

        return None

    def add(self, filename, data):
        return self.vfs.write(filename, data)
