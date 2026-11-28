import base64
import json
import os
import time
import re
import datetime
import inputstreamhelper
from html import unescape
from email.utils import parsedate
import xml.etree.ElementTree as ET

import urllib.parse
from urllib.request import Request, urlopen

import xbmc
import xbmcgui
import xbmcplugin

from bs4 import BeautifulSoup
from resources.lib.globals import G


def show_root_menu():
    """ Show the plugin root menu """
    li_style = xbmcgui.ListItem('[B]' + G.LANGUAGE(32002) + '[/B]', offscreen=True)
    li_style.setArt({'thumb': os.path.join(G.THUMB_PATH, 'direttalivela7.jpg'), 'fanart': G.FANART_PATH})
    add_directory_item_nodup({"mode": "diretta_la7"}, li_style, folder=False, is_live=True)
    li_style = xbmcgui.ListItem('[B]' + G.LANGUAGE(32009) + '[/B]', offscreen=True)
    li_style.setArt({'thumb': os.path.join(G.THUMB_PATH, 'direttalivela7cinema.jpg'), 'fanart': G.FANART_PATH})
    add_directory_item_nodup({"mode": "diretta_la7cinema"}, li_style, folder=False, is_live=True)
    li_style = xbmcgui.ListItem('[B]' + G.LANGUAGE(32001) + '[/B]', offscreen=True)
    li_style.setArt({'thumb': os.path.join(G.THUMB_PATH, 'rivedila7.jpg'), 'fanart': G.FANART_PATH})
    add_directory_item_nodup({"mode": "rivedi_la7"}, li_style)
    li_style = xbmcgui.ListItem('[B]' + G.LANGUAGE(32004) + '[/B]', offscreen=True)
    li_style.setArt({'thumb': os.path.join(G.THUMB_PATH, 'direttalivela7cinema.jpg'), 'fanart': G.FANART_PATH})
    add_directory_item_nodup({"mode": "rivedi_la7cinema"}, li_style)
    li_style = xbmcgui.ListItem('[B]' + G.LANGUAGE(32007) + '[/B]', offscreen=True)
    li_style.setArt({'thumb': os.path.join(G.THUMB_PATH, 'tgmeteo.jpg'), 'fanart': G.FANART_PATH})
    add_directory_item_nodup({"mode": "tg_meteo"}, li_style)
    li_style = xbmcgui.ListItem('[B]' + G.LANGUAGE(32006) + '[/B]', offscreen=True)
    li_style.setArt({'thumb': os.path.join(G.THUMB_PATH, 'programmi.jpg'), 'fanart': G.FANART_PATH})
    add_directory_item_nodup({"mode": "tutti_programmi"}, li_style)
    li_style = xbmcgui.ListItem('[B]' + G.LANGUAGE(32010) + '[/B]', offscreen=True)
    li_style.setArt({'thumb': os.path.join(G.THUMB_PATH, 'film.jpg'), 'fanart': G.FANART_PATH})
    add_directory_item_nodup({"mode": "film"}, li_style)
    li_style = xbmcgui.ListItem('[B]' + G.LANGUAGE(32020) + '[/B]', offscreen=True)
    li_style.setArt({'thumb': os.path.join(G.THUMB_PATH, 'documentari.jpg'), 'fanart': G.FANART_PATH})
    add_directory_item_nodup({"mode": "documentari"}, li_style)
    li_style = xbmcgui.ListItem('[B]' + G.LANGUAGE(32008) + '[/B]', offscreen=True)
    li_style.setArt({'thumb': os.path.join(G.THUMB_PATH, 'podcast.jpg'), 'fanart': G.FANART_PATH})
    add_directory_item_nodup({"mode": "podcast"}, li_style)
    li_style = xbmcgui.ListItem('[B]' + G.LANGUAGE(32012) + '[/B]', offscreen=True)
    li_style.setArt({'thumb': os.path.join(G.THUMB_PATH, 'cerca.jpg'), 'fanart': G.FANART_PATH})
    add_directory_item_nodup({"mode": "cerca_la7"}, li_style, folder=False)

    xbmcplugin.endOfDirectory(handle=G.PLUGIN_HANDLE, succeeded=True)


def add_directory_item_nodup(parameters, li, title='', folder=True, is_live=False):
    if not title:
        title = G.TITOLO
    if title in G.LIST_PROGRAMMI:
        # xbmc.log('PROGRAMMA DUPLICATO', xbmc.LOGINFO)
        pass
    else:
        url = G.PLUGIN_URL + '?' + urllib.parse.urlencode(parameters)
        if is_live:
            url += '&_l=.pvr'  # disabilita per le dirette la richiesta di riprendere il video dall'ultima volta
        # xbmc.log('LIST------: '+str(url),xbmc.LOGINFO)
        if not folder:
            li.setInfo('video', {})
            li.setProperty('isPlayable', 'true')
        return xbmcplugin.addDirectoryItem(handle=G.PLUGIN_HANDLE, url=url, listitem=li, isFolder=folder)


def get_html(url):
    req = Request(url, headers={'user-agent': G.HEADERS_SET['user-agent']})
    return urlopen(req).read().decode(errors='replace')


