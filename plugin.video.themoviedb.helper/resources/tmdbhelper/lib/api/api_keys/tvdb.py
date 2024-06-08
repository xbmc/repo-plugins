from tmdbhelper.lib.addon.permissions import __access__
from tmdbhelper.lib.api.api_keys.tokenhandler import TokenHandler
from jurialmunkey.parser import load_in_data

if __access__.has_access('internal'):
    API_KEY = load_in_data(
        b"#SFK\x03JI\x06N\x11\x04GY\x03\x14'\x0c_Y\x19\x0f]\x0c]\x00\x13\x01^JP\x11g(|\x03*",
        b'Be respectful. Dont jeopardise TMDbHelper access to this data by stealing API keys or changing item limits.'
    ).decode()
    USER_TOKEN = TokenHandler('tvdb_token', store_as='property')

elif __access__.has_access('tvdb'):
    API_KEY = ''
    USER_TOKEN = TokenHandler('tvdb_token', store_as='property')

else:
    API_KEY = ''
    USER_TOKEN = TokenHandler()
