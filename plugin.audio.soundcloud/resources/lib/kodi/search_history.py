from time import time


class SearchHistory:

    filename = "search_history.json"

    def __init__(self, settings, vfs):
        self.settings = settings
        self.size = int(self.settings.get("search.history.size"))
        self.vfs = vfs
        self.history = self.vfs.get_json_as_obj(self.filename)

    def get(self):
        return {k: self.history[k] for k in list(self.history)[:self.size]}

    def add(self, query):
        for k, v in self.history.items():
            if v["query"] == query:
                return

        self.history[str(int(time()))] = {"query": query}
        self.history = self._reduce(self.history)
        self._save()

    def remove(self, query):
        self.history = {k: v for k, v in list(self.history.items()) if v["query"] != query}
        self._save()

    def clear(self):
        return self.vfs.delete(self.filename)

    def _save(self):
        return self.vfs.save_obj_to_json(self.filename, self.history)

    def _reduce(self, search):
        return {k: search[k] for k in sorted(list(search), reverse=True)[:self.size]}
