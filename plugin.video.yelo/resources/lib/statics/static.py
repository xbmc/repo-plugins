from resources.lib.helpers import UAHelper

UA = UAHelper.get_UA()

default_headers = {
    'User-Agent': UA,
}

json_header = {
    'User-Agent': UA,
    'Accept': 'application/json, text/plain, */*',
    'Content-Type': 'application/json;charset=utf-8',
}

license_header_prepare = {
    "User-Agent": UA,
    "Accept-Encoding": "gzip, deflate, br",
    "Origin": "https://www.yeloplay.be",
    "Content-Type": "text/plain;charset=UTF-8"
}

form_headers = {
    'User-Agent': UA,
    'Content-Type': 'application/x-www-form-urlencoded'
}

json_request_device = {
    "meta": {"schema": "devicemanagement/Device.json", "version": "4.1"}, "deviceRegistration": {"deviceProperties": {
        "dict": [{"key": "DEVICE_OS", "value": "Web"}, {"key": "OS_NAME", "value": "Windows"},
                 {"key": "OS_VERSION", "value": "10"}, {"key": "BROWSER_NAME", "value": "Firefox"},
                 {"key": "BROWSER_VERSION", "value": "63.0"}, {"key": "SCREEN_RESOLUTION", "value": "1920x1080"},
                 {"key": "SCREEN_DENSITY", "value": "1"}, {"key": "DEVICE_TYPE", "value": "desktop"}]}}
}

json_prepare_message = {
    "OAuthPrepareParamsRequest":
        {
            "platform": "Web"
        }
}