def next_flight_data(html):
    # le pagine di la7play.it (Next.js) contengono i dati in blocchi self.__next_f.push([1,"..."])
    data = ''
    for m in re.finditer(r'self\.__next_f\.push\(\[1,"((?:[^"\\]|\\.)*)"\]\)', html):
        data += json.loads('"' + m.group(1) + '"')
    return data


def json_object_at(text, marker):
    # decodifica l'oggetto JSON che inizia con marker (o subito dopo, se marker e' una chiave)
    pos = text.find(marker)
    if pos < 0:
        return None
    if not marker.startswith('{'):
        pos = text.find('{', pos + len(marker))
    return json.JSONDecoder().raw_decode(text, pos)[0]


def json_string(text, key):
    # primo valore stringa (non null) della chiave nel payload
    m = re.search(r'"%s":"((?:[^"\\]|\\.)*)"' % key, text)
    return json.loads('"' + m.group(1) + '"') if m else ''


def guida_tv(url):
    # guida tv di la7play.it: lista di giorni, ognuno con la sua lista di programmi
    data = json_object_at(next_flight_data(get_html(url)), '{"@attributes":{"canale"')
    giorni = data.get('giorno', []) if data else []
    if isinstance(giorni, dict):
        giorni = [giorni]
    return giorni


def programmi_giorno(giorno):
    programmi = giorno.get('programma', [])
    if isinstance(programmi, dict):
        programmi = [programmi]
    return programmi


def titolo_in_onda(url_guida):
    adesso = time.time()
    try:
        for giorno in guida_tv(url_guida):
            for programma in programmi_giorno(giorno):
                inizio = int(programma['timestamp'])
                if inizio <= adesso < inizio + int(programma['durata']):
                    return programma['titolo']
    except Exception as e:
        xbmc.log('EXCEP TITOLO IN ONDA: ' + str(e), xbmc.LOGINFO)
    return ''


def get_drm_token(endpoint, content_id, content_type):
    headers_tok = {
        'user-agent': G.HEADERS_SET['user-agent'],
        'accept': G.HEADERS_SET['accept'],
        'accept-language': G.HEADERS_SET['accept-language'],
        'origin': G.HEADERS_SET['origin'],
        'referer': G.HEADERS_SET['referer'],
    }
    params = urllib.parse.urlencode({'id': content_id, 'contentType': content_type, 'v': str(int(time.time() * 1000))})
    response = json.loads(urlopen(Request((endpoint or G.URL_DRM_TOKEN) + '?' + params, headers=headers_tok)).read().decode())
    return response.get('preAuthToken') or response.get('token') or response.get('auth')


def play_drm(mpdurl, pre_auth_token, titolo='', plot=''):
    headers_lic = {
        'host': G.HEADERS_SET['host_license'],
        'user-agent': G.HEADERS_SET['user-agent'],
        'accept': G.HEADERS_SET['accept'],
        'accept-language': G.HEADERS_SET['accept-language'],
        'preAuthorization': pre_auth_token,
        'origin': G.HEADERS_SET['origin'],
        'referer': G.HEADERS_SET['referer'],
    }
    pre_lic = '&'.join(['%s=%s' % (name, value) for (name, value) in headers_lic.items()])
    # xbmc.log('LICENSE1------: '+str(pre_lic),xbmc.LOGINFO)

    tsatmp = str(int(time.time()))
    license_url = G.KEY_WIDEVINE + '?d=%s' % tsatmp
    lic_url = '%s|%s|R{SSM}|' % (license_url, pre_lic)
    # xbmc.log('LICENSE2------: '+str(lic_url),xbmc.LOGINFO)
    is_helper = inputstreamhelper.Helper(G.DRM_PROTOCOL, drm=G.DRM)
    if is_helper.check_inputstream():
        listitem = xbmcgui.ListItem(offscreen=True)
        listitem.setPath(mpdurl)
        if titolo:
            listitem.setInfo('video', {'plot': plot or titolo, 'title': titolo})
        listitem.setProperty("inputstream", is_helper.inputstream_addon)
        listitem.setProperty("inputstream.adaptive.manifest_type", G.DRM_PROTOCOL)
        listitem.setProperty("inputstream.adaptive.license_type", G.DRM)
        listitem.setProperty("inputstream.adaptive.license_key", lic_url)
        listitem.setMimeType('application/dash+xml')
        xbmcplugin.setResolvedUrl(G.PLUGIN_HANDLE, True, listitem)
    else:
        xbmcplugin.endOfDirectory(G.PLUGIN_HANDLE, succeeded=False)


