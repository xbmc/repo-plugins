# SPDX-License-Identifier: CC-BY-NC-SA-4.0

import json
import random

from resources.lib.authentication.authenticationhandler import AuthenticationHandler
from resources.lib.authentication.authenticationresult import AuthenticationResult
from resources.lib.addonsettings import AddonSettings, LOCAL
from resources.lib.helpers.htmlentityhelper import HtmlEntityHelper
from resources.lib.helpers.jsonhelper import JsonHelper
from resources.lib.logger import Logger
from resources.lib.urihandler import UriHandler


class RtlXlHandler(AuthenticationHandler):
    def __init__(self, realm, api_key):
        """ Initializes a handler for the authentication provider

        :param str api_key:     The API key to use
        :param str realm:       The realm for this handler

        """

        if not api_key:
            raise ValueError("API Key required for RTL XL via Gigya")

        super(RtlXlHandler, self).__init__(realm, device_id=None)

        self.api_key = api_key
        self.__setting_signature = "{}:signature".format(realm)

        # internal data
        self.__signature = None
        self.__user_id = None
        self.__signature_timestamp = None
        self.__common_param_dict = {
            "APIKey": self.api_key,
            "authMode": "cookie"
        }
        self.__common_params = \
            "APIKey={}&authMode=cookie".format(HtmlEntityHelper.url_encode(self.api_key))

        # rtl_cookie_consent=2.0.0; rtlcslistversion=39.0.0;
        # UriHandler.set_cookie(name="rtl_cookie_consent", value="2.0.0")
        # UriHandler.set_cookie(name="rtlcslistversion", value="39.0.0")

    def log_on(self, username, password):
        """ Peforms the logon of a user.

        :param str username:    The username
        :param str password:    The password to use

        :returns: a AuthenticationResult with the result of the log on
        :rtype: AuthenticationResult

        """

        # first we need a random context_id R<10 numbers>
        context_id = int(random.random() * 8999999999) + 1000000000

        # then we do an initial bootstrap call, which retrieves the `gmid` and `ucid` cookies
        url = "https://sso.rtl.nl/accounts.webSdkBootstrap" \
              "?apiKey={}" \
              "&pageURL=https%3A%2F%2Fwww.rtlxl.nl%2F" \
              "&format=json" \
              "&callback=gigya.callback" \
              "&context=R{}".format(self.api_key, context_id)
        init_login = UriHandler.open(url, no_cache=True)
        init_data = JsonHelper(init_login)
        if init_data.get_value("statusCode") != 200:
            Logger.error("Error initiating login")
            return AuthenticationResult(None)

        # actually do the login request, which requires an async call to retrieve the result
        login_url = "https://sso.rtl.nl/accounts.login" \
                    "?context={0}".format(context_id)

        login_data = {
            "loginID": username,
            "password": password,
            # "include": "profile,data",
            # "includeUserInfo": "true",
            "pageURL": "https://www.rtlxl.nl/profiel",
            "format": "json",
            # "callback": "gigya.callback",
            "context": "R{}".format(context_id),
            "targetEnv": "jssdk",
            "sessionExpiration": 7776000
        }
        login_data.update(self.__common_param_dict)
        login_response = UriHandler.open(login_url, data=login_data, no_cache=True)

        # Process the result
        authentication_result = self.__extract_session_data(login_response)
        authentication_result.existing_login = False
        return authentication_result

    def active_authentication(self):
        """ Check if the user with the given name is currently authenticated.

        :returns: a AuthenticationResult with the account data.
        :rtype: AuthenticationResult

        """

        login_token = AddonSettings.get_setting(self.__setting_signature, store=LOCAL)

        login_cookie = UriHandler.get_cookie("gmid", domain=".sso.rtl.nl")
        if login_token and \
                login_cookie is not None and \
                not login_cookie.is_expired():
            # only retrieve the account information using the cookie and the token
            account_info_url = "https://sso.rtl.nl/accounts.getAccountInfo?{}" \
                               "&login_token={}".format(self.__common_params, login_token)
            account_info = UriHandler.open(account_info_url, no_cache=True)

            # See if it was successful
            auth_info = self.__extract_session_data(account_info)
            auth_info.existing_login = True
            return auth_info

        return AuthenticationResult(None)

    def get_authentication_token(self):
        """ Fetches an authentication token for the given login

        :return: token value
        :rtype: str

        """

        token_data = UriHandler.open("https://api.rtl.nl/rtlxl/token/api/2/token", no_cache=True)
        token_json = JsonHelper(token_data)
        token = token_json.get_value("accessToken")
        return token

    def log_off(self, username):
        """ Check if the user with the given name is currently authenticated.

        :param str username:    The username to log off

        :returns: Indication of success
        :rtype: bool

        """

        # clean older data
        UriHandler.delete_cookie(domain=".sso.rtl.nl")
        AddonSettings.set_setting(self.__setting_signature, "", store=LOCAL)
        return True

    def __extract_session_data(self, logon_data):
        """

        :param logon_data:
        :return:
        :rtype: AuthenticationResult

        """

        logon_json = json.loads(logon_data)
        result_code = logon_json.get("statusCode")
        Logger.trace("Logging in returned: %s", result_code)
        if result_code != 200:
            Logger.error("Error loging in: %s - %s", logon_json.get("errorMessage"),
                         logon_json.get("errorDetails"))
            return AuthenticationResult(None)

        user_name = logon_json.get("profile", {}).get("email") or None

        signature_setting = logon_json.get("sessionInfo", {}).get("login_token")
        if signature_setting:
            Logger.info("Found 'login_token'. Saving it.")
            AddonSettings.set_setting(self.__setting_signature, signature_setting.split("|")[0],
                                      store=LOCAL)

        self.__signature = logon_json.get("UIDSignature")
        self.__user_id = logon_json.get("UID")
        self.__signature_timestamp = logon_json.get("signatureTimestamp")

        # TODO: is this correct?
        has_premium = logon_json.\
            get("data", {}).\
            get("authorization", {}).\
            get("rtlxl_premium", {}).\
            get("subscription", {}).\
            get("id") == "premium"

        # The channels are not interesting
        # premium_channels = logon_json.get_value(
        #     "data", "authorization", "Stievie_free", "channels")
        return AuthenticationResult(user_name, has_premium=has_premium)
