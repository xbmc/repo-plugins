class PermissionHandler:
    from xbmcaddon import Addon as _Addon

    _get_setting = staticmethod(_Addon().getSetting)

    # Any module name (relative to tmdbhelper.lib.) that matches an item in
    # _DENY is prevented from being imported outside of resources.lib
    _DENY = (
    )

    # Any module name (relative to tmdbhelper.lib.) that matches an item in
    # _ALLOW is allowed to be imported from outside of resources.lib
    # Overrides _DENY_ALL
    _ALLOW = (
        'api.tmdb.api',
    )

    # Any module name (relative to tmdbhelper.lib.) that starts with an item in
    # _DENY_ALL is prevented from being imported outside of resources.lib
    # Overrides _ALLOW_ALL
    _DENY_ALL = (
        'api.api_keys.',
    )

    # Any module name (relative to tmdbhelper.lib.) that starts with an item in
    # _ALLOW_ALL is allowed to be imported from outside of resources.lib
    _ALLOW_ALL = (
        'player.',
    )

    # Any module name (relative to tmdbhelper.lib.) that matches an item in
    # _RESTRICT requires specific user settings enabled to expose user data
    # when imported from outside of resources.lib
    _RESTRICT = (
    )

    # Any module name (relative to tmdbhelper.lib.) that starts with an item in
    # _RESTRICT_ALL requires specific user settings enabled to expose user data
    # when imported from outside of resources.lib
    _RESTRICT_ALL = (
        'api.',
    )

    _PERMISSION_LEVELS = {
        'deny': -1,
        'none': 0,
        'internal': 2 ** 0,
        'fanarttv': 2 ** 1,
        'mdblist': 2 ** 2,
        'omdb': 2 ** 3,
        'tmdb': 2 ** 4,
        'trakt': 2 ** 5,
        'tvdb': 2 ** 6,
    }

    _PERMISSION_TYPES = {
        'fanarttv': 'fanarttv_clientkey_access',
        'mdblist': 'mdblist_apikey_access',
        'omdb': 'omdb_apikey_access',
        'trakt': 'trakt_token_access',
        'tvdb': 'tvdb_token_access',
    }

    def __init__(self):
        self.access_levels = self._permissions('internal')

    @classmethod
    def _permissions(cls, *permissions):
        if not permissions or 'none' in permissions:
            return {cls._PERMISSION_LEVELS['none']}
        if 'deny' in permissions:
            return {cls._PERMISSION_LEVELS['deny']}
        if 'all' in permissions:
            return {*cls._PERMISSION_LEVELS.values()}
        return {cls._PERMISSION_LEVELS[p] for p in permissions
                if p in cls._PERMISSION_LEVELS}

    @classmethod
    def import_allowed(cls, relname):
        if relname in cls._DENY:
            return False
        if relname in cls._ALLOW:
            return True
        if any(allow.startswith(relname) for allow in cls._ALLOW):
            return True
        if f'{relname}.'.startswith(cls._DENY_ALL):
            return False
        if f'{relname}.'.startswith(cls._ALLOW_ALL):
            return True
        return False

    def has_access(self, *required):
        if self._PERMISSION_LEVELS['internal'] in self.access_levels:
            return True
        required = self._permissions(*required)
        if self._PERMISSION_LEVELS['deny'] in required:
            return False
        return not bool(required - self.access_levels)

    def set_spec_access(self, spec, basename, relname):
        if (relname in self._RESTRICT
                or f'{relname}.'.startswith(self._RESTRICT_ALL)):
            self.access_levels = self._permissions(
                access for access, name in self._PERMISSION_TYPES.items()
                if self._get_setting(name)
            )
        else:
            self.access_levels = self._permissions('internal')

        fullname = f'{basename}.{relname}'
        spec.name = fullname
        if spec.loader:
            spec.loader.name = fullname
        return spec


__access__ = PermissionHandler()