def play_dirette(url):
    xbmc.log('PLAY DIRETTE', xbmc.LOGINFO)
    #xbmc.log('PAGE DIRETTE-----: '+str(url),xbmc.LOGINFO)

    try:
        player = next_flight_data(get_html(url))
        # "mainLiveUrl": "<dash .mpd>|<hls .m3u8>"
        mpdurl = json_string(player, 'mainLiveUrl').split('|')[0].strip()
        pre_auth_token = get_drm_token(json_string(player, 'drmTokenEndpoint'), json_string(player, 'drmContentId'), 'LIVE')
    except Exception as e:
        xbmc.log('EXCEP DIRETTA: ' + str(e), xbmc.LOGINFO)
        mpdurl = ''
        pre_auth_token = ''
    #xbmc.log('URL VIDEO MPD-----: '+str(mpdurl),xbmc.LOGINFO)
    if not mpdurl or not pre_auth_token:
        xbmcgui.Dialog().ok(G.PLUGIN_NAME, G.LANGUAGE(32005))
        xbmcplugin.setResolvedUrl(G.PLUGIN_HANDLE, False, xbmcgui.ListItem(offscreen=True))
        return

    titolo_diretta = ''
    if url == G.URL_LIVE_LA7:
        titolo_diretta = titolo_in_onda(G.URL_RIVEDILA7)
    elif url == G.URL_LIVE_LA7CINEMA:
        titolo_diretta = titolo_in_onda(G.URL_RIVEDILA7CINEMA)

    play_drm(mpdurl, pre_auth_token, titolo_diretta)


def play_video_la7play(html):
    # pagina video di la7play.it: i dati del file sono in "uploadVideo"
    player = next_flight_data(html)
    video = json_object_at(player, '"uploadVideo":')
    if not video or not video.get('cf_remote_url'):
        return ''
    remote_url = video['cf_remote_url']
    drm = re.search(r'"drm":(true|false)', player)
    if drm and drm.group(1) == 'true' and '"abilitaDrm":true' in player:
        nome = remote_url.lstrip('/').split('/')[-1]
        mpdurl = json_string(player, 'hostnameCdnDrm').rstrip('/') + '/' + nome + '/DASH/' + nome + '.mpd'
        pre_auth_token = get_drm_token(json_string(player, 'drmTokenEndpoint'), json_string(player, 'drmContentId'), 'VOD')
        play_drm(mpdurl, pre_auth_token, G.TITOLO, G.PLOT)
        return None

    # stesso schema del player del sito: <cdn>/local/hls/,<file1>,<file2>,.mp4.urlset/master.m3u8
    cdn = (json_string(player, 'hostnameCdn') or G.URL_CDN_VOD).rstrip('/')
    files = (remote_url if remote_url.startswith('/') else '/' + remote_url).replace('.mp4', '')
    if not video.get('cf_old_entry_id'):
        nk = []
        for f in files.split(','):
            f = f.strip()
            if f and not f.startswith('/nk/'):
                f = '/nk' + f if f.startswith('/') else '/nk/' + f
            nk.append(f)
        files = ','.join(nk)
    return cdn + '/local/hls/,' + files + ',.mp4.urlset/master.m3u8'


def descrizione_pagina(html):
    # trama della pagina video di la7play.it (meta og:description)
    m = re.search(r'<meta property="og:description" content="([^"]*)"', html)
    return unescape(m.group(1)).strip() if m else ''


def play_video(page_video):
    xbmc.log('PLAY VIDEO', xbmc.LOGINFO)

    req = Request(page_video, headers={'user-agent': G.HEADERS_SET['user-agent']})
    html = urlopen(req).read().decode('utf-8', errors='ignore')
    if not G.PLOT:
        G.PLOT = descrizione_pagina(html)
    if 'self.__next_f.push' in html:
        link_video = play_video_la7play(html)
        if link_video is None:
            return
    else:
        # pagine del vecchio formato (TG Digital su tg.la7.it)
        match = re.findall(r'\.net/i/.*?content/(.*?)(?:\.mp4)', html)
        if match:
            link_video = 'https://awsvodpkg.iltrovatore.it/local/hls/,/content/' + match[0] + '.mp4.urlset/master.m3u8'
        else:
            match = re.findall('m3u8: "(.*?)"', html)
            link_video = match[0] if match else ''

    listitem = xbmcgui.ListItem(G.TITOLO, offscreen=True)
    listitem.setInfo('video', {'Title': G.TITOLO})
    if G.THUMB != "":
        listitem.setArt({'thumb': G.THUMB})
    listitem.setInfo('video', {'plot': G.PLOT})
    if link_video == '':
        xbmc.log('RivediLA7: NO VIDEO LINK', xbmc.LOGINFO)
        xbmcgui.Dialog().ok(G.PLUGIN_NAME, G.LANGUAGE(32005))
        xbmcplugin.setResolvedUrl(G.PLUGIN_HANDLE, False, listitem)
        return
    if '.m3u8' in link_video:
        listitem.setProperty('inputstream', 'inputstream.adaptive')
        listitem.setProperty('inputstream.adaptive.manifest_type', 'hls')

    listitem.setPath(link_video)
    xbmcplugin.setResolvedUrl(G.PLUGIN_HANDLE, True, listitem)


def rivedi(url, thumb):
    giorni = guida_tv(url)
    # xbmc.log('GIORNO----------: '+str(giorni),xbmc.LOGINFO)
    for giorno in reversed(giorni):
        # i giorni futuri della guida non hanno ancora video da rivedere
        if not any(p.get('pathname') for p in programmi_giorno(giorno)):
            continue
        data = giorno['@attributes']['data']
        giorno_num, mese, anno = [int(x) for x in data.split('-')]
        date_row_week = xbmc.getLocalizedString(11 + datetime.date(anno, mese, giorno_num).weekday())
        liStyle = xbmcgui.ListItem(date_row_week + " " + str(giorno_num) + " " + xbmc.getLocalizedString(20 + mese), offscreen=True)
        liStyle.setArt({'thumb': os.path.join(G.THUMB_PATH, thumb), 'fanart': G.FANART_PATH})
        add_directory_item_nodup({"mode": G.MODE, "giorno": data}, liStyle)
    xbmcplugin.endOfDirectory(handle=G.PLUGIN_HANDLE, succeeded=True)


