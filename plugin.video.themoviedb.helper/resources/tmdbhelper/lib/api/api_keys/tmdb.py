from tmdbhelper.lib.addon.permissions import __access__

if __access__.has_access('internal'):
    API_KEY = 'a07324c669cac4d96789197134ce272b'
else:
    API_KEY = ''
