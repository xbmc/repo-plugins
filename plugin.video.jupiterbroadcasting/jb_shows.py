"""
Jb Shows Module.
Contains shows/feeds/helper methods
"""

# list of jb shows
FEED_BURNER = 'http://feeds2.feedburner.com/'
FEED_PRESS = 'http://feedpress.me/'
JUPITER_COM = 'http://www.jupiterbroadcasting.com/'


# public methods

def get_all_shows():
    """
    Retuns all JB Shows
    """
    return _shows()

def get_active_shows():
    """
    Returns all JB shows where 'archive' is False
    """
    active_shows = {}

    for item_name, data in _shows().iteritems():
        if not data['archived']:
            active_shows[item_name] = data

    return active_shows

def get_archived_shows():
    """
    Returns all JB shows where 'archive' is True
    """
    archived_shows = {}

    for item_name, data in _shows().iteritems():
        if data['archived']:
            archived_shows[item_name] = data

    return archived_shows

def sort_shows(shows):
    """
    Returns shows sorted in a list where show
    name (kodi string index) is the outer
    """
    return sorted(shows.items(), key=_sort_key)



# private methods
def _shows():
    """
    List of available Jupiter Broadcasting shows.
    Indexes and plot point to resources/language/yourlanguageHere/strings.xml
    """

    shows = {}

    # All Shows
    shows[30006] = {
        'feed': FEED_BURNER + 'AllJupiterVideos?format=xml',
        'feed-low': FEED_BURNER + 'AllJupiterVideos?format=xml',
        'feed-audio': FEED_BURNER + '/JupiterBroadcasting?format=xml',
        'image': 'most-recent.jpg',
        'plot': 30206,
        'genre': 'Technology',
        'archived': False,
        'count': 0
    }

    # Linux Action Show
    shows[30000] = {
        'feed': FEED_BURNER + 'linuxashd?format=xml',
        'feed-low': FEED_BURNER + 'linuxactionshowipodvid?format=xml',
        'feed-audio': FEED_BURNER + 'TheLinuxActionShowOGG?format=xml',
        'image': 'linux-action-show.jpg',
        'plot': 30200,
        'genre': 'Technology',
        'archived': True
    }

    # STOked
    shows[30002] = {
        'feed': FEED_BURNER + 'stokedhd?format=xml',
        'feed-low': FEED_BURNER + 'stokedipod?format=xml',
        'feed-audio': FEED_BURNER + 'stoked-ogg?format=xml',
        'image':'stoked.png',
        'plot': 30202,
        'genre': 'Technology',
        'archived': True
    }

    # TechSnap
    shows[30008] = {
        'feed': FEED_PRESS + 'techsnapvid',
        'feed-low': FEED_PRESS + 'techsnapvid',
        'feed-audio': 'http://techsnap.systems/rss',
        'image': 'techsnap.jpg',
        'plot': 30208,
        'genre': 'Technology',
        'archived': False
    }

    # SCIbyte
    shows[30009] = {
        'feed': FEED_BURNER + 'scibytehd?format=xml',
        'feed-low': FEED_BURNER + 'scibytemobile?format=xml',
        'feed-audio': FEED_BURNER + 'scibyteaudio?format=xml',
        'image': 'scibyte.jpg',
        'plot': 30209,
        'genre': 'Science',
        'archived': True 
    }

    # In Depth Look
    shows[30014] = {
        'feed': JUPITER_COM + 'feeds/indepthlookihd.xml',
        'feed-low': JUPITER_COM + 'feeds/indepthlookmob.xml',
        'feed-audio': JUPITER_COM + 'feeds/indepthlookmp3.xml?format=xml',
        'image': 'in-depth-look.jpg',
        'plot': 30214,
        'genre': 'Technology',
        'archived': True
    }

    # Unfilter
    shows[30016] = {
        'feed': JUPITER_COM + 'feeds/unfilterHD.xml',
        'feed-low': JUPITER_COM + 'feeds/unfilterMob.xml',
        'feed-audio': 'http://unfilter.show/rss',
        'image': 'unfilter.jpg',
        'plot': 30216,
        'genre': 'Technology',
        'archived': False
    }

    # FauxShow
    shows[30011] = {
        'feed': JUPITER_COM + 'feeds/FauxShowHD.xml',
        'feed-low': JUPITER_COM + 'feeds/FauxShowMobile.xml',
        'feed-audio': JUPITER_COM + 'feeds/FauxShowMP3.xml',
        'image': 'faux-show.jpg',
        'plot': 30211,
        'genre': 'Comedy',
        'archived': True
    }

    # Jupiter@Nite
    shows[30004] = {
        'feed': FEED_BURNER + 'jupiternitehd?format=xml',
        'feed-low': FEED_BURNER + 'jupiternitelargevid?format=xml',
        'feed-audio': FEED_BURNER + 'jupiternitemp3?format=xml',
        'image': 'jupiter-at-nite.jpg',
        'plot': 30204,
        'genre': 'Technology',
        'archived': True
    }

    # MMOrgue
    shows[30007] = {
        'feed': FEED_BURNER + 'MMOrgueHD?format=xml',
        'feed-low': FEED_BURNER + 'MMOrgueHD?format=xml',
        'feed-audio': JUPITER_COM + 'feeds/AllJupiterBroadcastingShowsOGG.xml',
        'image': 'mmorgue.jpg',
        'plot': 30207,
        'genre': 'Technology',
        'archived': True
    }

    # LOTSO
    shows[30003] = {
        'feed': FEED_BURNER + 'lotsovideo?format=xml',
        'feed-low': FEED_BURNER + 'lotsovideo?format=xml',
        'feed-audio': FEED_BURNER + 'lotsomp3?format=xml',
        'image': 'lotso.jpg',
        'plot': 30203,
        'genre': 'Technology',
        'archived': True
    }

    # Beer is Tasty
    shows[30001] = {
        'feed': FEED_BURNER + 'jupiterbeeristasty-hd?format=xml',
        'feed-low': FEED_BURNER + 'BeerIsTasty?format=xml',
        'feed-audio': FEED_BURNER + 'BeerIsTasty?format=xml',
        'image': 'beer-is-tasty.png',
        'plot': 30201,
        'genre': 'Technology',
        'archived': True
    }

    # Jupiter Files
    shows[30005] = {
        'feed': FEED_BURNER + 'ldf-video?format=xml',
        'feed-low': FEED_BURNER + 'ldf-video?format=xml',
        'feed-audio': FEED_BURNER + 'ldf-mp3?format=xml',
        'image': 'jupiter-files.jpg',
        'plot': 30205,
        'genre': 'Technology',
        'archived': True
    }

    # TORked
    shows[30015] = {
        'feed': FEED_BURNER + 'TorkedHd?format=xml',
        'feed-low': FEED_BURNER + 'TorkedMobile?format=xml',
        'feed-audio': FEED_BURNER + 'TorkedMp3?format=xml',
        'image': 'torked.jpg',
        'plot': 30215,
        'genre': 'Technology',
        'archived': True
    }

    # Coder Radio
    shows[30017] = {
        'feed': FEED_BURNER + 'coderradiovideo?format=xml',
        'feed-low': FEED_BURNER + 'coderradiomp3?format=xml',
        'feed-audio': 'http://coder.show/rss',
        'image': 'coder-radio.jpg',
        'plot': 30217,
        'genre': 'Technology',
        'archived': False
    }

    # Plan B
    shows[30018] = {
        'feed': FEED_BURNER + 'PlanBVideo?format=xml',
        'feed-low': FEED_BURNER + 'planbogg?format=xml',
        'feed-audio': FEED_BURNER + 'planbogg?format=xml',
        'image': 'planb.jpg',
        'plot': 30218,
        'genre': 'Technology',
        'archived': True
    }

    # Linux Unplugged
    shows[30019] = {
        'feed': FEED_BURNER + 'linuxunvid?format=xml',
        'feed-low': FEED_BURNER + 'linuxunplugged?format=xml',
        'feed-audio': 'http://linuxunplugged.com/rss',
        'image': 'linux-unplugged.jpg',
        'plot': 30219,
        'genre': 'Technology',
        'archived': False
    }

    # BSD Now
    shows[30020] = {
        'feed': FEED_BURNER + 'BsdNowHd?format=xml',
        'feed-low': FEED_BURNER + 'BsdNowMobile?format=xml',
        'feed-audio': FEED_BURNER + 'BsdNowMp3?format=xml',
        'image': 'bsd-now.jpg',
        'plot': 30220,
        'genre': 'Technology',
        'archived': False
    }
    
    # HowTo Linux
    shows[30021] = {
        'feed': FEED_BURNER + 'HowtoLinuxHd?format=xml',
        'feed-low': FEED_BURNER + 'HowtoLinuxMobile?format=xml',
        'feed-audio': FEED_BURNER + 'HowtoLinuxOgg?format=xml',
        'image': 'howto-linux.jpg',
        'plot': 30221,
        'genre': 'Technology',
        'archived': True
    }

    # Tech Talk Today
    shows[30022] = {
        'feed': FEED_PRESS + 't3mob',
        'feed-low': FEED_PRESS + 't3ogg',
        'feed-audio': 'http://techtalk.today/rss',
        'image': 'tech-talk-today.png',
        'plot': 30222,
        'genre': 'Technology',
        'archived': False
    }

    # Women's Tech Radio
    shows[30023] = {
        'feed': FEED_BURNER + 'wtrmobile?format=xml',
        'feed-low': FEED_BURNER + 'wtrogg?format=xml',
        'feed-audio': FEED_BURNER + 'wtrmp3?format=xml',
        'image': 'womens-tech-radio.png',
        'plot': 30223,
        'genre': 'Technology',
        'archived': True
    }

    # Meta Archive show
    shows[30025] = {
        'image': 'icon.png',
        'plot': 30225,
        'genre': 'Technology',
        'archived': False
    }

    # User Error
    shows[30024] = {
        'feed': FEED_PRESS + 'uevideo',
        'feed-low': FEED_PRESS + 'usererror',
        'feed-audio': FEED_PRESS + 'usererror',
        'image': 'usererror.png',
        'plot': 30224,
        'genre': 'Technology',
        'archived': False
        }

    # Ask Noah
    shows[30026] = {
        'feed': FEED_PRESS + 'AskNoahHD',
        'feed-low': FEED_PRESS + 'AskNoahHD',
        'feed-audio': 'http://podcast.asknoahshow.com/rss',
        'image': 'asknoah.png',
        'plot': 30226,
        'genre': 'Technology',
        'archived': False
        }

    # Linux Action News
    shows[30027] = {
        'feed': 'http://linuxactionnews.com/rss',
        'feed-low': 'http://linuxactionnews.com/rss',
        'feed-audio': 'http://linuxactionnews.com/rss',
        'image': 'linux-action-news.jpg',
        'plot': 30227,
        'genre': 'Technology',
        'archived': False
        }

    return shows

def _sort_key(show):
    """
    Sets the key for sorting to be the lowercase show name
    """
    return (show[0]).lower()