def rivedi_giorno(url):
    for giorno in guida_tv(url):
        if giorno['@attributes']['data'] != G.GIORNO:
            continue
        for programma in programmi_giorno(giorno):
            if not programma.get('pathname'):
                continue
            orario = programma.get('ora', '')
            nome = programma.get('titolo', '').strip()
            thumb = programma.get('immagine_scena') or programma.get('immagine_programma') or ''
            plot = programma.get('sinossi', '').strip()
            urll = G.URL_BASE_LA7PLAY + programma['pathname']
            # xbmc.log('------LINK------: '+str(urll),xbmc.LOGINFO)
            liStyle = xbmcgui.ListItem(orario + " " + nome, offscreen=True)
            liStyle.setArt({'thumb': thumb, 'fanart': G.FANART_PATH})
            liStyle.setInfo('video', {'plot': plot})
            liStyle.setProperty('isPlayable', 'true')
            url2 = G.PLUGIN_URL + '?' + urllib.parse.urlencode({"mode": G.MODE, "play": urll, "titolo": nome, "thumb": thumb, "plot": plot})
            xbmcplugin.addDirectoryItem(handle=G.PLUGIN_HANDLE, url=url2, listitem=liStyle, isFolder=False)

    xbmcplugin.setContent(G.PLUGIN_HANDLE, 'episodes')
    xbmcplugin.endOfDirectory(handle=G.PLUGIN_HANDLE, succeeded=True)


def gql_query(query_hash, variables=None, base=None):
    # API GraphQL di la7play.it (query persistite): /api/gql/<hash>/<variabili JSON in base64url>
    url = (base or G.URL_GQL) + query_hash
    if variables:
        js = json.dumps(variables, sort_keys=True, separators=(',', ':'), ensure_ascii=False)
        url += '/' + base64.urlsafe_b64encode(js.encode('utf8')).decode().rstrip('=')
    req = Request(url, headers={'user-agent': G.HEADERS_SET['user-agent'], 'accept': 'application/json'})
    return json.loads(urlopen(req).read().decode()).get('data') or {}


def programmi_lettera():
    data = gql_query(G.GQL_TUTTI_PROGRAMMI)
    programmi = (data.get('graphqlTuttiProgrammi') or {}).get('results') or []

    for programma in programmi:
        if not programma.get('properti'):
            continue
        titolo = programma.get('titolo', '').strip()
        liStyle = xbmcgui.ListItem(titolo, offscreen=True)
        thumb = (programma.get('img') or '').split('||')[0]
        if thumb:
            # stessa immagine in versione verticale (la misura e' nell'URL)
            thumb = thumb.replace('/img/1280x720.', '/img/600x800.')
            liStyle.setArt({'thumb': thumb, 'poster': thumb})
        liStyle.setArt({'fanart': G.FANART_PATH})
        plot = unescape(re.sub(r'<[^>]+>', '', programma.get('occhiello') or '')).strip()
        liStyle.setInfo('video', {'plot': plot})
        # le puntate si filtrano per nome della property in minuscolo
        add_directory_item_nodup({"mode": G.MODE, "link": programma['properti'].lower()}, liStyle, titolo)
        G.LIST_PROGRAMMI.append(titolo)

    xbmcplugin.addSortMethod(G.PLUGIN_HANDLE, xbmcplugin.SORT_METHOD_LABEL_IGNORE_FOLDERS)
    xbmcplugin.setContent(G.PLUGIN_HANDLE, 'tvshows')
    xbmcplugin.endOfDirectory(handle=G.PLUGIN_HANDLE, succeeded=True)


def podcast_serie():
    # elenco delle serie: schede PodcastSeries della pagina /podcast di la7play.it
    html = get_html(G.URL_PODCAST)
    trovati = []
    for m in re.finditer(r'\{"@type":"PodcastSeries"', html):
        serie = json.JSONDecoder().raw_decode(html, m.start())[0]
        # gli episodi non sono sul sito: il feed RSS si ricava dal link Apple Podcasts della serie
        apple = re.search(r'podcasts\.apple\.com/\S*/id(\d+)', ' '.join(serie.get('sameAs') or []))
        if not apple or apple.group(1) in trovati:
            continue
        trovati.append(apple.group(1))
        titolo = (serie.get('name') or '').strip()
        thumb = (serie.get('image') or {}).get('url') or ''
        liStyle = xbmcgui.ListItem(titolo, offscreen=True)
        liStyle.setArt({'thumb': thumb, 'poster': thumb, 'fanart': G.FANART_PATH})
        liStyle.setInfo('video', {'plot': (serie.get('description') or '').strip()})
        add_directory_item_nodup({"mode": G.MODE, "link": apple.group(1)}, liStyle, titolo)

    xbmcplugin.endOfDirectory(handle=G.PLUGIN_HANDLE, succeeded=True)


