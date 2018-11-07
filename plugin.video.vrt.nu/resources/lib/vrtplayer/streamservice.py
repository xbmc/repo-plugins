from abc import ABCMeta, abstractmethod
import requests
from resources.lib.helperobjects import helperobjects

class StreamService:
    __metaclass__ = ABCMeta

    _BASE_MEDIA_SERVICE_URL = 'https://media-services-public.vrt.be/vualto-video-aggregator-web/rest/external/v1'
    _TOKEN_URL = _BASE_MEDIA_SERVICE_URL + '/tokens'
    _API_KEY ='3_qhEcPa5JGFROVwu5SWKqJ4mVOIkwlFNMSKwzPDAh8QZOtHqu6L4nD5Q7lk0eXOOG'

    @abstractmethod
    def __init__(self, kodi_wrapper):
        self._kodi_wrapper = kodi_wrapper

    def _get_session_and_token_from_(self):
        session = requests.session()
        token = None
        cred = helperobjects.Credentials(self._kodi_wrapper)
        if not cred.are_filled_in():
            self._kodi_wrapper.open_settings()
            cred.reload()
        
        r = session.post('https://accounts.vrt.be/accounts.login',
                               {'loginID': cred.username, 'password': cred.password, 'APIKey': self._API_KEY,
                                'sessionExpiration': '-1',
                                'targetEnv': 'jssdk',
                                'include': 'profile,data,emails,subscriptions,preferences,',
                                'includeUserInfo': 'true',
                                'loginMode': 'standard',
                                'lang': 'nl-inf',
                                'source': 'showScreenSet',
                                'sdk': 'js_latest',
                                'authMode': 'cookie',
                                'format': 'json'})

        session.get('https://token.vrt.be/vrtnuinitlogin?provider=site&destination=https://www.vrt.be/vrtnu/')

        logon_json = r.json()

        if logon_json['errorCode'] == 0:
            uid = logon_json['UID']
            sig = logon_json['UIDSignature']
            ts = logon_json['signatureTimestamp']

            data = {'UID': uid, 
                   'UIDSignature': sig,
                   'signatureTimestamp': ts ,
                   'client_id': 'vrtnu-site', 
                   'submit': 'submit'
                   } 

            response = session.post('https://login.vrt.be/perform_login', data=data)

            vrt_player_token_url = session.post(self._TOKEN_URL, headers={'Content-Type': 'application/json'})

            token = vrt_player_token_url.json()['vrtPlayerToken']
            return (session, token)
        else:
            title = self._kodi_wrapper.get_localized_string(32051)
            message = self._kodi_wrapper.get_localized_string(32052)
            self._kodi_wrapper.show_ok_dialog(title, message)
