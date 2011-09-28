import sys
import os

import xbmcaddon
import xbmcgui
import xbmcplugin

Q_BEST = 0   # 1700 kb/s
Q_HIGH = 1   # 1000 kb/s
Q_MEDIUM = 2 # 500 kb/s
Q_LOW = 3    # 250 kb/s

QUALITIES = [Q_BEST, Q_HIGH, Q_MEDIUM, Q_LOW]

CHANNELS = [
    # From: http://dr.dk/nu/embed/live?height=467&width=830
    {'name' : 'DR1', 'urls' : {
            Q_HIGH : 'rtmp://rtmplive.dr.dk/live/livedr01astream3',
            Q_MEDIUM : 'rtmp://rtmplive.dr.dk/live/livedr01astream2',
            Q_LOW : 'rtmp://rtmplive.dr.dk/live/livedr01astream1'
        }
    },
    {'name' : 'DR2', 'urls' : {
            Q_HIGH : 'rtmp://rtmplive.dr.dk/live/livedr02astream3',
            Q_MEDIUM : 'rtmp://rtmplive.dr.dk/live/livedr02astream2',
            Q_LOW : 'rtmp://rtmplive.dr.dk/live/livedr02astream1'
        }
    },
    {'name' : 'DR Update', 'urls' : {
            Q_HIGH : 'rtmp://rtmplive.dr.dk/live/livedr03astream3',
            Q_MEDIUM : 'rtmp://rtmplive.dr.dk/live/livedr03astream2',
            Q_LOW : 'rtmp://rtmplive.dr.dk/live/livedr03astream1'
        }
    },
    {'name' : 'DR K', 'urls' : {
            Q_HIGH : 'rtmp://rtmplive.dr.dk/live/livedr04astream3',
            Q_MEDIUM : 'rtmp://rtmplive.dr.dk/live/livedr04astream2',
            Q_LOW : 'rtmp://rtmplive.dr.dk/live/livedr04astream1'
        }
    },
    {'name' : 'DR Ramasjang', 'urls' : {
            Q_HIGH : 'rtmp://rtmplive.dr.dk/live/livedr05astream3',
            Q_MEDIUM : 'rtmp://rtmplive.dr.dk/live/livedr05astream2',
            Q_LOW : 'rtmp://rtmplive.dr.dk/live/livedr05astream1'
        }
    },
    {'name' : 'DR HD', 'urls' : {
            Q_BEST : 'rtmp://livetv.gss.dr.dk/live/livedr06astream3',
            Q_HIGH : 'rtmp://livetv.gss.dr.dk/live/livedr06astream2',
            Q_MEDIUM : 'rtmp://livetv.gss.dr.dk/live/livedr06astream1'
        }
    },
    # From: http://www.24nordjyske.dk/webtv_high.asp
    {'name' : '24 Nordjyske', 'urls' : {
            Q_HIGH : 'mms://stream.nordjyske.dk/24nordjyske - Full Broadcast Quality',
            Q_MEDIUM : 'mms://stream.nordjyske.dk/24nordjyske'
        }
    }]

class DanishLiveTV(object):
    def showChannels(self):
        for c in CHANNELS:
            icon = os.path.join(ADDON.getAddonInfo('path'), 'resources' ,'logos', c['name'].replace(' ', '_') + '.png')

            url = self.getUrl(c['urls'])
            if url:
                item = xbmcgui.ListItem(c['name'], iconImage = icon, thumbnailImage = icon)
                item.setInfo('video', infoLabels = {
                    'title' : c['name']
                })
                item.setProperty('Fanart_Image', FANART)
                item.setProperty('IsLive', 'true')
                xbmcplugin.addDirectoryItem(HANDLE, url, item)

        xbmcplugin.endOfDirectory(HANDLE)

    def getUrl(self, urls):
        quality = QUALITIES[int(ADDON.getSetting('quality'))]

        if urls.has_key(quality):
            return urls[quality]
        elif quality == Q_BEST and urls.has_key(Q_HIGH):
            return urls[Q_HIGH]
        else:
            return None

if __name__ == '__main__':
    ADDON = xbmcaddon.Addon(id = 'plugin.video.dr.dk.live')
    PATH = sys.argv[0]
    HANDLE = int(sys.argv[1])
    FANART = os.path.join(ADDON.getAddonInfo('path'), 'fanart.jpg')

    dktv = DanishLiveTV()
    dktv.showChannels()

