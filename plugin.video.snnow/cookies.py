import os

def my_time2isoz(t=None):
    """
    This method is used to monkey patch tme2isoz from cookielib. On 32-bit
    platforms cookies that expire too far in the future cause exceptions.
    """
    from datetime import datetime, timedelta
    if t is None:
        dt = datetime.now()
    else:
        dt = datetime.utcfromtimestamp(0) + timedelta(seconds=int(t))
    return "%04d-%02d-%02d %02d:%02d:%02dZ"%\
            (dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second)

def my_lwp_cookie_str(cookie):
    """
    This method is used to monkey patch lwp_cookie_str from _LWPCookieJar. See
    my_time2isoz for a description of the problem.
    """
    from cookielib import join_header_words
    h = [(cookie.name, cookie.value),
         ("path", cookie.path),
         ("domain", cookie.domain)]
    if cookie.port is not None: h.append(("port", cookie.port))
    if cookie.path_specified: h.append(("path_spec", None))
    if cookie.port_specified: h.append(("port_spec", None))
    if cookie.domain_initial_dot: h.append(("domain_dot", None))
    if cookie.secure: h.append(("secure", None))
    if cookie.expires: h.append(("expires",
                               my_time2isoz(float(cookie.expires))))
    if cookie.discard: h.append(("discard", None))
    if cookie.comment: h.append(("comment", cookie.comment))
    if cookie.comment_url: h.append(("commenturl", cookie.comment_url))

    keys = cookie._rest.keys()
    keys.sort()
    for k in keys:
        h.append((k, str(cookie._rest[k])))

    h.append(("version", str(cookie.version)))

    return join_header_words([h])

class Cookies:
    """
    Class to simplify cookie jar management.
    """

    inst = None

    @staticmethod
    def cookies():
        if not Cookies.inst:
            Cookies.inst = Cookies()
        return Cookies.inst

    @staticmethod
    def getCookieJar():
        cookies = Cookies.cookies()
        cookie_file = cookies.getCookieFile()
        if os.path.isfile(cookie_file):
            return cookies.loadCookieJar()
        return cookies.createCookieJar()

    @staticmethod
    def saveCookieJar(jar):
        import _LWPCookieJar
        _LWPCookieJar.lwp_cookie_str = my_lwp_cookie_str
        cookies = Cookies.cookies()
        cookie_file = cookies.getCookieFile()

        jar.save(filename=cookie_file, ignore_discard=True)
        return None


    def getCookieFile(self):
        try:
            import xbmc, xbmcaddon
            base = xbmc.translatePath(xbmcaddon.Addon().getAddonInfo('profile'))
        except:
            base = os.getcwd()
        return os.path.join(base, 'cookies.lwp')


    def createCookieJar(self):
        """
        Create the cookie jar file. Do not use this; instead, call getCookieJar,
        which will create the cookie jar if it doesn't already exist
        """
        import cookielib
        cookie_file = self.getCookieFile()
        return cookielib.LWPCookieJar(cookie_file)


    def loadCookieJar(self):
        """
        Load the cookie jar file. Do not use this; instead, call getCookieJar,
        which will load the cookie jar if it already exists.
        """
        import cookielib
        jar = cookielib.LWPCookieJar()
        cookie_file = self.getCookieFile()
        jar.load(cookie_file,ignore_discard=True)
        return jar