def podcast_leggi_feed(apple_id):
    # legge dal feed solo gli episodi della pagina corrente: alcuni feed hanno migliaia di episodi
    itunes = '{http://www.itunes.com/dtds/podcast-1.0.dtd}'
    feed = json.loads(get_html(G.URL_PODCAST_LOOKUP + apple_id))['results'][0]['feedUrl']
    inizio = G.PAGENUM * G.PODCAST_PER_PAGINA
    episodi = []
    thumb_serie = ''
    n = 0
    req = Request(feed, headers={'user-agent': G.HEADERS_SET['user-agent']})
    with urlopen(req) as response:
        for _, elem in ET.iterparse(response):
            if elem.tag == itunes + 'image' and not thumb_serie:
                thumb_serie = elem.get('href') or ''
            if elem.tag != 'item':
                continue
            n += 1
            if n > inizio + G.PODCAST_PER_PAGINA:
                return episodi, True
            if n > inizio:
                enclosure = elem.find('enclosure')
                immagine = elem.find(itunes + 'image')
                episodi.append({
                    'titolo': (elem.findtext('title') or '').strip(),
                    'url': enclosure.get('url') if enclosure is not None else '',
                    'data': parsedate(elem.findtext('pubDate') or ''),
                    'durata': elem.findtext(itunes + 'duration') or '',
                    'plot': elem.findtext(itunes + 'summary') or elem.findtext('description') or '',
                    'thumb': (immagine.get('href') if immagine is not None else '') or thumb_serie,
                })
            elem.clear()
    return episodi, False


def podcast_episodi():
    try:
        episodi, altre_pagine = podcast_leggi_feed(G.LINK)
    except Exception as e:
        xbmc.log('EXCEP PODCAST: ' + str(e), xbmc.LOGINFO)
        xbmcgui.Dialog().ok(G.PLUGIN_NAME, G.LANGUAGE(32005))
        xbmcplugin.endOfDirectory(handle=G.PLUGIN_HANDLE, succeeded=False)
        return

    for episodio in episodi:
        if not episodio['url']:
            continue
        data = '[I] - (' + time.strftime('%d.%m.%Y', episodio['data']) + ')[/I]' if episodio['data'] else ''
        titolo = episodio['titolo'] + data
        # durata in secondi oppure hh:mm:ss
        durata = 0
        if re.fullmatch(r'[\d:]+', episodio['durata']):
            for valore in episodio['durata'].split(':'):
                durata = durata * 60 + int(valore or 0)
        plot = unescape(re.sub(r'<[^>]+>', '', episodio['plot']))
        # il feed aggiunge a ogni descrizione questa frase pubblicitaria
        plot = re.sub(r'Learn more about your ad choices.*', '', plot, flags=re.S).strip()
        liStyle = xbmcgui.ListItem(titolo, offscreen=True)
        liStyle.setArt({'thumb': episodio['thumb'], 'fanart': G.FANART_PATH})
        liStyle.setInfo('video', {'plot': plot, 'duration': durata})
        add_directory_item_nodup({"mode": G.MODE, "play": episodio['url'], "titolo": titolo, "thumb": episodio['thumb']}, liStyle, titolo, folder=False)

    pagenext(altre_pagine)

    xbmcplugin.setContent(G.PLUGIN_HANDLE, 'episodes')
    xbmcplugin.endOfDirectory(handle=G.PLUGIN_HANDLE, succeeded=True)


def play_podcast():
    listitem = xbmcgui.ListItem(G.TITOLO, offscreen=True)
    listitem.setInfo('video', {'Title': G.TITOLO})
    if G.THUMB != "":
        listitem.setArt({'thumb': G.THUMB})
    listitem.setMimeType('audio/mpeg')
    listitem.setContentLookup(False)
    listitem.setPath(G.PLAY)
    xbmcplugin.setResolvedUrl(G.PLUGIN_HANDLE, True, listitem)


def programmi_lettera_tg_meteo():
    # link = nome della property su la7play.it (vedi video_programma_la7play)
    titolo = 'TG LA7'
    liStyle = xbmcgui.ListItem(titolo, offscreen=True)
    link = 'tgla7'
    thumb = os.path.join(G.THUMB_PATH, 'tgla7.jpg')
    liStyle.setArt({'thumb': thumb, 'fanart': G.FANART_PATH})
    add_directory_item_nodup({"mode": G.MODE, "link": link}, liStyle, titolo)

    titolo = 'TG Digital'
    liStyle = xbmcgui.ListItem(titolo, offscreen=True)
    link = G.URL_TGDIGITAL
    thumb = os.path.join(G.THUMB_PATH, 'tgdigital.jpg')
    liStyle.setArt({'thumb': thumb, 'fanart': G.FANART_PATH})
    add_directory_item_nodup({"mode": G.MODE, "link": link}, liStyle, titolo)

    titolo = 'Omnibus Meteo'
    liStyle = xbmcgui.ListItem(titolo, offscreen=True)
    link = 'omnibus meteo'
    thumb = os.path.join(G.THUMB_PATH, 'omnibusmeteo.jpg')
    liStyle.setArt({'thumb': thumb, 'fanart': G.FANART_PATH})
    add_directory_item_nodup({"mode": G.MODE, "link": link}, liStyle, titolo)

    xbmcplugin.endOfDirectory(handle=G.PLUGIN_HANDLE, succeeded=True)


