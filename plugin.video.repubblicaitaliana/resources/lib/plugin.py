import os
import sys
import urllib.parse
import xbmcgui
import xbmcplugin

from resources.lib.globals import G



def add_directory_item(parameters, li, folder=True):
    url = f"{sys.argv[0]}?{urllib.parse.urlencode(parameters)}"
    return xbmcplugin.addDirectoryItem(handle=G.PLUGIN_HANDLE, url=url, listitem=li, isFolder=folder)



def show_root_menu():
    """ Show the plugin root menu """

    menu_voci = [
        (32001, 'camera.jpg', 'camera'),
        (32002, 'senato.png',  'senato'),
        (32003, 'tv.png',      'tv'),
        (32004, 'radio.png',   'radio'),
    ]

    for str_id, icona, mode in menu_voci:
        titolo = f'[B]{G.LANGUAGE(str_id)}[/B]'
        li = xbmcgui.ListItem(titolo, offscreen=True)
        li.setArt({'thumb': os.path.join(G.THUMB_PATH, icona), 'fanart': G.FANART_PATH})
        add_directory_item({'mode': mode}, li)

    xbmcplugin.endOfDirectory(handle=G.PLUGIN_HANDLE, succeeded=True)



def programmi_camera():

    thumb = 'https://yt3.googleusercontent.com/hFbWr3ydEXfeoX1BS18GG7OEkXW_jNCDBhWu5sVoBAVv7fdpVUcIRKSNlRery4EbiUzQsRK39OU=s160-c-k-c0x00ffffff-no-rj'
    
    canali = [
        ('Camera - Canale Satellitare', 'BD4kcj6KspM'),
        ('Camera - Canale Assemblea', 'Cnjs83yowUM'),
    ]

    items = []
    for titolo, video_id in canali:
        link = f'plugin://plugin.video.youtube/play/?video_id={video_id}'
        li = xbmcgui.ListItem(titolo, offscreen=True)
        li.setArt({'thumb': thumb, 'fanart': G.FANART_PATH})
        li.setInfo('video', {})
        li.setProperty('isPlayable', 'true')
        items.append((link, li, False))

    xbmcplugin.addDirectoryItems(handle=G.PLUGIN_HANDLE, items=items, totalItems=len(items))
    xbmcplugin.endOfDirectory(handle=G.PLUGIN_HANDLE, succeeded=True)



def programmi_senato():

    thumb = 'https://yt3.googleusercontent.com/ytc/AIdro_kuWqJTQYB5earQtR1bMmun99HvofpjYQKNYbZdS4hNaA=s160-c-k-c0x00ffffff-no-rj'
    
    canali = [
        ('Senato - Canale 1', 'sPbVV3E737E'),
        ('Senato - Canale 2', 'WyQMW1oJpOo'),
        ('Senato - Canale 3', 'PjPRSf2oN4w'),
        ('Senato - Canale 4', 'KQPgwlDN-1E'),
        ('Senato - Canale 5', 'eIyBRC6dHoQ'),
        ('Senato - Canale 6', 'loiN1npW2MM'),
        ('Senato - Canale 7', 'c0hzsRTIbQk'),
        ('Senato - Canale 8', 'vOR7zAjorO8'),
    ]

    items = []
    for titolo, video_id in canali:
        link = f'plugin://plugin.video.youtube/play/?video_id={video_id}'
        li = xbmcgui.ListItem(titolo, offscreen=True)
        li.setArt({'thumb': thumb, 'fanart': G.FANART_PATH})
        li.setInfo('video', {})
        li.setProperty('isPlayable', 'true')
        items.append((link, li, False))

    xbmcplugin.addDirectoryItems(handle=G.PLUGIN_HANDLE, items=items, totalItems=len(items))
    xbmcplugin.endOfDirectory(handle=G.PLUGIN_HANDLE, succeeded=True)


