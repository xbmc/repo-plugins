"""SRGSSR Base API Client"""

from datetime import datetime, timedelta
import requests
from requests.auth import HTTPBasicAuth
from requests import Response


class SRGSSRApiException(Exception):
    def __init__(self, api_name: str, message: str):
        self.api_name = api_name
        self.message = message
        super().__init__(message)


class InvalidCredentialsException(SRGSSRApiException):
    pass


class InvalidTokenException(SRGSSRApiException):
    pass


class SRGSSRApiClient:
    """SRGSSR API Client Base Class"""

    _VERSION = None  # The API version (e.g. "v1")
    _API_NAME = None  # The API name (e.g. Video, Subtitles)
    _API_URL_NAME = None  # The API URL name (present in the API URL, e.g. videometadata)

    def __init__(self, base_url: str, creds: dict, plugin, verify: bool = True):
        """API Client creation
        :param base_url: The API base URL (with the protocol)
        :param creds: The credentials dictionary
        :param plugin: The plugin object that created the client. Used to access it's logger and settings
        :param verify: If true, server's SSL certificate is verified
        """

        if not creds.get("key") or not creds.get("secret"):
            raise ValueError("SRGSSRApiClient creds must contain a 'key' and 'secret' fields")

        self._base_url = base_url
        self._basic_auth = HTTPBasicAuth(creds.get("key"), creds.get("secret"))
        self._verify = verify
        self._plugin = plugin
        self._logger = self._plugin.logger
        self._session = requests.Session()
        self._auth_token = self.get_auth_token()

    @property
    def version(self):
        if self._VERSION is None:
            raise NotImplementedError(
                f"_VERSION attribute must be overriden in the subclass {self.__class__}"
            )
        return self._VERSION

    @property
    def api_name(self):
        if self._API_NAME is None:
            raise NotImplementedError(
                f"_API_NAME attribute must be overriden in the subclass {self.__class__}"
            )
        return self._API_NAME

    @property
    def api_url_name(self):
        if self._API_URL_NAME is None:
            raise NotImplementedError(
                f"_API_URL_NAME attribute must be overriden in the subclass {self.__class__}"
            )
        return self._API_URL_NAME

    def get_auth_token(self) -> str:
        """Returning the authorization token

        Trying to get the auth token from the plugin settings. If it doesn't
        exists, request a new one
        """
        token_exp = getattr(self._plugin.settings, f"srgssr_{self.api_name}_token_exp")
        if token_exp:
            token_exp = datetime.fromisoformat(token_exp)
            token = getattr(self._plugin.settings, f"srgssr_{self.api_name}_token")
            if token and (token_exp > datetime.utcnow()):
                self._logger.debug(f"Using cached AuthToken (valid until {token_exp})")
                return token

        # Token doesn't exist or no more valid
        return self.request_new_token()

    def request_new_token(self) -> str:
        """Requests a new AccessToken to the API using the credentials"""
        self._logger.debug("Requesting new AuthToken")

        params = {"grant_type": "client_credentials"}
        res = requests.post(
            f"{self._base_url}/oauth/v1/accesstoken",
            params=params,
            auth=self._basic_auth,
        )
        if res.status_code in [401, 403]:
            raise InvalidCredentialsException(self.api_name, "Invalid key/secret to access the API")
        if not res.ok:
            raise SRGSSRApiException(self.api_name, f"Error{res.status_code}: {res.content}")

        data = res.json()
        token = data["access_token"]
        expires_in = data["expires_in"]
        token_exp = (datetime.utcnow() + timedelta(seconds=expires_in)).isoformat()
        self._logger.debug(f"Got a new AuthToken valid until {token_exp}")

        setattr(self._plugin.settings, f"srgssr_{self.api_name}_token", token)
        setattr(self._plugin.settings, f"srgssr_{self.api_name}_token_exp", token_exp)

        return token

    @staticmethod
    def _renew_access_token(func):
        """Decorator for API calls. Automatically renews the access token if expired"""

        def wrapper(self, *args, **kwargs):
            try:
                return func(self, *args, **kwargs)
            except InvalidTokenException:
                # Invoke the code responsible for get a new token
                self.request_new_token()

                # once the token is refreshed, we can retry the operation
                return func(self, *args, **kwargs)

        return wrapper

    def _handle_response(self, res: Response) -> dict:
        """Errors handling + returning json response"""
        if res.status_code in [401, 403]:
            self._logger.error(f"Error{res.status_code}: Invalid token. {res.content}")
            raise InvalidTokenException(self.api_name, "Invalid Auth Token")
        if not res.ok:
            msg = f"Error{res.status_code}: {res.content}"
            self._logger.error(msg)
            raise SRGSSRApiException(self.api_name, msg)
        return res.json()

    def _url(self, path: str) -> str:
        """Constructs the API url"""
        return f"{self._base_url}/{self.api_url_name}/{self.version}/{path}"

    @property
    def _headers(self) -> dict:
        return {
            "accept": "application/json",
            "Authorization": f"Bearer {self._auth_token}",
        }

    # =============================== Generic http methods ==============================

    def _get(self, path: str, **kwargs) -> Response:
        return self._generic_http_method_request("get", path, **kwargs)

    def _post(self, path: str, **kwargs) -> Response:
        return self._generic_http_method_request("post", path, **kwargs)

    def _generic_http_method_request(self, method: str, path: str, **kwargs) -> Response:
        http_method = getattr(self._session, method)
        return http_method(
            self._url(path),
            **kwargs,
            verify=self._verify,
            headers=self._headers,
        )
