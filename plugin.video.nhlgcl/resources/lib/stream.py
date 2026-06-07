from resources.lib.globals import *

class Stream:
    id = ""
    auth_code = ""
    content_url = "https://nhltv.nhl.com/api/v3/contents/"

    def __init__(self,id):
        self.id = id
        self.auth_code = ""

    def check_access(self):
        url = f"{self.content_url}{self.id}/check-access"
        headers = {"User-Agent": UA_PC,
                   "Content-Type": "application/json;charset=UTF-8",
                   "Origin": "https://nhltv.nhl.com"
                   }
        data = {"type": "nhl"}
        xbmc.log(url)

        r = requests.post(url, headers=headers, json=data, cookies=load_cookies(), verify=VERIFY)
        xbmc.log(r.text)
        if r.ok:
            if "data" in r.json():
                self.auth_code = r.json()["data"]
        else:
            dialog = xbmcgui.Dialog()
            ok = dialog.ok(LOCAL_STRING(30368), LOCAL_STRING(30376))
            sys.exit()


    def player_settings(self):
        url = f"{self.content_url}{self.id}/player-settings"
        headers = {"User-Agent": UA_PC,
                   "Origin": "https://nhltv.nhl.com"
                   }

        xbmc.log(url)
        r = requests.get(url, headers=headers, cookies=load_cookies(), verify=VERIFY)
        xbmc.log(r.text)
        if not r.ok or 'streamAccess' not in r.json():
            dialog = xbmcgui.Dialog()
            ok = dialog.ok(LOCAL_STRING(30366), LOCAL_STRING(30367))
            sys.exit()

        access_url = r.json()['streamAccess']
        if self.auth_code != "":
            if "?" not in r.json()['streamAccess']:
                access_url = f"{access_url}?authorization_code={self.auth_code}"
            else:
                access_url = f"{access_url}&authorization_code={self.auth_code}"

        xbmc.log(str(access_url))

        return access_url

    def get_manifest(self):
        self.check_access()
        access_url = self.player_settings()
        headers = {"User-Agent": UA_PC,
                   "Content-Type": "application/json;charset=UTF-8",
                   "Origin": "https://nhltv.nhl.com"
                   }

        r = requests.post(access_url, headers=headers, verify=VERIFY)
        xbmc.log(r.text)

        if not r.ok or 'data' not in r.json() or 'stream' not in r.json()['data']:
            dialog = xbmcgui.Dialog()
            ok = dialog.ok(LOCAL_STRING(30366), r.json()["message"])
            sys.exit()


        return r.json()["data"]["stream"]