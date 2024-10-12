"""Cache utils."""

import json
import os
from typing import Any, Callable

import xbmc
import xbmcvfs

from lib.utils.kodi import get_addon_info, log


def use_cache(filepath: str) -> Callable[[Callable], Callable]:
    """Use cached data when Exception is raised or update cache on success."""
    cache_folder = os.path.join(xbmcvfs.translatePath(get_addon_info("profile")), "cache")

    if not os.path.exists(cache_folder):
        os.makedirs(cache_folder)

    def decorator(func: Callable[[Any], Any]):
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            result = {}

            try:
                result = func(*args, **kwargs)
                with open(os.path.join(cache_folder, filepath), "wb") as file:
                    file.write(json.dumps(result).encode("utf-8"))
            except Exception:
                log("Can't load data: using cache instead", xbmc.LOGWARNING)
                with open(os.path.join(cache_folder, filepath), encoding="utf-8") as file:
                    result = json.loads("".join(file.readlines()))

            return result

        return wrapper

    return decorator
