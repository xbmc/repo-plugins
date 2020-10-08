import os, re, sys
from kodi_six import xbmc, xbmcaddon

if sys.version_info[0] > 2:
    import http
    cookielib = http.cookiejar
else:
    import cookielib


class Util:
    addon_path = xbmc.translatePath(xbmcaddon.Addon().getAddonInfo('profile'))

    def find(self, source, start_str, end_str):
        start = source.find(start_str)
        end = source.find(end_str, start + len(start_str))

        if start != -1:
            return source[start + len(start_str):end]
        else:
            return ''

    def natural_sort_key(self, s):
        _nsre = re.compile('([0-9]+)')
        return [int(text) if text.isdigit() else text.lower()
                for text in re.split(_nsre, s)]

    def save_cookies(self, cookiejar):
        cookie_file = os.path.join(self.addon_path, 'cookies.lwp')
        cj = cookielib.LWPCookieJar()
        try:
            cj.load(cookie_file, ignore_discard=True)
        except:
            pass
        for c in cookiejar:
            args = dict(vars(c).items())
            args['rest'] = args['_rest']
            del args['_rest']
            c = cookielib.Cookie(**args)
            cj.set_cookie(c)
        cj.save(cookie_file, ignore_discard=True)

    def load_cookies(self):
        cookie_file = os.path.join(self.addon_path, 'cookies.lwp')
        cj = cookielib.LWPCookieJar()
        try:
            cj.load(cookie_file, ignore_discard=True)
        except:
            pass

        return cj

    def check_cookies(self):
        perform_login = True
        if os.path.isfile(os.path.join(self.addon_path, 'cookies.lwp')):
            fingerprint_valid = False
            ipid_valid = False
            cj = cookielib.LWPCookieJar(os.path.join(self.addon_path, 'cookies.lwp'))
            cj.load(os.path.join(self.addon_path, 'cookies.lwp'), ignore_discard=True)

            for cookie in cj:
                if cookie.name == "fprt" and not cookie.is_expired():
                    fingerprint_valid = True
                elif cookie.name == "ipid" and not cookie.is_expired():
                    ipid_valid = True

            if fingerprint_valid and ipid_valid:
                perform_login = False

        return perform_login

    def delete_cookies(self):
        if os.path.isfile(os.path.join(self.addon_path, 'cookies.lwp')):
            os.remove(os.path.join(self.addon_path, 'cookies.lwp'))
