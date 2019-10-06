import json
from resources.lib.statics.static import UA

def authorization_header_json(device_Id, accessToken):
    return {
        'User-Agent': UA,
        'Accept': 'application/json, text/plain, */*',
        'Content-Type': 'application/json;charset=utf-8',
        'X-Yelo-DeviceId': device_Id,
        "Authorization": "Bearer {}".format(accessToken)
    }


def customer_features_header(code, device_Id, accessToken):
    return {
        'User-Agent': UA,
        'Referer': 'https://www.yeloplay.be/openid/callback?code={}'.format(code),
        'Content-Type': 'application/json;charset=utf-8',
        "Authorization": "Bearer {}".format(accessToken),
        'X-Yelo-DeviceId': device_Id,
    }


def json_request_header(device_id, channel, protocol):
    return {
        "meta": {"schema": "stream/Stream.json", "version": "4.1"},
        "stream": {
            "deviceId": device_id,
            "resource": {"watchMode": "Live", "links": {"tvChannel": channel}, "timeShiftOffset": 0},
            "context": "Watch-TV", "platform": "Web", "drmMethod": "WIDEVINE", "protocol": protocol
        }
    }


def json_verify_header(device_Id, web_generated_id):
    return {
        "meta": {"schema": "devicemanagement/Device.json", "version": "4.1"}, "deviceRegistration": {
            "deviceProperties": {"dict": [{"key": "DEVICE_OS", "value": "Web"}, {"key": "OS_NAME", "value": "Windows"},
                                          {"key": "OS_VERSION", "value": "10"},
                                          {"key": "BROWSER_NAME", "value": "Firefox"},
                                          {"key": "BROWSER_VERSION", "value": "63.0"},
                                          {"key": "SCREEN_RESOLUTION", "value": "1920x1080"},
                                          {"key": "SCREEN_DENSITY", "value": "1"},
                                          {"key": "DEVICE_TYPE", "value": "desktop"},
                                          {"key": "WEB_GENERATED_ID",
                                           "value": web_generated_id}]},
            "id": device_Id}
    }


def json__token_header(code, callback):
    return {
        "OAuthTokenParamsRequest":
            {
                "authToken": code,
                "redirectUrl": callback
            }
    }


def token_header(device_Id, code):
    return {
        'User-Agent': UA,
        'Referer': 'https://www.yeloplay.be/openid/callback?code={}'.format(code),
        'Content-Type': 'application/json;charset=utf-8',
        'X-Yelo-DeviceId': device_Id,
    }


def verify_header(device_Id, code):
    return {
        'User-Agent': UA,
        'Referer': 'https://www.yeloplay.be/openid/callback?code={}'.format(code),
        'Content-Type': 'application/json;charset=utf-8',
        'X-Yelo-DeviceId': device_Id,
    }


def create_login_payload(username, password):


    return {
        'j_username': '{}'.format(username),
        'j_password': '{}'.format(password),
        'rememberme': 'true'
    }

def widevine_payload_package(device_Id, customer_Id):
    x = {
        "LatensRegistration": {
            "CustomerName": "{}".format(customer_Id),
            "AccountName": "PlayReadyAccount",
            "PortalId": "{}".format(device_Id),
            "FriendlyName": "THEOPlayer",
            "DeviceInfo": {
                "FormatVersion": "1",
                "DeviceType": "PC",
                "OSType": "Win32",
                "DRMProvider": "Google",
                "DRMVersion": "1.4.8.86",
                "DRMType": "Widevine",
                "DeviceVendor": "Google Inc.",
                "DeviceModel": ""
            }
        },
        "Payload": "b{SSM}"
    }

    return json.dumps(x)
