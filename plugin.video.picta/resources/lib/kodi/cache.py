import time

from typing import TYPE_CHECKING, Dict

if TYPE_CHECKING:
    from resources.lib.kodi.vfs import VFS


class Cache:
    def __init__(self, settings: Dict, vfs: VFS):
        self.settings = settings
        self.vfs = vfs

    def get(self, filename: str, age: int = 60) -> str:
        """
        Get a cached file.
        :param filename: str
        :type age: int Minutes
        :rtype: str
        """
        data = self.vfs.read(filename)

        if data:
            mtime = self.vfs.get_mtime(filename)
            return "" if (int(time.time()) - age * 60) > mtime else data

        return ""

    def add(self, filename: str, content: str):
        return self.vfs.write(filename, content)
