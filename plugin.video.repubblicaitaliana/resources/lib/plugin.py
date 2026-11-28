import os
import sys
import html
import json
import re
import urllib.request
import urllib.parse
import xbmcgui
import xbmcplugin

from resources.lib.globals import G



def add_directory_item(parameters, li, folder=True):
    url = f"{sys.argv[0]}?{urllib.parse.urlencode(parameters)}"
    return xbmcplugin.addDirectoryItem(handle=G.PLUGIN_HANDLE, url=url, listitem=li, isFolder=folder)



def media(nome):
    """ Full path of an image bundled in resources/media """
    return os.path.join(G.THUMB_PATH, nome)


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
        li.setArt({'thumb': media(icona), 'fanart': G.FANART_PATH})
        add_directory_item({'mode': mode}, li)

    xbmcplugin.endOfDirectory(handle=G.PLUGIN_HANDLE, succeeded=True)



# WebTV Camera
# --------------------------------------------------------------------------------
WEBTV = 'https://webtv.camera.it'
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/124.0.0.0 Safari/537.36'


def _get(url):
  try:
    req = urllib.request.Request(url, headers={'User-Agent': UA})
    with urllib.request.urlopen(req, timeout=8) as r:
      return r.read().decode('utf-8', 'ignore')
  except Exception:
    return ''


def _ch_info(ch):
  try:
    pl = json.loads(_get(f'{WEBTV}/ws/get_channel_playlist/{ch}.json'))[0]
    m = re.search(r'embed/([a-zA-Z0-9_-]{11})', pl.get('file', ''))
    return (m.group(1), pl.get('image', '')) if m else (None, '')
  except Exception:
    return None, ''


def programmi_camera():
  default_thumb = media('camera_yt.jpg')
  canali, seen = [], set()

  # 1. Canali fissi (Satellitare ch 12, Sottotitoli ch 512)
  for nome, ch in [
      ('Camera - Canale Satellitare', '12'),
      ('Camera - Sottotitoli automatici', '512'),
  ]:
    vid, img = _ch_info(ch)
    if vid and vid not in seen:
      seen.add(vid)
      canali.append((nome, vid, img))

  # 2. Dirette attive dalla home (Assemblea, Commissioni, Eventi)
  page = _get(WEBTV)
  for attrs, body in re.findall(
      r'<li\s+id="in_evidenza_\d+_container"([^>]*)>(.*?)</li>', page, re.DOTALL
  ):
    if 'data-tipo_evento="live"' not in attrs:
      continue
    yt = re.search(r'data-yotutube_id="([a-zA-Z0-9_-]{11})"', attrs)
    vid = yt.group(1) if yt else None
    if not vid:
      ch = re.search(r'data-ch_evento="(\d+)"', attrs)
      if ch:
        vid, _ = _ch_info(ch.group(1))
    if not vid or vid in seen:
      continue
    seen.add(vid)

    def clean(cls):
      m = re.search(rf'<div class="{cls}"[^>]*>(.*?)</div>', body, re.DOTALL)
      txt = (
          html.unescape(re.sub(r'<[^>]+>', ' ', m.group(1)))
          .replace('\u200b', '')
          .strip()
          if m
          else ''
      )
      return re.sub(r'\s+', ' ', txt)

    canale, titolo = clean('canale'), clean('titolo')
    label = f'{canale} - {titolo}' if canale and titolo else (titolo or canale)
    th = re.search(r'data-thumb_url="([^"]+)"', attrs)
    thumb = (
        (
            th.group(1)
            if th.group(1).startswith('http')
            else f'{WEBTV}{th.group(1)}'
        )
        if th
        else ''
    )
    canali.append((label, vid, thumb))

  items = []
  for titolo, vid, thumb in canali:
    link = f'plugin://plugin.video.youtube/play/?video_id={vid}'
    li = xbmcgui.ListItem(titolo, offscreen=True)
    li.setArt({'thumb': thumb or default_thumb, 'fanart': G.FANART_PATH})
    li.setInfo('video', {'title': titolo})
    li.setProperty('isPlayable', 'true')
    items.append((link, li, False))

  xbmcplugin.addDirectoryItems(
      handle=G.PLUGIN_HANDLE, items=items, totalItems=len(items)
  )
  xbmcplugin.endOfDirectory(handle=G.PLUGIN_HANDLE, succeeded=True)



