"""
Lightweight native Plugin mainly for routing/navigation.
This provides:
- Plugin.route(path, name=...) decorator to register handlers
- Plugin.run() to dispatch based on sys.argv
- Plugin.url_for(route_name, **kwargs) to build plugin URLs
- Plugin.get_storage
- Plugin.notify
"""

import json
import os
import inspect
import re
import sys
import time
import urllib.parse

import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin
import xbmcvfs


class RoutingMixin:
    """Routing and playback helpers for native Kodi plugin URLs."""

    def __init__(self, *args, **kwargs):
        current_url = urllib.parse.urlparse(sys.argv[0])
        if current_url.scheme and current_url.netloc:
            self.base_url = f"{current_url.scheme}://{current_url.netloc}"
        else:
            self.base_url = sys.argv[0]
        try:
            self.handle = int(sys.argv[1])
        # pylint: disable=broad-exception-caught
        except Exception:
            self.handle = None
        self._routes = {}
        self._url_paths = {}
        super().__init__(*args, **kwargs)

    def route(self, path, name=None):
        """Decorator to register route handlers."""
        def decorator(func):
            route_name = name or func.__name__
            self._routes[route_name] = func
            self._url_paths[route_name] = path
            return func

        return decorator

    def url_for(self, route_name, **kwargs):
        """Build a plugin URL for a registered route."""
        route_path = self._url_paths.get(route_name, '')
        path_params = set(re.findall(r'<([^>]+)>', route_path))
        for key in path_params:
            if key in kwargs:
                route_path = route_path.replace(
                    f'<{key}>', urllib.parse.quote(str(kwargs[key]), safe=''))
        params = {'route': route_name}
        for key, value in kwargs.items():
            params[key] = value
        return self.base_url + route_path + '?' \
            + urllib.parse.urlencode(params)

    def _route_from_path(self, path):
        """Return the route name and parameters encoded in a plugin path."""
        for route_name, route_path in self._url_paths.items():
            path_parts = route_path.strip('/').split('/')
            actual_parts = path.strip('/').split('/')
            if len(path_parts) != len(actual_parts):
                continue
            params = {}
            matches = True
            for expected, actual in zip(path_parts, actual_parts):
                if expected.startswith('<') and expected.endswith('>'):
                    params[expected[1:-1]] = urllib.parse.unquote(actual)
                elif expected != actual:
                    matches = False
                    break
            if matches:
                return route_name, params
        return None, {}

    def run(self):
        """Dispatch to a registered route based on the 'route' query parameter."""
        self.handle = int(sys.argv[1]) if len(sys.argv) > 1 else None
        params = {}
        route = ''
        # route is in sys.argv[2] when opening the plugin
        if len(sys.argv) > 2 and sys.argv[2]:
            raw_route = sys.argv[2][1:]  # Remove leading '?'
            params = urllib.parse.parse_qs(raw_route)
            params = {
                key: value[0] if isinstance(value, list) and len(value) > 0
                else value for key, value in params.items()
            }
            route = params.pop('route', None)
        # Route and parameters can also be encoded in the plugin path.
        elif sys.argv[0]:
            route, params = self._route_from_path(urllib.parse.urlparse(sys.argv[0]).path)

        if route == '/' or route is None:
            route = 'index'

        handler = self._routes.get(route)
        if handler is None:
            xbmc.log(f"No handler for route '{route}'", xbmc.LOGERROR)
            return

        accepted_params = inspect.signature(handler).parameters
        result = handler(**{
            key: value for key, value in params.items() if key in accepted_params
        })

        if self.handle is not None:
            self._post_process_result(result)

    def _post_process_result(self, result):
        """Post-process a route result for the active Kodi handle.

        Lists populate a directory, ListItems resolve playback, True signals
        a successfully handled non-directory action, and None signals an
        unsuccessful or incomplete route.
        """
        handle = self.handle
        if handle is None:
            return
        if isinstance(result, list):
            for item in result:
                path = item.getPath()
                is_playable = item.getProperty('is_playable') == 'True'
                xbmcplugin.addDirectoryItem(
                    handle=handle, url=path, listitem=item, isFolder=not is_playable)
            xbmcplugin.endOfDirectory(handle)
        elif isinstance(result, xbmcgui.ListItem):
            xbmcplugin.setResolvedUrl(handle, True, result)
        elif result is True:
            xbmcplugin.endOfDirectory(
                handle, succeeded=True, updateListing=False)
        elif result is None or result is False:
            xbmcplugin.endOfDirectory(
                handle, succeeded=False, updateListing=False)


