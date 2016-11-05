import urlparse
import urllib
import uuid
import hashlib
import hmac
import base64
import urllib2
import time
import json
import gzip
import os
import cookielib
from StringIO import StringIO

import xbmc
from globals import ADDON_PATH_PROFILE

SETTINGS_FILE = 'adobe.json'
UA_ATV = 'AppleCoreMedia/1.0.0.13Y234 (Apple TV; U; CPU OS 9_2 like Mac OS X; en_us)'
TAG = 'ESPN3-adobe-api: '


# Fixes an issue with 32bit systems not supporting times after 2038
def save_cookies(cj):
    for cookie in cj:
        if cookie.expires > 2000000000:
            cookie.expires = 2000000000
    cj.save(os.path.join(ADDON_PATH_PROFILE, 'adobe-cookies.lwp'), ignore_discard=True, ignore_expires=True)


def get_cookie_jar():
    cj = cookielib.LWPCookieJar()
    if not os.path.isfile(os.path.join(ADDON_PATH_PROFILE, 'adobe-cookies.lwp')):
        save_cookies(cj)
    else:
        cj.load(os.path.join(ADDON_PATH_PROFILE, 'adobe-cookies.lwp'), ignore_discard=True)
    return cj


def reset_settings():
    save_settings(dict())


def save_settings(settings):
    settings_file = os.path.join(ADDON_PATH_PROFILE, SETTINGS_FILE)
    with open(settings_file, 'w') as fp:
        json.dump(settings, fp, sort_keys=False, indent=4)


def load_settings():
    settings_file = os.path.join(ADDON_PATH_PROFILE, SETTINGS_FILE)
    if not os.path.isfile(settings_file):
        save_settings(dict())
    with open(settings_file, 'r') as fp:
        return json.load(fp)


def get_device_id():
    settings = load_settings()
    if 'device_id' not in settings:
        settings['device_id'] = str(uuid.uuid1())
        save_settings(settings)
    return settings['device_id']


def read_response(resp):
    if resp.info().get('Content-Encoding') == 'gzip':
        buf = StringIO(resp.read())
        f = gzip.GzipFile(fileobj=buf)
        content = f.read()
    else:
        content = resp.read()
    return json.loads(content)


def is_expired(expiration):
    return (time.time() * 1000) >= int(expiration)


def get_url_response(url, message, body = None, method = None):
    # xbmc.log(TAG + 'url %s message %s' % (url, message), xbmc.LOGDEBUG)
    cj = get_cookie_jar()
    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
    opener.addheaders = [ ("Accept", "application/json"),
                            ("Accept-Encoding", "gzip, deflate"),
                            ("Accept-Language", "en-us"),
                            ("Content-Type", "application/x-www-form-urlencoded; charset=UTF-8"),
                            ("Connection", "close"),
                            ("User-Agent", UA_ATV),
                            ("Authorization", message)]
    if method == 'DELETE':
        request = urllib2.Request(url)
        request.get_method = lambda: method
        resp = opener.open(request)
    else:
        resp = opener.open(url, body)
        resp = read_response(resp)
    save_cookies(cj)
    return resp


def generate_message(method, path):
    nonce = str(uuid.uuid4())
    today = str(int(time.time() * 1000))
    key = 'gB8HYdEPyezeYbR1'
    message = method + ' requestor_id=ESPN, nonce=' + nonce + ', signature_method=HMAC-SHA1, request_time=' + today + ', request_uri=' + path
    signature = hmac.new(key, message, hashlib.sha1)
    signature = base64.b64encode(signature.digest())
    message = message + ', public_key=yKpsHYd8TOITdTMJHmkJOVmgbb2DykNK, signature=' + signature
    return message


def is_reg_code_valid():
    settings = load_settings()
    if 'generateRegCode' not in settings:
        xbmc.log(TAG + 'Unable to find reg code', xbmc.LOGDEBUG)
        return False
    # Check code isn't expired
    expiration = settings['generateRegCode']['expires']
    if is_expired(expiration):
        xbmc.log(TAG + 'Reg code is expired at %s' % expiration, xbmc.LOGDEBUG)
        return False
    return True


# Gets called when the user wants to authorize this device, it returns a registration code to enter
# on the activation website page
# Sample : '{"id":"","code":"","requestor":"ESPN","generated":1463616806831,
# "expires":1463618606831,"info":{"deviceId":"","deviceType":"appletv","deviceUser":null,
# "appId":null,"appVersion":null,"registrationURL":null}}'
# (generateRegCode)
def get_regcode():
    if is_reg_code_valid():
        xbmc.log(TAG + 'Loading reg code from cache', xbmc.LOGDEBUG)
        return load_settings()['generateRegCode']['code']

    params = urllib.urlencode(
        {'deviceId': get_device_id(),
         'deviceType': 'appletv',
         'ttl': '1800'})

    path = '/regcode'
    url = urlparse.urlunsplit(['https', 'api.auth.adobe.com',
                               'reggie/v1/ESPN' + path,
                               params, ''])

    message = generate_message('POST', path)

    resp = get_url_response(url, message, dict())

    settings = load_settings()
    settings['generateRegCode'] = resp
    save_settings(settings)
    return resp['code']


# Authenticates the user after they have been authenticated on the activation website (authenticateRegCode)
# Sample: '{"mvpd":"","requestor":"ESPN","userId":"","expires":"1466208969000"}'
def authenticate():
    if not is_reg_code_valid():
        xbmc.log(TAG + 'reg code is invalid', xbmc.LOGDEBUG)
        raise ValueError('Registration code is invalid, please restart the authentication process')

    reg_code = get_regcode()

    params = urllib.urlencode({'requestor': 'ESPN'})

    path = '/authenticate/' + reg_code
    url = urlparse.urlunsplit(['https', 'api.auth.adobe.com',
                                   'api/v1' + path,
                                   params, ''])

    message = generate_message('GET', path)

    resp = get_url_response(url, message)
    settings = load_settings()
    settings['authenticateRegCode'] = resp
    save_settings(settings)