def cerca_la7():
    testo = G.LINK

    # voce del menu (azione): tastiera e poi apertura dei risultati con indirizzo completo
    if not testo:
        tastiera = xbmcgui.Dialog()
        testo = tastiera.input(G.LANGUAGE(32015), type=xbmcgui.INPUT_ALPHANUM)
        xbmcplugin.setResolvedUrl(G.PLUGIN_HANDLE, False, xbmcgui.ListItem(offscreen=True))  # niente da riprodurre
        if testo:
            xbmc.executebuiltin('Container.Update(%s)' % (G.PLUGIN_URL + '?' + urllib.parse.urlencode({'mode': 'cerca_la7', 'link': testo})))
        return

    # API di ricerca di la7play.it: i programmi solo nella prima pagina, i video paginati a 20 alla volta
    hits, altre_pagine = [], False
    try:
        for tipo in (('property', 'video') if G.PAGENUM == 0 else ('video',)):
            data = gql_query(G.GQL_SEARCH, {'q': testo, 'page': G.PAGENUM + 1, 'pageSize': 20, 'filters': {'contentTypes': [tipo]}}, G.URL_GQL_SEARCH).get('siteSearch') or {}
            for group in data.get('groups') or []:
                if group.get('contentType') == tipo:
                    hits += group.get('hits') or []
            if tipo == 'video':
                altre_pagine = data.get('page', 1) < data.get('totalPages', 1)
    except Exception as e:
        xbmc.log(f'ERRORE RICERCA LA7: {str(e)}', xbmc.LOGERROR)
        xbmcplugin.endOfDirectory(handle=G.PLUGIN_HANDLE, succeeded=False)
        return

    # Se non trova risultati: notifica, torna indietro e rilancia la voce "Cerca" (riapre la tastiera)
    if not hits:
        xbmcgui.Dialog().notification(G.LANGUAGE(32012), G.LANGUAGE(32016), xbmcgui.NOTIFICATION_INFO, 3000)
        xbmcplugin.endOfDirectory(handle=G.PLUGIN_HANDLE, succeeded=False)
        xbmc.executebuiltin('RunPlugin(%s)' % (G.PLUGIN_URL + '?mode=cerca_la7'))
        return

    for hit in hits:
        if not hit.get('url'):
            continue
        titolo = (hit.get('title') or '').strip() or G.LANGUAGE(32017)
        thumb = hit.get('imageUrl') or ''
        plot = (hit.get('excerpt') or '').strip()

        # Programmi: aprono l'elenco delle puntate (vedi video_programma_la7play)
        if hit.get('contentType') == 'property':
            label = '[B]' + titolo + '[/B]'
            liStyle = xbmcgui.ListItem(label, offscreen=True)
            liStyle.setArt({'thumb': thumb, 'poster': thumb, 'fanart': G.FANART_PATH})
            liStyle.setInfo('video', {'plot': plot})
            add_directory_item_nodup({"mode": "tutti_programmi", "link": titolo.lower()}, liStyle, label)
            continue

        programma = (hit.get('propertyName') or '').strip()
        data_str = ''
        if hit.get('publishedAt'):
            data_str = '.'.join(reversed(hit['publishedAt'][:10].split('-')))
        label = f"[{data_str}] {titolo}" if data_str else titolo
        if programma and programma.lower() not in titolo.lower():
            label += ' - ' + programma

        liStyle = xbmcgui.ListItem(label, offscreen=True)
        video_info_tag = liStyle.getVideoInfoTag()
        video_info_tag.setTitle(label)
        video_info_tag.setPlot(plot or f"{programma} - {data_str}".strip(" -"))
        if hit.get('duration'):
            video_info_tag.setDuration(int(hit['duration']))
        if thumb:
            liStyle.setArt({'thumb': thumb, 'poster': thumb})
        liStyle.setArt({'fanart': G.FANART_PATH})

        add_directory_item_nodup({"mode": "cerca_la7", "play": G.URL_BASE_LA7PLAY + hit['url']}, liStyle, label, folder=False)

    pagenext(altre_pagine)
    xbmcplugin.setContent(G.PLUGIN_HANDLE, 'episodes')
    xbmcplugin.endOfDirectory(handle=G.PLUGIN_HANDLE, succeeded=True)