def programmi_tv():

    canali = [
        (
            'R.Radicale TV - Camera',
            'https://video-ar.radioradicale.it/diretta/camera2/playlist.m3u8',
            'https://www.radioradicale.it/sites/all/themes/radioradicale_2014/images/audio-400.png'
        ),
        (
            'R.Radicale TV - Senato',
            'https://video-ar.radioradicale.it/diretta/senato2/playlist.m3u8',
            'https://www.radioradicale.it/sites/all/themes/radioradicale_2014/images/audio-400.png'
        ),
        (
            'R.Radicale TV',
            'https://video-ar.radioradicale.it/diretta/padtv2/playlist.m3u8',
            'https://www.radioradicale.it/sites/all/themes/radioradicale_2014/images/audio-400.png'
        ),
        (
            'RaiNews24',
            'https://8e7439fdb1694c8da3a0fd63e4dda518.msvdn.net/rainews1/hls/playlist_mo.m3u8',
            'https://www.rainews.it/dl/components/img/svg/RaiNewsBarra-logo.png'
        ),
        (
            'TgCom24',
            'https://live03-col.msf.cdn.mediaset.net/live/ch-kf/kf-clr.isml/manifest.mpd|User-Agent=HbbTV/1.6.1',
            'https://www.mimesi.com/wp-content/uploads/2017/11/tgcom24.jpg'
        ),
        (
            'SkyTg24',
            # Token expires on 22 Dec 2027
            'https://hlslive-web-gcdn-skycdn-it.akamaized.net/TACT/12221/web/master.m3u8?hdnts=st=1764666351~exp=1829466206~acl=/*~hmac=b0e9165b6c55027903ad103c8219f363d8765eb300c0d9a339e9767fc3509556',
            'https://www.motork.io/it/wp-content/uploads/sites/2/2020/02/skytg24-logo.jpg'
        ),
        (
            'IlSole24Ore TV',
            'https://ilsole24ore-radiovisual.akamaized.net/hls/live/2035302/persidera/master.m3u8',
            'https://www.ilsole24ore.tv/assets/img/logo-radio24TV.png'
        ),
        (
            'Radio24 TV',
            'https://ilsole24ore-radiovisual.akamaized.net/hls/live/2035302/stream/master.m3u8',
            'https://www.radio24.ilsole24ore.com/assets/img/splash_web-black.png'
        ),
    ]

    items = []
    for titolo, link, thumb in canali:
        li = xbmcgui.ListItem(titolo, offscreen=True)
        li.setArt({'thumb': thumb, 'fanart': G.FANART_PATH})
        li.setInfo('video', {})
        li.setProperty('isPlayable', 'true')
        items.append((link, li, False))

    xbmcplugin.addDirectoryItems(handle=G.PLUGIN_HANDLE, items=items, totalItems=len(items))
    xbmcplugin.endOfDirectory(handle=G.PLUGIN_HANDLE, succeeded=True)



def programmi_radio():

    canali = [
        (
            'R.Radicale - Camera',
            'https://live.radioradicale.it/camera.mp3',
            'https://www.radioradicale.it/sites/all/themes/radioradicale_2014/images/audio-400.png'
        ),
        (
            'R.Radicale - Senato',
            'https://live.radioradicale.it/senato.mp3',
            'https://www.radioradicale.it/sites/all/themes/radioradicale_2014/images/audio-400.png'
        ),
        (
            'RadioRadicale',
            'https://live.radioradicale.it/live.mp3',
            'https://www.radioradicale.it/sites/all/themes/radioradicale_2014/images/audio-400.png'
        ),
        (
            'RaiGRParlamento',
            'https://radioparlamento-live.akamaized.net/hls/live/2032597/radioparlamento/radioparlamento/playlist.m3u8',
            'http://db.radioline.fr/pictures/radio_994f2bf74254de17bb2c096c0cbf9e21/logo200.jpg'
        ),
        (
            'GiornaleRadio',
            'https://gr.fluidstream.eu/gr1.mp3?FLID=1',
            'https://giornaleradio.fm/wp-content/uploads/2023/03/Giornale-Radio-logo-2-1.png'
        ),
        (
            'RadioPopolare',
            'https://livex.radiopopolare.it/radiopop2',
            'https://www.radiopopolare.it/wp-content/uploads/2019/08/icon-logo@2x-1.png'
        ),
        (
            'Radio24',
            'https://ilsole24ore-radio.akamaized.net/hls/live/2035301/radio24/playlist.m3u8',
            'https://www.radio24.ilsole24ore.com/assets/img/splash_web-black.png'
        ),
    ]

    items = []
    for titolo, link, thumb in canali:
        li = xbmcgui.ListItem(titolo, offscreen=True)
        li.setArt({'thumb': thumb, 'fanart': G.FANART_PATH})
        li.setInfo('music', {})
        li.setProperty('isPlayable', 'true')
        items.append((link, li, False))

    xbmcplugin.addDirectoryItems(handle=G.PLUGIN_HANDLE, items=items, totalItems=len(items))
    xbmcplugin.endOfDirectory(handle=G.PLUGIN_HANDLE, succeeded=True)


def run(argv):
    """ Addon entry point """

    G.init_globals(argv)

    if G.MODE == "camera":
        programmi_camera()

    elif G.MODE == "senato":
        programmi_senato()

    elif G.MODE == "tv":
        programmi_tv()

    elif G.MODE == "radio":
        programmi_radio()

    else:
        show_root_menu()
