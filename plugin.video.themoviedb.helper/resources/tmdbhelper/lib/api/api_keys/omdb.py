from tmdbhelper.lib.addon.permissions import __access__
from tmdbhelper.lib.addon.plugin import get_setting

if __access__.has_access('internal') or __access__.has_access('omdb'):
    API_KEY = get_setting('omdb_apikey', 'str')
else:
    API_KEY = ''
