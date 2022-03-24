# Base URL for Authentication Server (without trailing slash)
base_url = 'http://localhost:8080'

# Device code endpoint
device_code_url = base_url + '/device/code'

# token endpoint
token_url = base_url + '/token'

# refresh endpoint
refresh_url = base_url + '/refresh'

# Endpoint to get user email (https://accounts.google.com/.well-known/openid-configuration)
email_url = 'https://openidconnect.googleapis.com/v1/userinfo'

# Google Photos API
service_endpoint = 'https://photoslibrary.googleapis.com/v1'
# TODO: Remove this
# token_folder = 'accounts/'
token_filename = 'token.json'
media_filename = 'media_db'