# PUNTATE DI UN PROGRAMMA su la7play.it, G.LINK = nome della property (es. "otto e mezzo")
def video_programma_la7play():
    data = gql_query(G.GQL_PUNTATE, {'property': G.LINK, 'page': G.PAGENUM + 1, 'pageSize': 20, 'stagione': None, 'sortDirection': 'DESC'})
    listing = data.get('filteredNodeReplicasListing') or {}
    puntate = listing.get('nodes') or []
    for puntata in puntate:
        if not puntata.get('path'):
            continue
        titolo = (puntata.get('title') or '').strip()
        timestamp = (puntata.get('dataMessaInOnda') or puntata.get('created') or {}).get('timestamp')
        data_puntata = '[I] - (' + time.strftime('%d.%m.%Y %H:%M', time.localtime(timestamp)) + ')[/I]' if timestamp else ''
        video = puntata.get('uploadVideo') or {}
        thumb = (video.get('thumbnailDefault') or {}).get('url') or video.get('cf_thumbnail_url') or ''
        link = G.URL_BASE_LA7PLAY + puntata['path']
        liStyle = xbmcgui.ListItem(titolo + data_puntata, offscreen=True)
        liStyle.setArt({'thumb': thumb, 'fanart': G.FANART_PATH})
        liStyle.setInfo('video', {'plot': '[B]' + titolo + '[/B]'})
        add_directory_item_nodup({"mode": G.MODE, "play": link, "titolo": titolo + data_puntata, "thumb": thumb}, liStyle, titolo + data_puntata, folder=False)

    if not puntate and G.PAGENUM == 0:
        xbmcgui.Dialog().ok(G.PLUGIN_NAME, G.LANGUAGE(32005))
    pagenext((listing.get('pageInfo') or {}).get('hasNextPage'))

    xbmcplugin.setContent(G.PLUGIN_HANDLE, 'episodes')
    xbmcplugin.endOfDirectory(handle=G.PLUGIN_HANDLE, succeeded=True)


# FILM su la7play.it (contenuti NodeEventoSingolo nella pagina)
def timestamp_film(film):
    # chiave di ordinamento: data di messa in onda, altrimenti di creazione
    return (film.get('dataMessaInOnda') or film.get('created') or {}).get('timestamp') or 0


def chiudi_elenco_film():
    # l'ordine di default e' quello di inserimento (piu' recenti in alto); alfabetico e data restano scelte possibili
    xbmcplugin.addSortMethod(G.PLUGIN_HANDLE, xbmcplugin.SORT_METHOD_UNSORTED)
    xbmcplugin.addSortMethod(G.PLUGIN_HANDLE, xbmcplugin.SORT_METHOD_LABEL_IGNORE_FOLDERS)
    xbmcplugin.addSortMethod(G.PLUGIN_HANDLE, xbmcplugin.SORT_METHOD_DATE)
    xbmcplugin.setContent(G.PLUGIN_HANDLE, 'movies')
    xbmcplugin.endOfDirectory(handle=G.PLUGIN_HANDLE, succeeded=True)


def aggiungi_film(film, serie='', mostra_in_onda=True):
    # elemento riproducibile di un film o documentario singolo (titolo, date, plot nel pannello)
    titolo = (film.get('title') or '').strip()
    if serie and serie.lower() not in titolo.lower():
        titolo = serie + ' - ' + titolo  # es. "La furia e il frastuono - St. 1 Episodio 3"
    video = film.get('uploadVideo') or {}
    thumb = (video.get('cf_thumbnail_cover') or {}).get('url') or (video.get('thumbnailDefault') or {}).get('url') or ''
    link = G.URL_BASE_LA7PLAY + film['path']
    timestamp = (film.get('dataMessaInOnda') or film.get('created') or {}).get('timestamp')
    data = time.strftime('%d.%m.%Y', time.localtime(timestamp)) if timestamp else ''
    # testo del pannello informazioni dell'elenco: titolo e le due date
    righe = ['[B]' + titolo + '[/B]']
    ts = (film.get('dataMessaInOnda') or {}).get('timestamp')
    if ts and mostra_in_onda:
        righe.append(G.LANGUAGE(32013) + ': ' + time.strftime('%d.%m.%Y - %H:%M', time.localtime(ts)))
    liStyle = xbmcgui.ListItem(titolo + ('[I] - (' + data + ')[/I]' if data else ''), offscreen=True)
    liStyle.setArt({'thumb': thumb, 'poster': thumb, 'fanart': G.FANART_PATH})
    liStyle.setInfo('video', {'plot': '\n'.join(righe)})
    if data:
        liStyle.setInfo('video', {'date': data})
    add_directory_item_nodup({"mode": G.MODE, "play": link, "titolo": titolo, "thumb": thumb}, liStyle, titolo, folder=False)


def video_film_la7play():
    player = next_flight_data(get_html(G.URL_FILM))
    trovati = []
    elementi = []
    for m in re.finditer(r'\{"__typename":"NodeEventoSingolo"', player):
        film = json.JSONDecoder().raw_decode(player, m.start())[0]
        if not film.get('path') or film.get('id') in trovati:
            continue
        trovati.append(film.get('id'))
        elementi.append(film)

    for film in sorted(elementi, key=timestamp_film, reverse=True):
        aggiungi_film(film)
    chiudi_elenco_film()


