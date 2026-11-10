"""Live list directory, with small static fallbacks for service outages."""

from resources.lib.ebibliocat.validation import valid_id
from resources.lib.utils.urls import url_populars
from resources.lib.video.foldervideo import FolderVideo


def from_entries(entries, language="ca"):
    folders, seen = [], set()
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        collection = entry.get("list")
        if not isinstance(collection, dict):
            continue
        list_id = collection.get("id")
        if not valid_id(list_id) or str(list_id) in seen or not entry.get("count"):
            continue
        name = collection.get("name_" + language) or collection.get("name")
        if isinstance(name, str) and name:
            seen.add(str(list_id))
            folders.append(FolderVideo(name, "1", "collection:" + str(list_id)))
    return folders


def getList(strings):
    folders = []
    for key, url in url_populars.items():
        name = (
            strings.get(key)
            if key in ("popular", "noperdis")
            else url.rsplit("/", 1)[-1].replace("-", " ").capitalize()
        )
        list_id = url.split("/lists/", 1)[1].split("/", 1)[0]
        folders.append(FolderVideo(name, "1", "collection:" + list_id))
    return folders
