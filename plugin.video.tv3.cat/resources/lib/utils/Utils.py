from future import standard_library
standard_library.install_aliases()
from builtins import str
import urllib.request, urllib.parse, urllib.error
import urllib.request, urllib.error, urllib.parse
import json
import xbmcgui
import xbmc


def buildUrl(query, base_url):
    return base_url + '?' + urllib.parse.urlencode(query)


def getHtml(url):
    try:

        req = urllib.request.Request(url)
        response = urllib.request.urlopen(req)
        link = response.read()
        response.close()


        return link

    except urllib.error.URLError as e:
        xbmc.log("getHtml error - " + str(e))
        xbmc.log("getHtml url - " + url)

        return None


def getDataVideo(url):
    link = getHtml(url)

    try:

        link = link.decode("ISO-8859-1")
        data = json.loads(link)

    except ValueError:
        return None

    except TypeError:
        return None

    except:
        return None

    else:
        if len(data) > 0:

            return data

        else:
            return None


def toSeconds(durada):
    if durada:

        if len(durada) == 8:
            # durada hh:mm:ss

            h = durada[0:2]
            m = durada[3:5]
            s = durada[6:]

            r = (int(h) * 3600) + (int(m) * 60) + int(s)

            return r

        elif len(durada) == 11:
            # PT00H32M13S

            h = durada[2:4]
            m = durada[5:7]
            s = durada[8:10]

            r = (int(h) * 3600) + (int(m) * 60) + int(s)

            return r

        else:

            return None

    else:

        return None
