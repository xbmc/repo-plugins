from tmdbhelper.lib.addon.permissions import __access__
from tmdbhelper.lib.addon.plugin import get_setting

if __access__.has_access('internal'):
    API_KEY = 'fcca59bee130b70db37ee43e63f8d6c1'
    CLIENT_KEY = get_setting('fanarttv_clientkey', 'str')

elif __access__.has_access('fanarttv'):
    API_KEY = ''
    CLIENT_KEY = get_setting('fanarttv_clientkey', 'str')

else:
    API_KEY = ''
    CLIENT_KEY = ''

