"""Helpers for Kodi GUI."""

from xbmcgui import ListItem


def create_directory_items(data: list) -> list:
    """Create a list of directory items from data."""
    items = []

    for d in data:
        list_item = ListItem(label=d["label"], path=d["path"])

        # list_item.setLabel2("LABEL2")
        # list_item.setInfo("INFO", {"INFO1": "INFO1", "INFO2": "INFO2"})

        if "art" in d and "thumb" in d["art"]:
            list_item.setArt({"thumb": d["art"]["thumb"]})

        items.append((d["path"], list_item, bool(d["is_folder"])))

    return items


def create_video_item(stream_info: dict) -> ListItem:
    """Create a video item from stream data."""
    list_item = ListItem(path=stream_info["path"])
    list_item.setMimeType(stream_info["mime_type"])
    list_item.setContentLookup(False)
    list_item.setProperty("inputstream", "inputstream.adaptive")
    list_item.setProperty("inputstream.adaptive.play_timeshift_buffer", "true")
    list_item.setProperty("inputstream.adaptive.manifest_config", '{"timeshift_bufferlimit":14400}')
    list_item.setProperty("inputstream.adaptive.license_type", stream_info["license_type"])
    list_item.setProperty("inputstream.adaptive.license_key", stream_info["license_key"])

    return list_item