def documentari():
    # pagina hub: i caroselli sono caricati dal browser con la query programsContentSlots
    data = gql_query(G.GQL_CONTENT_SLOTS, {'path': G.PATH_DOCUMENTARI})
    slots = ((data.get('route') or {}).get('entity') or {}).get('contentSlots') or []
    ids, serie, elementi = [], [], []
    for slot in slots:
        for item in (slot.get('paginatedItems') or {}).get('items') or []:
            tipo = item.get('__typename')
            if tipo == 'NodeEventoSingolo' and item.get('path') and item.get('id') not in ids:
                ids.append(item.get('id'))
                elementi.append((item, ''))
            elif tipo == 'NodeReplica':  # serie: le sue puntate entrano nello stesso elenco
                nome = ((item.get('property') or {}).get('titolo') or '').strip()
                if nome and nome.lower() not in serie:
                    serie.append(nome.lower())
                    puntate = gql_query(G.GQL_PUNTATE, {'property': nome.lower(), 'page': 1, 'pageSize': 20, 'stagione': None, 'sortDirection': 'DESC'})
                    for ep in (puntate.get('filteredNodeReplicasListing') or {}).get('nodes') or []:
                        if ep.get('path') and ep.get('id') not in ids:
                            ids.append(ep.get('id'))
                            elementi.append((ep, nome))
    if not elementi:
        xbmcgui.Dialog().ok(G.PLUGIN_NAME, G.LANGUAGE(32005))
    for film, nome_serie in sorted(elementi, key=lambda e: timestamp_film(e[0]), reverse=True):
        aggiungi_film(film, nome_serie, mostra_in_onda=False)
    chiudi_elenco_film()


def video_programma():
    if not G.LINK.startswith('http'):
        video_programma_la7play()
        return

    # TG DIGITAL (tg.la7.it, pagine HTML)
    req = Request(G.LINK + str(G.PAGENUM), headers={'user-agent': G.HEADERS_SET['user-agent']})
    html = BeautifulSoup(urlopen(req), 'html.parser')
    video_tgdigital = html.find('div', class_='article-container').find_all('div', class_='tgla7-news')
    if video_tgdigital:
        get_rows_video_tgdigital(video_tgdigital)
        pagenext(html.find('li', class_='pager-next').find('a'))

    xbmcplugin.setContent(G.PLUGIN_HANDLE, 'episodes')
    xbmcplugin.endOfDirectory(handle=G.PLUGIN_HANDLE, succeeded=True)


def get_rows_video_tgdigital(video):
    for div in video:
        titolo = div.find('h4', class_='news-title').text.strip()
        thumb = div.find('div', class_='news-img').find('a').get('style').split("url(")[1].split(")")[0]
        # Cerca il div della descrizione
        descrizione_div = div.find('div', class_='news-descrizione')
        # Estrai il testo solo se il div esiste, altrimenti usa una stringa vuota
        plot = descrizione_div.text.strip() if descrizione_div else ""
        link = G.URL_BASE_TGDIGITAL + div.find('h4', class_='news-title').find('a').get('href')
        liStyle = xbmcgui.ListItem(titolo, offscreen=True)
        liStyle.setArt({'thumb': thumb, 'fanart': G.FANART_PATH})
        liStyle.setInfo('video', {'plot': plot})
        add_directory_item_nodup({"mode": G.MODE, "play": link, "titolo": titolo, "thumb": thumb, "plot": plot}, liStyle, folder=False)


def pagenext(pagenb):
    if pagenb:
        liStyle = xbmcgui.ListItem('[B]' + G.LANGUAGE(32003) + '[/B]', offscreen=True)
        liStyle.setArt({'fanart': G.FANART_PATH})
        add_directory_item_nodup({"mode": G.MODE, "link": G.LINK, "page": G.PAGENUM + 1}, liStyle)


def run(argv):
    """ Addon entry point """
    G.init_globals(argv)

    if G.PARAMS.get("page", "") == "":
        G.PAGENUM = 0
    else:
        G.PAGENUM = int(G.PARAMS.get("page", ""))

    if G.MODE == "diretta_la7":
        play_dirette(G.URL_LIVE_LA7)

    elif G.MODE == "diretta_la7cinema":
        play_dirette(G.URL_LIVE_LA7CINEMA)

    elif G.MODE == "rivedi_la7":
        if G.PLAY == "":
            if G.GIORNO == "":
                rivedi(G.URL_RIVEDILA7, 'rivedila7.jpg')
            else:
                rivedi_giorno(G.URL_RIVEDILA7)
        else:
            play_video(G.PLAY)

    elif G.MODE == "rivedi_la7cinema":
        if G.PLAY == "":
            if G.GIORNO == "":
                rivedi(G.URL_RIVEDILA7CINEMA, 'direttalivela7cinema.jpg')
            else:
                rivedi_giorno(G.URL_RIVEDILA7CINEMA)
        else:
            play_video(G.PLAY)

    elif G.MODE == "tg_meteo":
        if G.PLAY == "":
            if G.LINK == "":
                programmi_lettera_tg_meteo()
            else:
                video_programma()
        else:
            play_video(G.PLAY)

    elif G.MODE == "tutti_programmi":
        if G.PLAY == "":
            if G.LINK == "":
                programmi_lettera()
            else:
                video_programma()
        else:
            play_video(G.PLAY)

    elif G.MODE == "film":
        if G.PLAY == "":
            video_film_la7play()
        else:
            play_video(G.PLAY)

    elif G.MODE == "documentari":
        if G.PLAY == "":
            documentari()
        else:
            play_video(G.PLAY)

    elif G.MODE == "podcast":
        if G.PLAY == "":
            if G.LINK == "":
                podcast_serie()
            else:
                podcast_episodi()
        else:
            play_podcast()

    elif G.MODE == "cerca_la7":
        if G.PLAY == "":
            cerca_la7()
        else:
            play_video(G.PLAY)

    else:
        show_root_menu()