# pylint: disable=too-few-public-methods
class StorageMixin:
    """Addon profile storage and settings helpers."""

    def __init__(self, *args, **kwargs):
        try:
            self.storage_path = xbmcvfs.translatePath(self.addon.getAddonInfo('profile'))
        # pylint: disable=broad-exception-caught
        except Exception:
            self.storage_path = xbmcvfs.translatePath('special://home/')
        self._storage = {}
        super().__init__(*args, **kwargs)

    def _ensure_storage_dir(self):
        storage_dir = os.path.join(self.storage_path, 'storage')
        try:
            if not xbmcvfs.exists(storage_dir):
                xbmcvfs.mkdir(storage_dir)
        # pylint: disable=broad-exception-caught
        except Exception:
            os.makedirs(storage_dir, exist_ok=True)
        return storage_dir

    def _storage_file_path(self, key):
        return os.path.join(self._ensure_storage_dir(), f"{key}.json")

    def get_storage(self, key, ttl=None):
        """File-backed storage with TTL support (TTL in minutes)."""
        if key in self._storage:
            storage = self._storage[key]
            created = storage.created
            if ttl is None or created is None \
                    or int(time.time()) - created <= int(ttl) * 60:
                return storage
            storage = storage.__class__(storage.path, {}, None)
            self._storage[key] = storage
            return storage

        file_path = self._storage_file_path(key)

        class FileStorageDict(dict):
            """Dictionary that automatically saves to a JSON file on changes."""
            def __init__(self, path, initial, created):
                super().__init__(initial or {})
                self.path = path
                self.created = created

            def _save(self):
                self.created = int(time.time())
                payload = {'created': self.created, 'value': dict(self)}
                with xbmcvfs.File(self.path, 'w') as handle:
                    handle.write(json.dumps(payload))

            def __setitem__(self, key_name, value):
                super().__setitem__(key_name, value)
                self._save()

            def __delitem__(self, key_name):
                super().__delitem__(key_name)
                self._save()

            def clear(self):
                super().clear()
                self._save()

            def update(self, *args, **kwargs):
                super().update(*args, **kwargs)
                self._save()

            def pop(self, *args, **kwargs):
                value = super().pop(*args, **kwargs)
                self._save()
                return value

        storage = FileStorageDict(file_path, {}, None)
        if xbmcvfs.exists(file_path):
            with xbmcvfs.File(file_path, 'r') as handle:
                content = handle.read()
            if content:
                data = json.loads(content)
                created = int(data.get('created', 0))
                value = data.get('value', {})
                if ttl is not None and int(time.time()) - created > int(ttl) * 60:
                    value = {}
                storage = FileStorageDict(file_path, value, created)

        # try:
        #     storage._save()
        # except Exception:
        #     pass
        self._storage[key] = storage
        return storage


class Plugin(RoutingMixin, StorageMixin):
    """
    Plugin implementing:
    - Routing
    - File-based storage interface
    - Notification
    """

    def __init__(self):
        self.addon = xbmcaddon.Addon()
        super().__init__()

    def notify(self, msg, image=None, mtime=5000):
        """Show a notification message in Kodi."""
        xbmcgui.Dialog().notification(self.addon.getAddonInfo('name'), msg, image, mtime)


# convenience single instance for modules that expect Plugin in the module scope
_default_plugin = Plugin()
