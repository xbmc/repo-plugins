#
#      Copyright (C) 2012 Tommy Winther
#      http://tommy.winther.nu
#
#  This Program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2, or (at your option)
#  any later version.
#
#  This Program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this Program; see the file LICENSE.txt.  If not, write to
#  the Free Software Foundation, 675 Mass Ave, Cambridge, MA 02139, USA.
#  http://www.gnu.org/copyleft/gpl.html
#

Q_BEST = 0   # 1700 kb/s
Q_HIGH = 1   # 1000 kb/s
Q_MEDIUM = 2 # 500 kb/s
Q_LOW = 3    # 250 kb/s

QUALITIES = [Q_BEST, Q_HIGH, Q_MEDIUM, Q_LOW]

CHANNELS = list()

CATEGORY_DR = 30201
CATEGORY_TV2_REG = 30202
CATEGORY_MISC = 30203
CATEGORIES = {CATEGORY_DR : list(), CATEGORY_TV2_REG : list(), CATEGORY_MISC : list()}

class Channel(object):
    def __init__(self, id, category, config_key = None):
        self.id = id
        self.category = category
        self.config_key = config_key
        self.urls = dict()

        CHANNELS.append(self)
        CATEGORIES[category].append(self)

    def add_urls(self, best = None, high = None, medium = None, low = None):
        if best: self.urls[Q_BEST] = best
        if high: self.urls[Q_HIGH] = high
        if medium: self.urls[Q_MEDIUM] = medium
        if low: self.urls[Q_LOW] = low

    def get_url(self, quality, idx = 0):
        if self.urls.has_key(quality):
            urls = self.urls[quality]
        elif quality == Q_BEST and self.urls.has_key(Q_HIGH):
            urls = self.urls[Q_HIGH]
        else:
            return None

        if type(urls) == list:
            if len(urls) > idx:
                return urls[idx]
            else:
                return urls[0]
        else:
            return urls

    def get_id(self):
        return self.id

    def get_category(self):
        return self.category

    def get_description(self):
        return ''

    def get_config_key(self):
        return self.config_key

# http://dr.dk/nu/embed/live?height=467&width=830
# DR1
Channel(1, CATEGORY_DR, "dr1.stream").add_urls(
    high   = ['rtmp://livetv.gss.dr.dk/live/livedr01astream3 live=1', 'rtmp://livetv.gss.dr.dk/live/livedr01bstream3 live=1'],
    medium = ['rtmp://livetv.gss.dr.dk/live/livedr01astream2 live=1', 'rtmp://livetv.gss.dr.dk/live/livedr01bstream2 live=1'],
    low    = ['rtmp://livetv.gss.dr.dk/live/livedr01astream1 live=1', 'rtmp://livetv.gss.dr.dk/live/livedr01bstream1 live=1'])
# DR2
Channel(2, CATEGORY_DR, "dr2.stream").add_urls(
    high   = ['rtmp://rtmplive.dr.dk/live/livedr02astream3 live=1', 'rtmp://rtmplive.dr.dk/live/livedr02bstream3 live=1'],
    medium = ['rtmp://rtmplive.dr.dk/live/livedr02astream2 live=1', 'rtmp://rtmplive.dr.dk/live/livedr02bstream2 live=1'],
    low    = ['rtmp://rtmplive.dr.dk/live/livedr02astream1 live=1', 'rtmp://rtmplive.dr.dk/live/livedr02bstream1 live=1'])
# DR Update
Channel(3, CATEGORY_DR).add_urls(#, "drupdate.stream").add_urls(
    high   = 'rtmp://livetv.gss.dr.dk/live/livedr03astream3 live=1',
    medium = 'rtmp://livetv.gss.dr.dk/live/livedr03astream2 live=1',
    low    = 'rtmp://livetv.gss.dr.dk/live/livedr03astream1 live=1')
# DR K
Channel(4, CATEGORY_DR, "drk.stream").add_urls(
    high   = ['rtmp://rtmplive.dr.dk/live/livedr04astream3 live=1', 'rtmp://rtmplive.dr.dk/live/livedr04bstream3 live=1'],
    medium = ['rtmp://rtmplive.dr.dk/live/livedr04astream2 live=1', 'rtmp://rtmplive.dr.dk/live/livedr04bstream2 live=1'],
    low    = ['rtmp://rtmplive.dr.dk/live/livedr04astream1 live=1', 'rtmp://rtmplive.dr.dk/live/livedr04bstream1 live=1'])