# WebTV Senato
# --------------------------------------------------------------------------------
def programmi_senato():

    thumb = media('senato_yt.jpg')

    items = []
    for n in range(1, 9):
        link = f'https://senato-live.morescreens.com/SENATO_1_{n:03d}/playlist.m3u8'
        li = xbmcgui.ListItem(f'Senato - Canale {n}', offscreen=True)
        li.setArt({'thumb': thumb, 'fanart': G.FANART_PATH})
        li.setInfo('video', {})
        li.setProperty('isPlayable', 'true')
        items.append((link, li, False))

    xbmcplugin.addDirectoryItems(handle=G.PLUGIN_HANDLE, items=items, totalItems=len(items))
    xbmcplugin.endOfDirectory(handle=G.PLUGIN_HANDLE, succeeded=True)



# Programmi TV
# --------------------------------------------------------------------------------
def programmi_tv():

    canali = [
        (
            'R.Radicale TV - Camera',
            'https://video-ar.radioradicale.it/diretta/camera2/playlist.m3u8',
            media('radioradicale.png')
        ),
        (
            'R.Radicale TV - Senato',
            'https://video-ar.radioradicale.it/diretta/senato2/playlist.m3u8',
            media('radioradicale.png')
        ),
        (
            'R.Radicale TV',
            'https://video-ar.radioradicale.it/diretta/padtv2/playlist.m3u8',
            media('radioradicale.png')
        ),
        (
            'RaiNews24',
            'https://mediapolis.rai.it/relinker/relinkerServlet.htm?cont=1&output=16',
            media('rainews24.png')
        ),
        (
            'TgCom24',
            'https://d3k8wzt41aflvx.cloudfront.net/TGCOM24/Live.m3u8',
            media('tgcom24.jpg')
        ),
        (
            'SkyTg24',
            # Token expires on 22 Dec 2027
            'https://hlslive-web-gcdn-skycdn-it.akamaized.net/TACT/12221/web/master.m3u8?hdnts=st=1764666351~exp=1829466206~acl=/*~hmac=b0e9165b6c55027903ad103c8219f363d8765eb300c0d9a339e9767fc3509556',
            media('skytg24.jpg')
        ),
        (
            'IlSole24Ore TV',
            'https://ilsole24ore-radiovisual.akamaized.net/hls/live/2035302/persidera/master.m3u8',
            media('ilsole24ore_tv.png')
        ),
        (
            'Radio24 TV',
            'https://ilsole24ore-radiovisual.akamaized.net/hls/live/2035302/stream/master.m3u8',
            media('radio24.png')
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



# Programmi Radio
# --------------------------------------------------------------------------------
def programmi_radio():

    canali = [
        (
            'R.Radicale - Camera',
            'https://live.radioradicale.it/camera.mp3',
            media('radioradicale.png')
        ),
        (
            'R.Radicale - Senato',
            'https://live.radioradicale.it/senato.mp3',
            media('radioradicale.png')
        ),
        (
            'RadioRadicale',
            'https://live.radioradicale.it/live.mp3',
            media('radioradicale.png')
        ),
        (
            'RaiGRParlamento',
            'https://radioparlamento-live.akamaized.net/hls/live/2032597/radioparlamento/radioparlamento/playlist.m3u8',
            media('raigr.jpg')
        ),
        (
            'GiornaleRadio',
            'https://gr.fluidstream.eu/gr1.mp3?FLID=1',
            media('giornaleradio.png')
        ),
        (
            'RadioPopolare',
            'https://livex.radiopopolare.it/radiopop2',
            media('radiopopolare.png')
        ),
        (
            'Radio24',
            'https://ilsole24ore-radio.akamaized.net/hls/live/2035301/radio24/playlist.m3u8',
            media('radio24.png')
        ),
    ]

    items = []
    for titolo, link, thumb in canali:
        li = xbmcgui.ListItem(titolo, offscreen=True)
        li.setArt({'thumb': thumb, 'fanart': G.FANART_PATH})
        li.setInfo('video', {
            'title': titolo,
            'plot': f'{titolo}\nDiretta radio',
            'mediatype': 'video',
        })
        li.setProperty('isPlayable', 'true')
        items.append((link, li, False))

    xbmcplugin.setContent(G.PLUGIN_HANDLE, 'episodes')
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
