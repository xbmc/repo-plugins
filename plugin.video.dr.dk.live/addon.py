import sys

import xbmc
import xbmcgui
import xbmcplugin

import danishaddons

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
    },
    # From: http://ft.arkena.tv/xml/core_player_clip_data_v2.php?wtve=187&wtvl=2&wtvk=012536940751284
    {'name' : 'Folketinget', 'urls' : {
            'high' : 'rtmp://chip.arkena.com/webtvftfl/hi1'
        }
    }
]

def showChannels():

    for idx, c in enumerate(CHANNELS):
        icon = danishaddons.ADDON_PATH + "/resources/logos/" + c['name'].replace(" ", "_") + ".png"

        if c['urls'].has_key(getQuality()):
            item = xbmcgui.ListItem(c['name'], iconImage = icon)
            url = danishaddons.ADDON_PATH + '?idx=' + str(idx)
            xbmcplugin.addDirectoryItem(danishaddons.ADDON_HANDLE, url, item, True)

    xbmcplugin.endOfDirectory(danishaddons.ADDON_HANDLE)

def playChannel(idx):
    c = CHANNELS[int(idx)]
    q = getQuality()

    icon = danishaddons.ADDON_PATH + "/resources/logos/" + c['name'].replace(" ", "_") + ".png"

    if c['urls'].has_key(q):
        item = xbmcgui.ListItem(c['name'], thumbnailImage = icon)
        item.setProperty("IsLive", "true")
        xbmc.Player().play(c['urls'][q], item)
    else:
        d = xbmcgui.Dialog()
        d.ok(c['name'], danishaddons.msg(30001) % q.capitalize(), danishaddons.msg(30002))

def getQuality():
    return danishaddons.ADDON.getSetting('quality').lower()


if __name__ == '__main__':
    danishaddons.init(sys.argv)

    if danishaddons.ADDON_PARAMS.has_key('idx'):
        playChannel(danishaddons.ADDON_PARAMS['idx'])
    else:
        showChannels()