# DR Ramasjang
Channel(5, CATEGORY_DR, "drramasjang.stream").add_urls(
    high   = ['rtmp://rtmplive.dr.dk/live/livedr05astream3 live=1', 'rtmp://rtmplive.dr.dk/live/livedr05bstream3 live=1'],
    medium = ['rtmp://rtmplive.dr.dk/live/livedr05astream2 live=1', 'rtmp://rtmplive.dr.dk/live/livedr05bstream2 live=1'],
    low    = ['rtmp://rtmplive.dr.dk/live/livedr05astream1 live=1', 'rtmp://rtmplive.dr.dk/live/livedr05bstream1 live=1'])
# DR HD
Channel(6, CATEGORY_DR, "drhd.stream").add_urls(
    best   = ['rtmp://livetv.gss.dr.dk/live/livedr06astream3 live=1', 'rtmp://livetv.gss.dr.dk/live/livedr06bstream3 live=1'],
    high   = ['rtmp://livetv.gss.dr.dk/live/livedr06astream2 live=1', 'rtmp://livetv.gss.dr.dk/live/livedr06bstream2 live=1'],
    medium = ['rtmp://livetv.gss.dr.dk/live/livedr06astream1 live=1', 'rtmp://livetv.gss.dr.dk/live/livedr06bstream1 live=1'])

# TV2 Fyn
Channel(100, CATEGORY_TV2_REG).add_urls(
    high   = 'rtmp://80.63.11.91:1935/live/_definst_/tv2fyn_1000 live=1'
)
# TV2 Lorry
Channel(101, CATEGORY_TV2_REG).add_urls(
    best   = 'rtmp://80.63.11.91:1935/live/_definst_/tv2lorry_2000 live=1',
    high   = 'rtmp://80.63.11.91:1935/live/_definst_/tv2lorry_1000 live=1',
    medium = 'rtmp://80.63.11.91:1935/live/_definst_/tv2lorry_300 live=1'
)
# TV2 Syd
Channel(102, CATEGORY_TV2_REG).add_urls(
    best   = 'rtmp://80.63.11.91:1935/live/_definst_/tvsyd_2000 live=1',
    high   = 'rtmp://80.63.11.91:1935/live/_definst_/tvsyd_1000 live=1',
    medium = 'rtmp://80.63.11.91:1935/live/_definst_/tvsyd_300 live=1'
)
# TV2 Midtvest
Channel(103, CATEGORY_TV2_REG).add_urls(
    high   = 'http://ms1.tvmidtvest.dk/live')
# TV2 Nord
Channel(105, CATEGORY_TV2_REG).add_urls(
    best   = 'rtmp://80.63.11.91:1935/live/_definst_/tv2nord-plus_2000 live=1',
    high   = 'rtmp://80.63.11.91:1935/live/_definst_/tv2nord-plus_1000 live=1',
    medium = 'rtmp://80.63.11.91:1935/live/_definst_/tv2nord-plus_300 live=1'
)
# TV2 East
Channel(106, CATEGORY_TV2_REG).add_urls(
    best   = 'rtmp://tv2regup1.webhotel.net/videostreaming/ playpath=tv2east live=1'
)
# TV2 OJ
#Channel(108, CATEGORY_TV2_REG).add_urls(
#    best   = 'rtmp://80.63.11.91:1935/live/_definst_/tv2oj_2000 live=1',
#    high   = 'rtmp://80.63.11.91:1935/live/_definst_/tv2oj_1000 live=1',
#    medium = 'rtmp://80.63.11.91:1935/live/_definst_/tv2oj_300 live=1'
# )
# TV2 Bornholm
Channel(109, CATEGORY_TV2_REG).add_urls(
    best   = 'rtsp://itv02.digizuite.dk/tv2b live=1'
)

# http://ft.arkena.tv/xml/core_player_clip_data_v2_REAL.php?wtve=187&wtvl=2&wtvk=012536940751284&as=1
# Folketinget
Channel(201, CATEGORY_MISC).add_urls(
    best   = 'rtmp://ftflash.arkena.dk/webtvftlivefl/ playpath=mp4:live.mp4 pageUrl=http://www.ft.dk/webTV/TV_kanalen_folketinget.aspx live=1')
# danskespil lotto
Channel(202, CATEGORY_MISC).add_urls(
    best   = 'rtmp://lvs.wowza.jay.net/webstream/lotto live=1'
)
# kanalsport.dk
Channel(203, CATEGORY_MISC).add_urls(
    best   = 'http://lswb-de-08.servers.octoshape.net:1935/live/kanalsport/500k/playlist.m3u8'
)
