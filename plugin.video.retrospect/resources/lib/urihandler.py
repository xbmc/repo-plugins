# SPDX-License-Identifier: CC-BY-NC-SA-4.0

import os
import time

from resources.lib.backtothefuture import PY2
if PY2:
    # noinspection PyCompatibility,PyUnresolvedReferences
    from cookielib import Cookie, CookieJar, MozillaCookieJar
else:
    # noinspection PyCompatibility
    from http.cookiejar import Cookie, CookieJar, MozillaCookieJar
from collections import namedtuple

import requests
import requests.cookies
import requests.utils

from resources.lib.connectivity.cachehttpadapter import CacheHTTPAdapter
from resources.lib.connectivity.streamcache import StreamCache
from resources.lib.logger import Logger
from resources.lib.proxyinfo import ProxyInfo


UriStatus = namedtuple('UriStatus', [
    'code',
    'reason',
    'url',
    'error'
])


class UriHandler(object):
    __handler = None
    __error = "UriHandler not initialized. Use UriHandler.create_uri_handler ======="

    @staticmethod
    def create_uri_handler(cache_dir=None, web_time_out=30,
                           cookie_jar=None, ignore_ssl_errors=False):
        """ Initialises the UriHandler class

        Keyword Arguments:
        :param str cache_dir:           A path for http caching. If specified, caching will be used.
        :param int web_time_out:        Timeout for requests in seconds.
        :param str|unicode cookie_jar:  The path to the cookie jar (in case of file storage).
        :param bool ignore_ssl_errors:  Ignore any SSL certificate errors.

        :return: A new UriHandler object
        :rtype: _RequestsHandler

        """

        # Only create a new handler if we did not have, or if the user options changed
        if UriHandler.__handler is None or \
                UriHandler.instance().ignoreSslErrors != ignore_ssl_errors:

            handler = _RequestsHandler(
                cache_dir=cache_dir, web_time_out=web_time_out, cookie_jar=cookie_jar,
                ignore_ssl_errors=ignore_ssl_errors
            )

            UriHandler.__handler = handler
            Logger.info("Initialised: %s", handler)
        else:
            Logger.info("Re-using existing UriHandler: %s", UriHandler.__handler)
        return UriHandler.__handler

    @staticmethod
    def instance():
        """ return the logger instance

        :return: The current UriHandler instance
        :rtype: _RequestsHandler

        """

        return UriHandler.__handler

    @staticmethod
    def download(uri, filename, folder, progress_callback=None, proxy=None,
                 params=None, data=None, json=None, referer=None, additional_headers=None):
        """ Downloads a remote file

        :param str filename:                The filename that should be used to store the file.
        :param str folder:                  The folder to save the file in.
        :param str params:                  Data to send with the request (open(uri, params)).
        :param str uri:                     The URI to download.
        :param dict[str, any]|str data:     Data to send with the request (open(uri, data)).
        :param dict[str, any] json:              Json to send with the request (open(uri, params)).
        :param ProxyInfo proxy:             The address and port (proxy.address.ext:port) of a
                                            proxy server that should be used.
        :param str referer:                 The http referer to use.
        :param dict additional_headers:     The optional headers.
        :param function progress_callback:  The callback for progress update. The format is
                                            function(retrievedSize, totalSize, perc, completed, status)

        :return: The full path of the location to which it was downloaded.
        :rtype: str

        """

        return UriHandler.instance().download(uri, filename, folder, progress_callback, proxy,
                                              params, data, json, referer, additional_headers)

    @staticmethod
    def open(uri, proxy=None, params=None, data=None, json=None,
             referer=None, additional_headers=None, no_cache=False, force_text=False):
        """ Open an URL Async using a thread

        :param str uri:                   The URI to download.
        :param str params|bytes:          Data to send with the request (open(uri, params)).
        :param dict[str, any]|str data:   Data to send with the request (open(uri, data)).
        :param dict[str, any] json:       Json to send with the request (open(uri, params)).
        :param ProxyInfo proxy:           The address and port (proxy.address.ext:port) of a
                                          proxy server that should be used.
        :param str referer:               The http referer to use.
        :param dict additional_headers:   The optional headers.
        :param bool no_cache:             Should cache be disabled.
        :param bool force_text:           In case no content type is specified, force text.

        :return: The data that was retrieved from the URI.
        :rtype: str|unicode

        """

        return UriHandler.instance().open(uri, proxy, params, data, json,
                                          referer, additional_headers, no_cache, force_text)

    @staticmethod
    def header(uri, proxy=None, referer=None, additional_headers=None):
        """ Retrieves header information only.

        :param str uri:                     The URI to fetch the header from.
        :param ProxyInfo proxy:             The address and port (proxy.address.ext:port) of a
                                            proxy server that should be used.
        :param str referer:                 The http referer to use.
        :param dict additional_headers:     The optional headers.

        :return: Content-type and the URL to which a redirect could have occurred.
        :rtype: tuple[str,str]

        """

        return UriHandler.instance().header(uri, proxy, referer,
                                            additional_headers)

    @staticmethod
    def set_cookie(version=0, name='', value='',
                   port=None,
                   # Not used: port_specified=False,
                   domain='',
                   # Not used: domain_specified=True,
                   domain_initial_dot=False,
                   path='/',
                   # Not used: path_specified=True,
                   secure=False,
                   expires=4102444555,
                   # Not used:
                   # discard=False,
                   # comment=None,
                   # comment_url=None,
                   # rest=None,
                   # rfc2109=False
                   ):
        """ Sets a cookie in the UriHandler cookie jar

        :param int version:             The cookie version
        :param str name:                The name of the cookie
        :param str value:               The value of the cookie
        :param int|None port:           String representing a port or a set of
                                        ports (eg. '80', or '80,8080'), or None
        :param str domain:              The domain for which the cookie should be valid
        :param bool domain_initial_dot: If the domain explicitly specified by the server began with a dot ('.').
        :param str path:                The path the cookie is valid for
        :param bool secure:             If cookie should only be returned over a secure connection
        :param int expires:             Integer expiry date in seconds since epoch, or None.

        :return: The new cookie.
        :rtype: cookielib.Cookie
        """

        Logger.debug("Setting a cookie with this data:\n"
                     "name:   '%s'\n"
                     "value:  '%s'\n"
                     "domain: '%s'\n"
                     "path:   '%s'",
                     name, value, domain, path)
        c = Cookie(version=version, name=name, value=value,
                   port=port, port_specified=port is not None,
                   domain=domain, domain_specified=domain is not None,
                   domain_initial_dot=domain_initial_dot,
                   path=path, path_specified=path is not None,
                   secure=secure,
                   expires=expires,
                   discard=False,
                   comment=None,
                   comment_url=None,
                   rest={'HttpOnly': None})  # rfc2109=False)
        # the rfc2109 parameters is not valid in Python 2.4 (Xbox), so we ommit it.
        UriHandler.instance().cookieJar.set_cookie(c)
        return c

    # noinspection PyProtectedMember
    @staticmethod
    def get_cookie(name, domain, path="/", match_start=False):
        """ Fetches a specific cookie.

        :param str name:            Name of the cookie.
        :param str domain:          Domain of the cookie.
        :param str path:            Path of the cookie.
        :param bool match_start:    Should only match the start of a name?

        :return: the found cookie or
        :rtype: cookielib.Cookie|None

        """

        if domain not in UriHandler.instance().cookieJar._cookies or \
                path not in UriHandler.instance().cookieJar._cookies[domain]:
            return None

        cookies = UriHandler.instance().cookieJar._cookies[domain][path]
        if not match_start:
            if name in cookies:
                return cookies[name]
            return None

        # do a startswith search
        cookies = [c for c in cookies.values() if c.name.startswith(name)]
        if not cookies:
            return None
        else:
            Logger.trace("Found cookie '%s'", cookies[0].name)
            return cookies[0]

    # noinspection PyProtectedMember
    @staticmethod
    def delete_cookie(name=None, domain=None):
        cookie_jar = UriHandler.instance().cookieJar
        if domain not in cookie_jar._cookies:
            Logger.debug("No cookies were found for '%s'", domain)
            return

        if name is None:
            cookie_jar.clear(domain=domain)
        else:
            cookie_jar.clear(name=name, domain=domain)

        if UriHandler.instance().cookieJarFile:
            # noinspection PyUnresolvedReferences
            cookie_jar.save()

    @staticmethod
    def get_extension_from_url(url):
        """ determines the file extension for a certain URL

        :param str url:     The URL to search
        :return: Returns an extension or "" if not was found.
        :rtype: str

        """

        extensions = {".divx": "divx",
                      ".flv": "flv",
                      ".mp4": "mp4",
                      ".m4v": "mp4",
                      ".avi": "avi",
                      "h264": "mp4"}
        for ext in extensions:
            if url.find(ext) > 0:
                return extensions[ext]

        return ""


