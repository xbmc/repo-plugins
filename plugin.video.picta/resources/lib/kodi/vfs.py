import json
import os
from typing import Dict, List, Tuple

import xbmcvfs


class VFS:
    def __init__(self, path: str):
        self.path = path
        if not xbmcvfs.exists(self.path):
            xbmcvfs.mkdir(self.path)

    def read(self, filename: str) -> str:
        filepath = os.path.join(self.path, filename)
        if xbmcvfs.exists(filepath):
            with xbmcvfs.File(filepath) as file:
                return file.read()
        return ""

    def write(self, filename: str, content: str) -> Tuple[str, bool]:
        filepath: str = os.path.join(self.path, filename)
        with xbmcvfs.File(filepath, "w") as file:
            return (filepath, True) if file.write(content) else ("", False)

    def delete(self, filename: str):
        filepath: str = os.path.join(self.path, filename)
        return xbmcvfs.delete(filepath)

    def remove_dir(self, path: str) -> bool:
        """
        Remove a directory and all its contents recursively."
        :param path: str
        :rtype: bool
        """
        dir_list: List[str] = []
        file_list: List[str] = []

        dir_list, file_list = xbmcvfs.listdir(path)

        try:
            for file in file_list:
                xbmcvfs.delete(os.path.join(path, file))

            for directory in dir_list:
                self.remove_dir(os.path.join(path, directory))
        except OSError as e:
            return False

        xbmcvfs.rmdir(path)
        return True

    def destroy(self):
        """
        Deletes the VFS folder and all files in it.
        """
        self.remove_dir(self.path)

    def get_mtime(self, filename: str) -> int:
        """
        Returns the modification time of a file.
        :param filename: str
        :rtype: int Timestamp
        """
        filepath = os.path.join(self.path, filename)
        stat = xbmcvfs.Stat(filepath)
        return stat.st_mtime()

    def json(self, filename: str, default=None) -> Dict:
        """
        Loads a JSON file and returns the contents as a dictionary.
        :param filename: str
        :param default: dict
        :rtype: dict
        """
        if default is None:
            default = {}
        content = self.read(filename)
        return json.loads(content) if content else default

    def to_json(self, filename: str, obj) -> str:
        """
        Serializes an object to JSON and writes it to a file.
        :param filename: str
        :param obj: object
        :rtype: str
        """
        content = json.dumps(obj)
        return self.write(filename, content)[0]
