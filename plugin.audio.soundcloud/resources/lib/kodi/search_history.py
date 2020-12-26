from time import time


class SearchHistory:

    filename = "search_history.json"

    def __init__(self, settings, vfs):
        self.settings = settings
        self.size = int(self.settings.get("search.history.size"))
        self.vfs = vfs

    def get(self):
        search = self.vfs.get_json_as_obj(self.filename)
        return {k: search[k] for k in list(search)[:self.size]}

    def add(self, query):
        search = self.vfs.get_json_as_obj(self.filename)
        search[str(int(time()))] = {"query": query}
        search = self._reduce(search)
        self.vfs.save_obj_to_json(self.filename, search)

    def _reduce(self, search):
        return {k: search[k] for k in sorted(list(search), reverse=True)[:self.size]}
