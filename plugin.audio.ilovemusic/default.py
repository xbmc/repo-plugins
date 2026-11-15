import xbmcaddon
import xbmcplugin
import xbmcgui
import sys
import urllib.parse
import os

ADDON = xbmcaddon.Addon()
ADDON_ID = ADDON.getAddonInfo('id')
ADDON_NAME = ADDON.getAddonInfo('name')
ADDON_ICON = os.path.join(ADDON.getAddonInfo('path'), 'resources', 'media', 'ico.png')

STREAMS = [
    ('https://ilm.stream18.radiohost.de/ilm_iloveradio_mp3-192', 'I LOVE RADIO', 'i_love_radio.png'),
    ('https://ilm.stream18.radiohost.de/ilm_ilove2dance_mp3-192', 'I LOVE 2 DANCE', 'i_love_2_dance.png'),
    # I LOVE 2000+ THROWBACKS
    # I LOVE THROWBACKS
    ('https://ilm.stream35.radiohost.de/ilm_ilovebass_mp3-192', 'I LOVE BASS BY HBZ', 'i_love_BASS_BY_HBZ.png'),
    # I LOVE POP HITS
    ('https://ilm.stream35.radiohost.de/ilm_ilovechillhop_mp3-192', 'I LOVE CHILLHOP', 'i_love_chillhop.png'),
    # I LOVE CHILLOUT BEATS
    # I LOVE DANCE 2025
    # I LOVE DANCE FIRST!
    ('https://ilm.stream18.radiohost.de/ilm_ilovedancehistory_mp3-192', 'I LOVE DANCE HISTORY', 'i_love_dance_history.png'),
    ('https://ilm.stream35.radiohost.de/ilm_ilovedeutschrapbeste_mp3-192', 'I LOVE DEUTSCHRAP BESTE', 'i_love_deutschrap_beste.png'),
    ('https://ilm.stream35.radiohost.de/ilm_ilovedeutschrapfirst_mp3-192', 'I LOVE DEUTSCHRAP FIRST!', 'i_love_deutschrap_first.png'),
    # I LOVE DJ FROM MARS
    ('https://ilm.stream18.radiohost.de/ilm_ilovegreatesthits_mp3-192', 'I LOVE GREATEST HITS', 'i_love_greatest_hits.png'),
    ('https://ilm.stream18.radiohost.de/ilm_ilovehardstyle_mp3-192', 'I LOVE HARDSTYLE', 'i_love_hardstyle.png'),
    ('https://ilm.stream35.radiohost.de/ilm_ilovehiphop_mp3-192', 'I LOVE HIP HOP', 'i_love_hip_hop.png'),
    # I LOVE HIP HOP 2025
    ('https://ilm.stream35.radiohost.de/ilm_ilovehiphophistory_mp3-192', 'I LOVE HIP HOP HISTORY', 'i_love_hip_hop_history.png'),
    # I LOVE HIT-QUIZ
    # I LOVE HITS 2025
    ('https://ilm.stream18.radiohost.de/ilm_ilovehitshistory_mp3-192', 'I LOVE HITS HISTORY', 'i_love_hits_history.png'),
    ('https://ilm.stream35.radiohost.de/ilm_ilovemainstagemadness_mp3-192', 'I LOVE MAINSTAGE', 'i_love_mainstage.png'),
    # I LOVE MALLE
    ('https://ilm.stream35.radiohost.de/ilm_ilovemashup_mp3-192', 'I LOVE MASHUP', 'i_love_mashup.png'),
    ('https://ilm.stream35.radiohost.de/ilm_ilovemusicandchill_mp3-192', 'I LOVE MUSIC&CHILL', 'i_love_music_and_chill.png'),
    ('https://ilm.stream35.radiohost.de/ilm_ilovepartyhard_mp3-192', 'I LOVE PARTY HARD', 'i_love_party_hard.png'),
    # I LOVE ROCK RADIO
    # I LOVE SUGAR RADIO
    # I LOVE THE 90S
    ('https://ilm.stream35.radiohost.de/ilm_ilovethebeach_mp3-192', 'I LOVE THE BEACH', 'i_love_the_beach.png'),
    ('https://ilm.stream35.radiohost.de/ilm_ilovethesun_mp3-192', 'I LOVE THE SUN', 'i_love_the_sun.png'),
    # I LOVE TOMORROWLAND
    ('https://ilm.stream18.radiohost.de/ilm_ilovetop100charts_mp3-192', 'I LOVE THE TOP 100 CHARTS', 'i_love_the_top_100_charts.png'),
    ('https://ilm.stream18.radiohost.de/ilm_ilovetrashpop_mp3-192', 'I LOVE TRASHPOP', 'i_love_trashpop.png'),
    ('https://ilm.stream18.radiohost.de/ilm_iloveusonlyrapradio_mp3-192', 'I LOVE US ONLY RAP RADIO', 'i_love_us_only.rap.png'),
    ('https://ilm.stream35.radiohost.de/ilm_iloveworkout_mp3-192', 'I LOVE WORKOUT', 'i_love_workout.png'),
    ('https://ilm.stream35.radiohost.de/ilm_ilovexmas_mp3-192', 'I LOVE X-MAS', 'i_love_X-Mas.png')
]

def main():
    for url, title, img in STREAMS:
        add_item(url, title, img)
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

def add_item(url, title, img=''):
    item_url = build_url({'action': 'play', 'url': url})
    li = xbmcgui.ListItem(title)
    li.setInfo('music', {'title': title})
    img_path = os.path.join(ADDON.getAddonInfo('path'), 'resources', 'media', img) if img else ADDON_ICON
    li.setArt({'thumb': img_path, 'icon': img_path})
    li.setProperty('IsPlayable', 'true')
    xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=item_url, listitem=li, isFolder=False)

def play():
    params = dict(urllib.parse.parse_qsl(sys.argv[2][1:]))
    stream_url = params.get('url', STREAMS[0][0])
    li = xbmcgui.ListItem(path=stream_url)
    li.setInfo('music', {'title': "Playing Stream"})
    xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, listitem=li)

def build_url(query):
    return sys.argv[0] + '?' + urllib.parse.urlencode(query)

def router():
    params = dict(urllib.parse.parse_qsl(sys.argv[2][1:]))
    if params:
        if params['action'] == 'play':
            play()
    else:
        main()

if __name__ == '__main__':
    router()