class _RequestsHandler(object):

    def __init__(self, cache_dir=None, web_time_out=30, cookie_jar=None,
                 ignore_ssl_errors=False):
        """ Initialises the UriHandler class

        Keyword Arguments:
        :param str cache_dir:         A path for http caching. If specified, caching will be used.
        :param int web_time_out:      Timeout for requests in seconds
        :param str cookie_jar:        The path to the cookie jar (in case of file storage)
        :param ignore_ssl_errors:     Ignore any SSL certificate errors.

        """

        self.id = int(time.time())

        if cookie_jar:
            self.cookieJar = MozillaCookieJar(cookie_jar)
            if not os.path.isfile(cookie_jar):
                self.cookieJar.save()
            self.cookieJar.load()
            self.cookieJarFile = True
        else:
            self.cookieJar = CookieJar()
            self.cookieJarFile = False

        self.cacheDir = cache_dir
        self.cacheStore = None
        if cache_dir:
            self.cacheStore = StreamCache(cache_dir)
            Logger.debug("Opened %s", self.cacheStore)
        else:
            Logger.debug("No cache-store provided. Cached disabled.")

        self.userAgent = "Mozilla/5.0 (Windows; U; Windows NT 6.1; en-GB; rv:1.9.2.13) Gecko/20101203 Firefox/3.6.13 (.NET CLR 3.5.30729)"
        self.webTimeOut = web_time_out                # max duration of request
        self.ignoreSslErrors = ignore_ssl_errors      # ignore SSL errors
        if self.ignoreSslErrors:
            Logger.warning("Ignoring all SSL errors in Python")

        # status of the most recent call
        self.status = UriStatus(code=0, url=None, error=False, reason=None)

        # for download animation
        self.__animationIndex = -1

    def download(self, uri, filename, folder, progress_callback=None, proxy=None, params="",
                 data="", json="", referer=None, additional_headers=None):
        """ Downloads a remote file

        :param str filename:                The filename that should be used to store the file.
        :param str folder:                  The folder to save the file in.
        :param str params:                  Data to send with the request (open(uri, params)).
        :param str uri:                     The URI to download.
        :param dict[str, any]|str data:     Data to send with the request (open(uri, data)).
        :param dict[str, any] json:              Json to send with the request (open(uri, params)).
        :param ProxyInfo proxy:             The address and port (proxy.address.ext:port) of a
                                            proxy server that should be used.
        :param str referer:                 The http referer to use.
        :param dict additional_headers:     The optional headers.
        :param function progress_callback:  The callback for progress update. The format is
                                            function(retrievedSize, totalSize, perc, completed, status)

        :return: The full path of the location to which it was downloaded.
        :rtype: str

        """

        if not folder or not filename:
            raise ValueError("Destination folder and filename should be specified")
        if not os.path.isdir(folder):
            raise ValueError("Destination folder is not a valid location")
        if not progress_callback:
            raise ValueError("A callback must be specified")

        download_path = os.path.join(folder, filename)
        if os.path.isfile(download_path):
            Logger.info("Url already downloaded to: %s", download_path)
            return download_path

        Logger.info("Creating Downloader for url '%s' to filename '%s'", uri, download_path)
        r = self.__requests(uri, proxy=proxy, params=params, data=data, json=json,
                            referer=referer, additional_headers=additional_headers,
                            no_cache=True, stream=True)
        if r is None:
            return ""

        retrieved_bytes = 0
        total_size = int(r.headers.get('Content-Length', '0').strip())
        # There is an issue with the way Requests checks for input and it does not like the newInt.
        if PY2:
            chunk_size = 10 * 1024
        else:
            chunk_size = 1024 if total_size == 0 else total_size // 100
        cancel = False
        with open(download_path, 'wb') as fd:
            for chunk in r.iter_content(chunk_size=chunk_size):
                fd.write(chunk)
                retrieved_bytes += len(chunk)

                if progress_callback:
                    cancel = self.__do_progress_callback(progress_callback, retrieved_bytes, total_size, False)
                if cancel:
                    Logger.warning("Download of %s aborted", uri)
                    break

        if cancel:
            if os.path.isfile(download_path):
                Logger.info("Removing partial download: %s", download_path)
                os.remove(download_path)
            return ""

        if progress_callback:
            self.__do_progress_callback(progress_callback, retrieved_bytes, total_size, True)
        return download_path

    def open(self, uri, proxy=None, params=None, data=None, json=None,
             referer=None, additional_headers=None, no_cache=False, force_text=False):
        """ Open an URL Async using a thread

        :param str uri:                         The URI to download.
        :param str params:                      Data to send with the request (open(uri, params)).
        :param dict[str, any]|str|bytes data:   Data to send with the request (open(uri, data)).
        :param dict[str, any] json:             Json to send with the request (open(uri, params)).
        :param ProxyInfo proxy:                 The address and port (proxy.address.ext:port) of a
                                                proxy server that should be used.
        :param str referer:                     The http referer to use.
        :param dict|None additional_headers:    The optional headers.
        :param bool no_cache:                   Should cache be disabled.
        :param bool force_text:                 In case no content type is specified, force text.

        :return: The data that was retrieved from the URI.
        :rtype: str|unicode

        """
        r = self.__requests(uri, proxy=proxy, params=params, data=data, json=json,
                            referer=referer, additional_headers=additional_headers,
                            no_cache=no_cache, stream=False)
        if r is None:
            return ""

        content_type = r.headers.get("content-type", "")
        if r.encoding == 'ISO-8859-1' and "text" in content_type:
            # Requests defaults to ISO-8859-1 for all text content that does not specify an encoding
            Logger.debug("Found 'ISO-8859-1' for 'text' content-type. Using UTF-8 instead.")
            r.encoding = 'utf-8'

        elif r.encoding is None and force_text:
            Logger.debug("Found missing encoding and 'force_text' was specified. Using UTF-8.")
            r.encoding = 'utf-8'

        elif r.encoding is None and self.__is_text_content_type(content_type):
            Logger.debug("Found missing encoding for content type '%s' is considered text. Using UTF-8 instead.", content_type)
            r.encoding = 'utf-8'

        # We might need a better mechanism here.
        if not r.encoding and content_type.lower() in ["application/json", "application/javascript"]:
            return r.text

        return r.text if r.encoding else r.content

    def header(self, uri, proxy=None, referer=None, additional_headers=None):
        """ Retrieves header information only.

        :param str uri:                         The URI to fetch the header from.
        :param ProxyInfo|none proxy:            The address and port (proxy.address.ext:port) of a
                                                proxy server that should be used.
        :param str|none referer:                The http referer to use.
        :param dict|none additional_headers:    The optional headers.

        :return: Content-type and the URL to which a redirect could have occurred.
        :rtype: tuple[str,str]

        """

        with requests.session() as s:
            s.cookies = self.cookieJar
            s.verify = not self.ignoreSslErrors

            proxies = self.__get_proxies(proxy, uri)
            headers = self.__get_headers(referer, additional_headers)

            Logger.info("Performing a HEAD for %s", uri)
            r = s.head(uri, proxies=proxies, headers=headers, allow_redirects=True,
                       timeout=self.webTimeOut)

            content_type = r.headers.get("Content-Type", "")
            real_url = r.url

            self.status = UriStatus(code=r.status_code, url=uri, error=not r.ok, reason=r.reason)
            if self.cookieJarFile:
                # noinspection PyUnresolvedReferences
                self.cookieJar.save()

            if r.ok:
                Logger.info("%s resulted in '%s %s' (%s) for %s",
                            r.request.method, r.status_code, r.reason, r.elapsed, r.url)
                return content_type, real_url
            else:
                Logger.error("%s failed with in '%s %s' (%s) for %s",
                             r.request.method, r.status_code, r.reason, r.elapsed, r.url)
                return "", ""

    # noinspection PyUnusedLocal
    def __requests(self, uri, proxy, params, data, json, referer,
                   additional_headers, no_cache, stream):

        with requests.session() as s:
            s.cookies = self.cookieJar
            s.verify = not self.ignoreSslErrors
            if self.cacheStore and not no_cache:
                Logger.trace("Adding the %s to the request", self.cacheStore)
                s.mount("https://", CacheHTTPAdapter(self.cacheStore))
                s.mount("http://", CacheHTTPAdapter(self.cacheStore))

            proxies = self.__get_proxies(proxy, uri)

            headers = self.__get_headers(referer, additional_headers)

            if params is not None:
                # Old UriHandler behaviour. Set form header to keep compatible
                if "content-type" not in headers:
                    headers["content-type"] = "application/x-www-form-urlencoded"

                Logger.info("Performing a POST with '%s' for %s", headers["content-type"], uri)
                r = s.post(uri, data=params, proxies=proxies, headers=headers,
                           stream=stream, timeout=self.webTimeOut)
            elif data is not None:
                # Normal Requests compatible data object
                Logger.info("Performing a POST with '%s' for %s", headers.get("content-type", "<No Content-Type>"), uri)
                r = s.post(uri, data=data, proxies=proxies, headers=headers,
                           stream=stream, timeout=self.webTimeOut)
            elif json is not None:
                Logger.info("Performing a json POST with '%s' for %s", headers.get("content-type", "<No Content-Type>"), uri)
                r = s.post(uri, json=json, proxies=proxies, headers=headers,
                           stream=stream, timeout=self.webTimeOut)
            else:
                Logger.info("Performing a GET for %s", uri)
                r = s.get(uri, proxies=proxies, headers=headers,
                          stream=stream, timeout=self.webTimeOut)

            if r.ok:
                Logger.info("%s resulted in '%s %s' (%s) for %s",
                            r.request.method, r.status_code, r.reason, r.elapsed, r.url)
            else:
                Logger.error("%s failed with '%s %s' (%s) for %s",
                             r.request.method, r.status_code, r.reason, r.elapsed, r.url)

            self.status = UriStatus(code=r.status_code, url=r.url, error=not r.ok, reason=r.reason)
            if self.cookieJarFile:
                # noinspection PyUnresolvedReferences
                self.cookieJar.save()
            return r

    def __get_headers(self, referer, additional_headers):
        headers = {}
        if additional_headers:
            for k, v in additional_headers.items():
                headers[k.lower()] = v

        if "user-agent" not in headers:
            headers["user-agent"] = self.userAgent
        if referer and "referer" not in headers:
            headers["referer"] = referer

        return headers

    def __get_proxies(self, proxy, url):
        """

        :param ProxyInfo proxy:
        :param url:

        :return:
        :rtype: dict[str, str]

        """

        if proxy is None:
            return None

        elif not proxy.use_proxy_for_url(url):
            Logger.debug("Not using proxy due to filter mismatch")

        elif proxy.Scheme == "http":
            Logger.debug("Using a http(s) %s", proxy)
            proxy_address = proxy.get_proxy_address()
            return {"http": proxy_address, "https": proxy_address}

        elif proxy.Scheme == "dns":
            Logger.debug("Using a DNS %s", proxy)
            return {"dns": proxy.Proxy}

        Logger.warning("Unsupported Proxy Scheme: %s", proxy.Scheme)
        return None

    def __do_progress_callback(self, progress_callback, retrieved_size, total_size, completed):
        """ Performs a callback, if the progressCallback was specified.

        :param progress_callback:        The callback method
        :param retrieved_size:           Number of bytes retrieved
        :param total_size:               Total number of bytes
        :param completed:               Are we done?
        @rtype : Boolean                Should we cancel the download?

        """

        if progress_callback is None:
            # no callback so it was not cancelled
            return False

        # calculated some stuff
        self.__animationIndex = (self.__animationIndex + 1) % 4
        bytes_to_mb = 1048576
        animation_frames = ["-", "\\", "|", "/"]
        animation = animation_frames[self.__animationIndex]
        retrievedsize_mb = 1.0 * retrieved_size / bytes_to_mb
        totalsize_mb = 1.0 * total_size / bytes_to_mb
        if total_size > 0:
            percentage = 100.0 * retrieved_size / total_size
        else:
            percentage = 0
        status = '%s - %i%% (%.1f of %.1f MB)' % \
                 (animation, percentage, retrievedsize_mb, totalsize_mb)
        try:
            return progress_callback(retrieved_size, total_size, percentage, completed, status)
        except:
            Logger.error("Error in Progress Callback", exc_info=True)
            # cancel the download
            return True

    def __is_text_content_type(self, content_type):
        return content_type.lower() in ["application/vnd.apple.mpegurl", "application/x-mpegurl"]

    def __str__(self):
        return "UriHandler [id={0}, useCaching={1}, ignoreSslErrors={2}]"\
            .format(self.id, self.cacheStore, self.ignoreSslErrors)
