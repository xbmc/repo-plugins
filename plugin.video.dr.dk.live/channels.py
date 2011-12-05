__author__ = 'tommy'

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
    def __init__(self, id, category):
        self.id = id
        self.category = category
        self.urls = dict()

        CHANNELS.append(self)
        CATEGORIES[category].append(self)

    def add_urls(self, best = None, high = None, medium = None, low = None):
        if best: self.urls[Q_BEST] = best
        if high: self.urls[Q_HIGH] = high
        if medium: self.urls[Q_MEDIUM] = medium
        if low: self.urls[Q_LOW] = low

    def get_url(self, quality):
        if self.urls.has_key(quality):
            return self.urls[quality]
        elif quality == Q_BEST and self.urls.has_key(Q_HIGH):
            return self.urls[Q_HIGH]
        else:
            return None

    def get_id(self):
        return self.id

    def get_category(self):
        return self.category

    def get_description(self):
        return ''

# http://dr.dk/nu/embed/live?height=467&width=830
# DR1
Channel(1, CATEGORY_DR).add_urls(
    high   = 'rtmp://rtmplive.dr.dk/live/livedr01astream3 live=1',
    medium = 'rtmp://rtmplive.dr.dk/live/livedr01astream2 live=1',
    low    = 'rtmp://rtmplive.dr.dk/live/livedr01astream1 live=1')
# DR2
Channel(2, CATEGORY_DR).add_urls(
    high   = 'rtmp://rtmplive.dr.dk/live/livedr02astream3 live=1',
    medium = 'rtmp://rtmplive.dr.dk/live/livedr02astream2 live=1',
    low    = 'rtmp://rtmplive.dr.dk/live/livedr02astream1 live=1')
# DR Update
Channel(3, CATEGORY_DR).add_urls(
    high   = 'rtmp://rtmplive.dr.dk/live/livedr03astream3 live=1',
    medium = 'rtmp://rtmplive.dr.dk/live/livedr03astream2 live=1',
    low    = 'rtmp://rtmplive.dr.dk/live/livedr03astream1 live=1')
# DR K
Channel(4, CATEGORY_DR).add_urls(
    high   = 'rtmp://rtmplive.dr.dk/live/livedr04astream3 live=1',
    medium = 'rtmp://rtmplive.dr.dk/live/livedr04astream2 live=1',
    low    = 'rtmp://rtmplive.dr.dk/live/livedr04astream1 live=1')
# DR Ramasjang
Channel(5, CATEGORY_DR).add_urls(
    high   = 'rtmp://rtmplive.dr.dk/live/livedr05astream3 live=1',
    medium = 'rtmp://rtmplive.dr.dk/live/livedr05astream2 live=1',
    low    = 'rtmp://rtmplive.dr.dk/live/livedr05astream1 live=1')
# DR HD
Channel(6, CATEGORY_DR).add_urls(
    best   = 'rtmp://livetv.gss.dr.dk/live/livedr06astream3 live=1',
    medium = 'rtmp://livetv.gss.dr.dk/live/livedr06astream2 live=1',
    low    = 'rtmp://livetv.gss.dr.dk/live/livedr06astream1 live=1')

# TV2 Fyn
Channel(100, CATEGORY_TV2_REG).add_urls(
    high   = 'rtmp://80.63.11.91:1935/live/_definst_/tv2fyn_1000 live=1')
# TV2 Lorry
Channel(101, CATEGORY_TV2_REG).add_urls(
    best   = 'rtmp://80.63.11.91:1935/live/_definst_/tv2lorry_2000 live=1',
    high   = 'rtmp://80.63.11.91:1935/live/_definst_/tv2lorry_1000 live=1',
    medium = 'rtmp://80.63.11.91:1935/live/_definst_/tv2lorry_300 live=1')
# Lorry+
Channel(102, CATEGORY_TV2_REG).add_urls(
    best   = 'rtmp://80.63.11.91:1935/live/_definst_/tv2lorry-plus_2000 live=1',
    high   = 'rtmp://80.63.11.91:1935/live/_definst_/tv2lorry-plus_1000 live=1',
    medium = 'rtmp://80.63.11.91:1935/live/_definst_/tv2lorry-plus_300 live=1')
# TV2 Midtvest
Channel(103, CATEGORY_TV2_REG).add_urls(
    high   = 'http://ms1.tvmidtvest.dk/frokosttv')
# TV2 Nord
Channel(104, CATEGORY_TV2_REG).add_urls(
    best   = 'rtmp://80.63.11.91:1935/live/_definst_/tv2nord_2000 live=1',
    high   = 'rtmp://80.63.11.91:1935/live/_definst_/tv2nord_1000 live=1',
    medium = 'rtmp://80.63.11.91:1935/live/_definst_/tv2nord_300 live=1')
# TV2 NordPlus
Channel(105, CATEGORY_TV2_REG).add_urls(
    best   = 'rtmp://80.63.11.91:1935/live/_definst_/tv2nord-plus_2000 live=1',
    high   = 'rtmp://80.63.11.91:1935/live/_definst_/tv2nord-plus_1000 live=1',
    medium = 'rtmp://80.63.11.91:1935/live/_definst_/tv2nord-plus_300 live=1')
# TV2 East
Channel(106, CATEGORY_TV2_REG).add_urls(
    high   = 'rtmp://tv2regup1.webhotel.net/videostreaming/ playpath=tv2east live=1')
# Kanal east
Channel(107, CATEGORY_TV2_REG).add_urls(
    high   = 'rtmp://tv2regup1.webhotel.net/videostreaming/ playpath=kanaleast live=1')
# TV2 OJ
Channel(108, CATEGORY_TV2_REG).add_urls(
    best   = 'rtmp://80.63.11.91:1935/live/_definst_/tv2oj_2000 live=1',
    high   = 'rtmp://80.63.11.91:1935/live/_definst_/tv2oj_1000 live=1',
    medium = 'rtmp://80.63.11.91:1935/live/_definst_/tv2oj_300 live=1')

# http://www.24nordjyske.dk/webtv_high.asp
# 24 Nordjyske
Channel(200, CATEGORY_MISC).add_urls(
    high   = 'mms://stream.nordjyske.dk/24nordjyske - Full Broadcast Quality',
    medium = 'mms://stream.nordjyske.dk/24nordjyske')

# http://ft.arkena.tv/xml/core_player_clip_data_v2_REAL.php?wtve=187&wtvl=2&wtvk=012536940751284&as=1
# Folketinget
Channel(201, CATEGORY_MISC).add_urls(
    best   = 'rtmp://ftflash.arkena.dk/webtvftlivefl/ playpath=mp4:live.mp4 pageUrl=http://www.ft.dk/webTV/TV_kanalen_folketinget.aspx live=1')
