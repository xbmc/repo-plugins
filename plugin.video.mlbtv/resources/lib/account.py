import sys, xbmc, xbmcaddon, xbmcgui
import requests
from utils import Util


class Account:
    addon = xbmcaddon.Addon()
    username = ''
    password = ''
    session_key = ''
    verify = False

    def __init__(self):
        self.username = self.addon.getSetting('username')
        self.password = self.addon.getSetting('password')
        self.session_key = self.addon.getSetting('session_key')
        self.util = Util()

    def login(self):
        # Check if username and password are provided
        if self.username == '':
            dialog = xbmcgui.Dialog()
            username = dialog.input('Please enter your username', type=xbmcgui.INPUT_ALPHANUM)
            self.addon.setSetting(id='username', value=username)

        if self.password == '':
            dialog = xbmcgui.Dialog()
            password = dialog.input('Please enter your password', type=xbmcgui.INPUT_ALPHANUM, option=xbmcgui.ALPHANUM_HIDE_INPUT)
            self.addon.setSetting(id='password', value=password)

        if self.username == '' or self.password == '':
            sys.exit()
        else:
            url = 'https://secure.mlb.com/pubajaxws/services/IdentityPointService'
            headers = {
                "SOAPAction": "http://services.bamnetworks.com/registration/identityPoint/identify",
                "Content-type": "text/xml; charset=utf-8",
                "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 6.0.1; Hub Build/MHC19J)",
                "Connection": "Keep-Alive"
            }

            payload = "<?xml version='1.0' encoding='UTF-8'?>"
            payload += '<SOAP-ENV:Envelope xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">'
            payload += '<SOAP-ENV:Body><tns:identityPoint_identify_request xmlns:tns="http://services.bamnetworks.com/registration/types/1.4">'
            payload += '<tns:identification type="email-password"><tns:id xsi:nil="true"/>'
            payload += '<tns:fingerprint xsi:nil="true"/>'
            payload += '<tns:email>'
            payload += '<tns:id xsi:nil="true"/>'
            payload += '<tns:address>' + self.username + '</tns:address>'
            payload += '</tns:email>'
            payload += '<tns:password>' + self.password + '</tns:password>'
            payload += '<tns:mobilePhone xsi:nil="true"/>'
            payload += '<tns:profileProperty xsi:nil="true"/>'
            payload += '</tns:identification>'
            payload += '</tns:identityPoint_identify_request>'
            payload += '</SOAP-ENV:Body>'
            payload += '</SOAP-ENV:Envelope>'

            r = requests.post(url, headers=headers, data=payload, verify=self.verify)

            """
            Bad username => <status><code>-1000</code><message> [Invalid credentials for identification] [com.bamnetworks.registration.types.exception.IdentificationException: Account doesn't exits]</message><exceptionClass>com.bamnetworks.registration.types.exception.IdentificationException</exceptionClass><detail type="identityPoint" field="exists" message="false" messageKey="identityPoint.exists" /><detail type="identityPoint" field="email-password" message="identification error on identity point of type email-password" messageKey="identityPoint.email-password" /></status>
            Bad password => <status><code>-1000</code><message> [Invalid credentials for identification] [com.bamnetworks.registration.types.exception.IdentificationException: Invalid Password]</message><exceptionClass>com.bamnetworks.registration.types.exception.IdentificationException</exceptionClass><detail type="identityPoint" field="exists" message="true" messageKey="identityPoint.exists" /><detail type="identityPoint" field="email-password" message="identification error on identity point of type email-password" messageKey="identityPoint.email-password" /></status>
            Good => <status><code>1</code><message>OK</message></status>
            """
            if self.util.find(r.text, '<code>', '</code>') != '1':
                title = self.util.find(r.text, '<message> [', '] [')
                msg = self.util.find(r.text, 'com.bamnetworks.registration.types.exception.IdentificationException: ', ']</message>')
                dialog = xbmcgui.Dialog()
                dialog.ok(title, msg)
                sys.exit()
            else:
                self.util.save_cookies(r.cookies)

    def feature_service(self):
        if self.util.check_cookies():
            self.login()
        cookies = requests.utils.dict_from_cookiejar(self.util.load_cookies())
        url = 'https://secure.mlb.com/pubajaxws/services/FeatureService'
        headers = {
            "SOAPAction": "http://services.bamnetworks.com/registration/feature/findEntitledFeatures",
            "Content-type": "text/xml; charset=utf-8",
            "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 6.0.1; Hub Build/MHC19J)",
            "Connection": "Keep-Alive"
        }

        payload = "<?xml version='1.0' encoding='UTF-8'?>"
        payload += '<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/">'
        payload += '<soapenv:Header />'
        payload += '<soapenv:Body>'
        payload += '<feature_findEntitled_request xmlns="http://services.bamnetworks.com/registration/types/1.6">'

        if 'ipid' in cookies and 'fprt' in cookies and self.session_key != '':
            payload += "<identification type='fingerprint'>"
            payload += '<id>' + cookies['ipid'] + '</id>'
            payload += '<fingerprint>' + cookies['fprt'] + '</fingerprint>'
            payload += "<signOnRestriction type='mobileApp'>"
            payload += '<location>ANDROID_21d994bd-ebb1-4253-bcab-3550e7882294</location>'
            payload += '<sessionKey>' + self.session_key + '</sessionKey>'
        else:
            payload += "<identification type='email-password'>"
            payload += '<email><address>' + self.username + '</address></email>'
            payload += '<password>' + self.password + '</password>'
            payload += '<signOnRestriction type="mobileApp">'
            payload += '<location>ANDROID_21d994bd-ebb1-4253-bcab-3550e7882294</location>'

        payload += '</signOnRestriction>'
        payload += '</identification>'
        payload += '<featureContextName>MLBTV2017.INAPPPURCHASE</featureContextName>'
        payload += '</feature_findEntitled_request>'
        payload += '</soapenv:Body>'
        payload += '</soapenv:Envelope>'

        r = requests.post(url, headers=headers, data=payload, verify=self.verify)
        if self.util.find(r.text, '<code>', '</code>') != '1':
            title = self.util.find(r.text, '<message> [', '] [')
            msg = self.util.find(r.text, 'com.bamnetworks.registration.types.exception.IdentificationException: ', ']</message>')
            dialog = xbmcgui.Dialog()
            dialog.ok(title, msg)
            sys.exit()
        else:
            self.session_key = self.util.find(r.text, '<sessionKey>', '</sessionKey>')
            self.addon.setSetting("session_key", self.session_key)
            self.util.save_cookies(r.cookies)

    def logout(self):
        self.util.delete_cookies()

    def media_entitlement(self):
        # check_cookies()
        self.feature_service()
        cookies = requests.utils.dict_from_cookiejar(self.util.load_cookies())
        url = 'https://media-entitlement.mlb.com/jwt'
        url += '?ipid=' + cookies['ipid']
        url += '&fingerprint=' + cookies['fprt']
        url += '&os=Android'
        url += '&appname=AtBat'
        headers = {
            'x-api-key': 'arBv5yTc359fDsqKdhYC41NZnIFZqEkY5Wyyn9uA',
            'Cache-Control': 'no-cache',
            'Connection': 'Keep-Alive',
            'User-Agent': 'okhttp/3.9.0'
        }

        r = requests.get(url, headers=headers, cookies=self.util.load_cookies(), verify=self.verify)

        return r.text

    def access_token(self):
        url = 'https://edge.bamgrid.com/token'
        headers = {
            'Authorization': 'Bearer bWxidHYmYW5kcm9pZCYxLjAuMA.6LZMbH2r--rbXcgEabaDdIslpo4RyZrlVfWZhsAgXIk',
            'Accept': 'application/json',
            'X-BAMSDK-Version': 'v3.0.0-beta2-3',
            'X-BAMSDK-Platform': 'Android',
            'User-Agent': 'BAMSDK/3.0.0-beta2 (mlbaseball-7993996e; v2.0/v3.0.1; android; tv) WeTek Hub (wetekhub-user 6.0.1 MHC19J 20170612 release-keys; Linux; 6.0.1; API 23)',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Connection': 'Keep-Alive',
            'Accept-Encoding': 'gzip'
        }

        payload = 'grant_type=urn:ietf:params:oauth:grant-type:token-exchange'
        payload += '&subject_token=' + self.media_entitlement()
        payload += '&subject_token_type=urn:ietf:params:oauth:token-type:jwt'
        payload += '&platform=android-tv'

        r = requests.post(url, headers=headers, data=payload, cookies=self.util.load_cookies(), verify=self.verify)
        access_token = r.json()['access_token']
        # refresh_toekn = r.json()['refresh_token']
        return access_token

    def get_stream(self, media_id):
        auth = self.access_token()
        url = 'https://edge.svcs.mlb.com/media/' + media_id + '/scenarios/android'
        headers = {
            'Accept': 'application/vnd.media-service+json; version=2',
            'Authorization': auth,
            'X-BAMSDK-Version': 'v3.0.0-beta2-3',
            'X-BAMSDK-Platform': 'Android',
            'User-Agent': 'BAMSDK/3.0.0-beta2 (mlbaseball-7993996e; v2.0/v3.0.1; android; tv) WeTek Hub (wetekhub-user 6.0.1 MHC19J 20170612 release-keys; Linux; 6.0.1; API 23)'
        }

        r = requests.get(url, headers=headers, cookies=self.util.load_cookies(), verify=self.verify)
        if r.status_code != 200:
            dialog = xbmcgui.Dialog()
            title = "Error Occured"
            msg = ""
            for item in r.json()['errors']:
                msg += item['code'] + '\n'
            dialog.notification(title, msg, ICON, 5000, False)
            sys.exit()

        stream_url = r.json()['stream']['complete']
        headers = '|User-Agent=MLB.TV/3.5.0 (Linux;Android 6.0.1) ExoPlayerLib/2.5.4'
        headers += '&Authorization=' + auth
        headers += '&Cookie='
        cookies = requests.utils.dict_from_cookiejar(self.util.load_cookies())
        for key, value in cookies.iteritems():
            headers += key + '=' + value + '; '

        return stream_url, headers
