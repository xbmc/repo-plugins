import sys
import cgi as urlparse

import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin

# High   : 1000 kb/s
# Medium :  500 kb/s
# Low    :  300 kb/s

CHANNELS = [
    # From: http://dr.dk/TV/Live/UPlayer?banner=false&deepLinking=true&useStartControls=false&width=830&height=467&disableWmode=true
    {'name' : 'DR1', 'urls' : {
            'high' : 'rtmp://rtmplive.dr.dk/live/livedr01astream3',
            'medium' : 'rtmp://rtmplive.dr.dk/live/livedr01astream2',
            'low' : 'rtmp://rtmplive.dr.dk/live/livedr01astream1'
        }
    },
    {'name' : 'DR2', 'urls' : {
            'high' : 'rtmp://rtmplive.dr.dk/live/livedr02astream3',
            'medium' : 'rtmp://rtmplive.dr.dk/live/livedr02astream2',
            'low' : 'rtmp://rtmplive.dr.dk/live/livedr02astream1'
        }
    },
    {'name' : 'DR Update', 'urls' : {
            'high' : 'rtmp://rtmplive.dr.dk/live/livedr03astream3',
            'medium' : 'rtmp://rtmplive.dr.dk/live/livedr03astream2',
            'low' : 'rtmp://rtmplive.dr.dk/live/livedr03astream1'
        }
    },
    {'name' : 'DR K', 'urls' : {
            'high' : 'rtmp://rtmplive.dr.dk/live/livedr04astream3',
            'medium' : 'rtmp://rtmplive.dr.dk/live/livedr04astream2',
            'low' : 'rtmp://rtmplive.dr.dk/live/livedr04astream1'
        }
    },
    {'name' : 'DR Ramasjang', 'urls' : {
            'high' : 'rtmp://rtmplive.dr.dk/live/livedr05astream3',
            'medium' : 'rtmp://rtmplive.dr.dk/live/livedr05astream2',
            'low' : 'rtmp://rtmplive.dr.dk/live/livedr05astream1'
        }
    },

    # From: http://www.24nordjyske.dk/webtv_high.asp
    {'name' : '24 Nordjyske', 'urls' : {
            'high' : 'mms://stream.nordjyske.dk/24nordjyske - Full Broadcast Quality',
            'medium' : 'mms://stream.nordjyske.dk/24nordjyske'
        }
    }]

def showChannels():
    for idx, c in enumerate(CHANNELS):
        icon = ADDON.getAddonInfo('path') + "/resources/logos/" + c['name'].replace(" ", "_") + ".png"

        if c['urls'].has_key(getQuality()):
            item = xbmcgui.ListItem(c['name'], iconImage = icon)
            url = PATH + '?idx=' + str(idx)
            xbmcplugin.addDirectoryItem(HANDLE, url, item, True)

    xbmcplugin.endOfDirectory(HANDLE)

def playChannel(idx):
    c = CHANNELS[int(idx)]
    q = getQuality()

    icon = ADDON.getAddonInfo('path') + "/resources/logos/" + c['name'].replace(" ", "_") + ".png"

    if c['urls'].has_key(q):
        item = xbmcgui.ListItem(c['name'], thumbnailImage = icon)
        item.setProperty("IsLive", "true")
        xbmc.Player().play(c['urls'][q], item)
    else:
        d = xbmcgui.Dialog()
        d.ok(c['name'], ADDON.getLocalizedString(30001) % q.capitalize(), ADDON.getLocalizedString(30002))

def getQuality():
    return ADDON.getSetting('quality').lower()


if __name__ == '__main__':
    ADDON = xbmcaddon.Addon(id = 'plugin.video.dr.dk.live')
    PATH = sys.argv[0]
    HANDLE = int(sys.argv[1])
    PARAMS = urlparse.parse_qs(sys.argv[2][1:])

    if PARAMS.has_key('idx'):
        playChannel(PARAMS['idx'][0])
    else:
        showChannels()

