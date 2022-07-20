from time import time
from typing import TYPE_CHECKING, Dict

if TYPE_CHECKING:
    from resources.lib.kodi.vfs import VFS


class SearchHistory:

    filename: str = "search_history.json"

    def __init__(self, settings: Dict, vfs: VFS):
        self.settings = settings
        self.size: int = int(self.settings.get("search.history.size") or 10)
        self.vfs: VFS = vfs
        self.history: Dict = self.vfs.json(self.filename)

    def get(self) -> Dict:
        """
        Returns the history of searches size=10.
        :rtype: dict"""
        return {k: self.history[k] for k in list(self.history)[: self.size]}

    def add(self, query: str):
        for k, v in list(self.history.items()):
            if v["query"] == query:
                return None

        self.history[str(int(time()))] = {"query": query}
        self.history = self._reduce(self.history)
        self._save()

    def remove(self, query):
        self.history = {k: v for k, v in self.history.items() if v["query"] != query}
        self._save()

    def clear(self):
        return self.vfs.delete(self.filename)

    def _save(self):
        return self.vfs.to_json(self.filename, self.history)

    def _reduce(self, history):
        return {k: history[k] for k in sorted(list(history), reverse=True)[: self.size]}