# Get authn token (re-auth device after it expires), getAuthnToken
def re_authenticate():
    params = urllib.urlencode({'requestor': 'ESPN',
                               'deviceId': get_device_id()})

    path = '/tokens/authn'
    url = urlparse.urlunsplit(['https', 'api.auth.adobe.com',
                                   'api/v1' + path,
                                   params, ''])

    message = generate_message('GET', path)

    resp = get_url_response(url, message)
    settings = load_settings()
    settings['authenticateRegCode'] = resp
    if 'authorize' in settings:
        del settings['authorize']
    save_settings(settings)


def get_resource(channel, event_name, event_guid, event_parental_rating):
    return '<rss version="2.0" xmlns:media="http://search.yahoo.com/mrss/"><channel><title><![CDATA[' + channel + "]]></title><item><title><![CDATA[" + event_name + "]]></title><guid><![CDATA[" + event_guid + ']]></guid><media:rating scheme="urn:v-chip"><![CDATA[' + event_parental_rating + "]]></media:rating></item></channel></rss>"


# Sample '{"resource":"resource","mvpd":"","requestor":"ESPN","expires":"1463621239000"}'
def authorize(resource):
    if is_authorized(resource):
        xbmc.log(TAG + 'already authorized', xbmc.LOGDEBUG)
        return
    params = urllib.urlencode({'requestor': 'ESPN',
                               'deviceId': get_device_id(),
                               'resource': resource})

    path = '/authorize'
    url = urlparse.urlunsplit(['https', 'api.auth.adobe.com',
                                   'api/v1' + path,
                                   params, ''])

    message = generate_message('GET', path)

    resp = get_url_response(url, message)
    settings = load_settings()
    if 'authorize' not in settings:
        settings['authorize'] = dict()
    xbmc.log(TAG + 'resource %s' % resource, xbmc.LOGDEBUG)
    settings['authorize'][resource.decode('iso-8859-1').encode('utf-8')] = resp
    save_settings(settings)


def deauthorize():
    params = urllib.urlencode({'deviceId': get_device_id()})

    path = '/logout'
    url = urlparse.urlunsplit(['https', 'api.auth.adobe.com',
                               'api/v1' + path,
                               params, ''])

    message = generate_message('DELETE', path)

    resp = get_url_response(url, message, body = None, method = 'DELETE')
    settings = load_settings()
    if 'authorize' in settings:
        del settings['authorize']
    if 'authenticateRegCode' in settings:
        del settings['authenticateRegCode']
    save_settings(settings)


# getShortMediaToken
# Sample '{"mvpdId":"","expires":"1463618218000","serializedToken":"+++++++=","userId":"",
# "requestor":"ESPN","resource":" resource"}'
def get_short_media_token(resource):
    if has_to_reauthenticate():
        xbmc.log(TAG + 're-authenticating device', xbmc.LOGDEBUG)
        re_authenticate()
    authorize(resource)
    params = urllib.urlencode({'requestor': 'ESPN',
                               'deviceId' : get_device_id(),
                               'resource' : resource})

    path = '/mediatoken'
    url = urlparse.urlunsplit(['https', 'api.auth.adobe.com',
                                   'api/v1' + path,
                                   params, ''])

    message = generate_message('GET', path)

    try:
        resp = get_url_response(url, message)
    except urllib2.HTTPError as exception:
        if exception.code == 401:
            xbmc.log(TAG + 'Unauthorized exception, trying again', xbmc.LOGDEBUG)
            re_authenticate()
            resp = get_url_response(url, message)
        else:
            raise exception
    settings = load_settings()
    settings['getShortMediaToken'] = resp
    save_settings(settings)
    return resp['serializedToken']


def is_authenticated():
    settings = load_settings()
    return 'authenticateRegCode' in settings


def has_to_reauthenticate():
    settings = load_settings()
    return is_expired(settings['authenticateRegCode']['expires'])


def is_authorized(resource):
    settings = load_settings()
    if 'authorize' in settings and resource.decode('iso-8859-1').encode('utf-8') in settings['authorize']:
        return not is_expired(settings['authorize'][resource.decode('iso-8859-1').encode('utf-8')]['expires'])


def get_expires_time(key):
    settings = load_settings()
    expires = settings[key]['expires']
    expires_time = time.localtime(int(expires) / 1000)
    return time.strftime('%Y-%m-%d %H:%M', expires_time)


def get_authentication_expires():
    return get_expires_time('authenticateRegCode')


def get_authorization_expires():
    return get_expires_time('authorize')


def clean_up_authorization_tokens():
    settings = load_settings()
    keys_to_delete = list()
    if 'authorize' in settings:
        for key in settings['authorize']:
            if 'expires' in settings['authorize'][key]:
                if is_expired(settings['authorize'][key]['expires']):
                    keys_to_delete.append(key)
            else:
                keys_to_delete.append(key)
    for key in keys_to_delete:
        del settings['authorize'][key]
    save_settings(settings)


def get_user_metadata():
    params = urllib.urlencode({'requestor': 'ESPN',
                               'deviceId' : get_device_id()})

    path = '/tokens/usermetadata'
    url = urlparse.urlunsplit(['https', 'api.auth.adobe.com',
                                   'api/v1' + path,
                                   params, ''])

    message = generate_message('GET', path)

    resp = get_url_response(url, message)
