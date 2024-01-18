import time
from typing import Optional

try:
    import jwt
except ImportError:
    # The package is named pyjwt in Kodi 18: https://github.com/lottaboost/script.module.pyjwt/pull/1
    # noinspection PyUnresolvedReferences
    import pyjwt as jwt

from resources.lib.addonsettings import AddonSettings, LOCAL
from resources.lib.authentication.authenticationhandler import AuthenticationHandler
from resources.lib.authentication.authenticationresult import AuthenticationResult
from resources.lib.helpers.jsonhelper import JsonHelper
from resources.lib.logger import Logger
from resources.lib.urihandler import UriHandler


class GigyaHandler(AuthenticationHandler):
    def __init__(self, realm: str, api_key_3: str, api_key_4: str, device_id: str):
        super().__init__(realm, device_id.replace("-", "") + device_id.replace("-", "")[::-1])

        self.__api_key_3 = api_key_3
        self.__api_key_4 = api_key_4
        self.__build_id = "15627"

        self.__uid = None
        self.__uid_signature = None
        self.__uid_signature_timestamp = None
        self.__has_premium = False
        self.__jwt = None

    def log_on(self, username: str, password: str) -> AuthenticationResult:
        bootstrap_url = f"https://accounts.eu1.gigya.com/accounts.webSdkBootstrap?apiKey={self.__api_key_3}&sdk=js_latest&sdkBuild={self.__build_id}&format=json"
        bootstrap = UriHandler.open(bootstrap_url, no_cache=True)
        bootstrap_json = JsonHelper(bootstrap)
        if not bootstrap_json.get_value("statusReason") == "OK":
            Logger.error("Error initiating login")
            return AuthenticationResult(None)

        gmid = UriHandler.get_cookie("gmid", ".gigya.com").value
        UriHandler.set_cookie(name="gmid", value=gmid, domain=f".{self._realm}")

        login_url = f"https://gigya-merge.{self._realm}/accounts.login"
        login_data = {
            "loginID": username,
            "password": password,
            "sessionExpiration": -2,
            "targetEnv": "jssdk",
            "include": "profile,data",
            "includeUserInfo": True,
            "lang": "en",
            "APIKey": self.__api_key_4,
            "sdk": "js_latest",
            "authMode": "cookie",
            "pageURL": f"https://www.{self._realm}/inloggen",
            "sdkBuild": 15627,
            "format": "json",
        }

        headers = {
            "content-type": "application/x-www-form-urlencoded"
        }
        login_result = UriHandler.open(login_url, data=login_data, no_cache=True, additional_headers=headers)
        result = JsonHelper(login_result)

        error = result.get_value("errorDetails", fallback=None)
        if error:
            return AuthenticationResult(None, error=error)
        account = result.get_value("profile", "email")

        self.__extract_uid_info(result)

        # Check for premium, which also happens to need the JWT
        self.__check_for_premium()

        return AuthenticationResult(
            username=account, uid=self.__uid,
            has_premium=self.__has_premium, jwt=self.__jwt)

    def active_authentication(self) -> AuthenticationResult:
        login_token_cookie = UriHandler.get_cookie(f"glt_{self.__api_key_4}", domain=f".{self.realm}")
        if not login_token_cookie:
            return AuthenticationResult(None)

        profile_data = {
            "include": "profile,data",
            "lang": "en",
            "APIKey": self.__api_key_4,
            "sdk": "js_latest",
            "login_token": login_token_cookie.value,
            "authMode": "cookie",
            # "pageURL": "",
            "sdkBuild": 15627,
            "format": "json",
        }
        headers = {
            "content-type": "application/x-www-form-urlencoded"
        }
        data = UriHandler.open(f"https://gigya-merge.{self._realm}/accounts.getAccountInfo", additional_headers=headers, data=profile_data)
        json_data = JsonHelper(data)
        if json_data.get_value("errorCode"):
            error = json_data.get_value("statusReason")
            error = json_data.get_value("errorMessage", fallback=error)
            Logger.error(f"Gigya: getAccountInfo failed: {error}")
            return AuthenticationResult(None)

        username = json_data.get_value("profile", "email")
        self.__extract_uid_info(json_data)

        # Check for premium, which also happens to need the JWT
        self.__check_for_premium()

        return AuthenticationResult(
            username, existing_login=True, uid=self.__uid,
            has_premium=self.__has_premium, jwt=self.__jwt)

    def log_off(self, username) -> bool:
        UriHandler.delete_cookie(domain=".gigya.com")
        UriHandler.delete_cookie(domain=f".{self.realm}")
        AddonSettings.set_setting(f"{self.realm}-jwt", "", store=LOCAL)

        self.__uid = None
        self.__uid_signature = None
        self.__uid_signature_timestamp = None
        self.__has_premium = False
        self.__jwt = None
        return True

    def get_authentication_token(self) -> Optional[str]:
        if self.__jwt:
            return self.__jwt

        token_value = AddonSettings.get_setting(f"{self.realm}-jwt", store=LOCAL)
        if token_value:
            token = jwt.decode(token_value, options={"verify_signature": False})
            expire = token.get("exp")
            if expire < time.time():
                token = None

            if token:
                self.__jwt = token_value
                return token_value

        if not self.__uid:
            return None

        # Get a generic token
        url = "https://front-auth.videoland.bedrock.tech/v2/platforms/m6group_web/getJwt"
        headers = {
            "x-auth-device-id": self._device_id,
            "x-auth-gigya-signature": self.__uid_signature,
            "x-auth-gigya-signature-timestamp": str(self.__uid_signature_timestamp),
            "x-auth-gigya-uid": self.__uid
        }

        token = UriHandler.open(url, additional_headers=headers, no_cache=True)
        if not token:
            return None

        # Now load it for a profile
        # TODO: Might be the wrong profile if there are more.
        token_value = JsonHelper(token).get_value("token")
        profile_url = f"https://users.videoland.bedrock.tech/v2/platforms/m6group_web/users/{self.__uid}/profiles"
        profile_headers = {
            "Authorization": f"Bearer {token_value}"
        }
        profile_info = JsonHelper(UriHandler.open(profile_url, additional_headers=profile_headers, no_cache=True))
        puid = profile_info.get_value(0, "uid")

        # Actually fetch a token for it.
        headers["x-auth-profile-id"] = puid
        token_value = JsonHelper(UriHandler.open(url, additional_headers=headers, no_cache=True)).get_value("token")

        AddonSettings.set_setting(f"{self.realm}-jwt", token_value, store=LOCAL)
        self.__jwt = token_value
        return token_value

    def __check_for_premium(self):
        url = f"https://stores.videoland.bedrock.tech/premium/v4/customers/rtlnl/platforms/m6group_web/users/{self.__uid}/subscriptions"
        jwt = self.get_authentication_token()
        headers = {"Authorization": f"Bearer {jwt}"}
        subscriptions = JsonHelper(UriHandler.open(url, additional_headers=headers))
        current_subscription = subscriptions.get_value("current", 0, "current_contract")
        self.__has_premium = False if current_subscription.get("variant_id", "") == "Free" else True

    def __extract_uid_info(self, token: JsonHelper) -> None:
        self.__uid = token.get_value("UID")
        self.__uid_signature = token.get_value("UIDSignature")
        self.__uid_signature_timestamp = token.get_value("signatureTimestamp")
