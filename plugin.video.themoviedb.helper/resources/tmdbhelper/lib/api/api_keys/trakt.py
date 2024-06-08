from tmdbhelper.lib.addon.permissions import __access__
from tmdbhelper.lib.api.api_keys.tokenhandler import TokenHandler

if __access__.has_access('internal'):
    CLIENT_ID = 'e6fde6173adf3c6af8fd1b0694b9b84d7c519cefc24482310e1de06c6abe5467'
    CLIENT_SECRET = '15119384341d9a61c751d8d515acbc0dd801001d4ebe85d3eef9885df80ee4d9'
    USER_TOKEN = TokenHandler('trakt_token', store_as='setting')

elif __access__.has_access('trakt'):
    CLIENT_ID = ''
    CLIENT_SECRET = ''
    USER_TOKEN = TokenHandler('trakt_token', store_as='setting')

else:
    CLIENT_ID = ''
    CLIENT_SECRET = ''
    USER_TOKEN = TokenHandler()
