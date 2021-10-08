# Module: addon.py
# Author: Fabio F. / 2016-2021 ARSAT
# License: GNU General Public License, Version 3, http://www.gnu.org/licenses/

import xbmcgui
import xbmcplugin
import xbmcaddon
import json
import os
import requests
import base64
import hashlib
from urllib.parse import urlencode, parse_qsl, quote_plus as quote


PLUGIN_NAME = 'plugin.video.cinear'
API_URL     = 'https://play.cine.ar/api/v1.6'
ID_URL      = 'https://id.cine.ar/v1.5'

addon_url = sys.argv[0]
addon_handle = int(sys.argv[1])
addon = xbmcaddon.Addon(PLUGIN_NAME)
addon_name = addon.getAddonInfo('name')
addon_icon = addon.getAddonInfo('icon')
addon_version = addon.getAddonInfo('version')
art_path = os.path.join(addon.getAddonInfo('path'), 'resources', 'media')

META = None  # result of GET /metadata
PID  = None  # received always via params


def digest(data):
    digest = hashlib.md5(data.encode('utf-8')).digest()
    return base64.b64encode(digest)


def translation(id):
    return addon.getLocalizedString(id).encode('utf-8')


def init_session():
    email = xbmcgui.Dialog().input(translation(30001), addon.getSetting('email'), xbmcgui.INPUT_ALPHANUM)
    if email == '': return False
    addon.setSetting('email', email)
    clave = xbmcgui.Dialog().input(translation(30002), '', xbmcgui.INPUT_ALPHANUM, xbmcgui.ALPHANUM_HIDE_INPUT)
    if clave == '': return False

    url = f"{ID_URL}/auth/login"
    response = requests.post(url, json={'email': email, 'password': clave}, headers=get_headers())
    data, errmsg = decode_json(response)

    if data:
        addon.setSetting('token', data['token'])
        return True
    else:
        xbmcgui.Dialog().ok(translation(30003), errmsg)
        return False


def add_directory_item(name, query, image=None, isFolder=True, art=None, info=None):
    url = '%s?action=%s' % (addon_url, query)
    url += ('&pid=%s' % PID) if PID else ''
    item = xbmcgui.ListItem(label=name)
    if image:
        thumb = os.path.join(art_path, image)
        item.setArt({'icon': thumb, 'thumb': thumb})
    if art: item.setArt(art)
    if info: item.setInfo('video', info)
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=item, isFolder=isFolder)


def list_profiles():
    # get the list of profiles of a user
    profiles = None
    if addon.getSetting('token') != '':
        profiles = json_request('user')
    if profiles == None:
        if not init_session(): return
        profiles = json_request('user')

    # check if terms and conditions were accepted
    if profiles['torAccept']['mustAccept']:
        xbmcgui.Dialog().ok(translation(30004), translation(30005))
        xbmc.executebuiltin('ActivateWindow(Videos,addons://sources/video/)')
        return

    # if there is only one profile, go ahead
    if len(profiles['perfiles']) == 1:
        profile =  profiles['perfiles'][0]
        global PID
        PID = profile['id']
        root_menu({'pid': profile['id'], 'alias': profile['alias'], 'conclave': profile.get('conclave')})
        return

    # or prepare a list to choose a profile
    for profile in profiles['perfiles']:
        query = f"root_menu&pid={profile['id']}&alias={profile['alias'].encode('utf-8')}&conclave={profile.get('conclave')}"
        add_directory_item(profile['alias'], query, art={"poster": image_url(profile['avatar'], 'avatar')})
    xbmcplugin.endOfDirectory(addon_handle)


def get_media(title):
    media = {"culas": "movies.png", "Serie": "series.png", "Corto": "shorts.png", "Especial": "specials.png", "Estreno": "premieres.png"}
    for k, v in list(media.items()):
        if k in title:
            return v
    return "movies.png"


def root_menu(params):
    if params['conclave'] == 'True':
        pin = xbmcgui.Dialog().input(translation(30006) + params['alias'], type=xbmcgui.INPUT_NUMERIC)
        if pin == '': return
        # validate pin if required (pins are optional)
        path = f"perfil/{PID}/clave/{pin}"
        response = json_request(path)
        valid = response['valid']
        if not valid:
            xbmcgui.Dialog().ok(translation(30007), translation(30008))
            return

    # Home / Inicio
    add_directory_item(translation(30009), 'list_tiras', 'explore.png')
    # Last seen / Últimas vistas
    add_directory_item(translation(30010), 'list_prods&url=%s' % quote('tira/histoprods'), 'last-seen.png')
    # Movies, TV Shows, Shorts, Featured
    categories = json_request(f"navbar?perfil={PID}")
    for tipo in sorted(categories['tipos'], key=lambda cat: cat['orden']):
        add_directory_item(tipo['text'], 'list_prods&url=%s' % quote('tipo/' + tipo['tag']), get_media(tipo['text']))
    # Explore
    add_directory_item(translation(30011), 'list_generos', 'explore.png')
    # Mi sala
    add_directory_item(translation(30012), 'list_prods&url=%s' % quote('tira/misala'), 'mi-sala.png')
    # Search / Búsqueda
    add_directory_item(translation(30013), 'search', 'search.png')
    # Close session
    add_directory_item(translation(30014), 'close_session', 'close-session.png', False)

    xbmcplugin.endOfDirectory(addon_handle)


def list_tiras(params):
    """ Explorar por tiras """
    # first featured, aka banner
    add_directory_item(translation(30015), 'list_prods&url=%s' % quote('tira/banner'), 'movies.png')

    # then add dynamic content (tira)
    for tira in json_request(f"tiras?perfil={PID}"):
        add_directory_item(tira['titulo'], 'list_prods&url=%s' % quote('tira/' + str(tira['id'])), get_media(tira['titulo']))

    xbmcplugin.endOfDirectory(addon_handle)


def list_generos(params):
    """ Explorar por generos """
    categories = json_request(f"navbar?perfil={PID}")
    for tipo in categories['generos']:
        iurl = quote('genre/' + quote(tipo['nom'].encode('utf8', 'ignore')))
        add_directory_item(tipo['nom'], 'list_prods&url=%s' % iurl, 'movies.png')

    xbmcplugin.endOfDirectory(addon_handle)


def close_session(params):
    """ Cierra la sesión y vuelve al menu de videos addons """
    addon.setSetting('token', '')
    xbmc.executebuiltin('ActivateWindow(Videos,addons://sources/video/)')


def list_prods(params):
    """ Arma la lista de producciones del menu principal """
    # optional parameters
    items = int(addon.getSetting('itemsPerPage'))
    page = int(params.get('pag', '1'))
    orden = params.get('orden')

    if 'tvod' in params['url']:
        xbmcgui.Dialog().ok(translation(30033), translation(30034))

    path = f"{params['url']}?perfil={PID}&cant={items}&pag={page}"
    if orden: path += f"&orden={orden}"
    prod_list = json_request(path)

    # list everything but seasons, episodes y compiled elements
    for prod in prod_list['prods']:
        add_film_item(prod, params)

    if len(prod_list['prods']) == items:
        query = f"list_prods&url={quote(params['url'])}&pag={page+1}"
        if orden: query += f"&orden={orden}"
        add_directory_item(translation(30031), query, 'movies.png')

    xbmcplugin.endOfDirectory(addon_handle)


def list_subprods(params):
    """ Arma la lista de producciones para series y compilados (especiales) """
    path = f"{params['source']}/prod/{params['sid']}?perfil={PID}"
    # 'items' restringe por temporada en caso de cabeserie
    season = params.get('season')   # selected season or None
    if params.get('full'):
        path += '&items=' + str(season or 0)
    prod_list = json_request(path)

    if prod_list['tipos'][0]['tag'] == 'cabeserie':

        # set comprehension fails in ARM (in 2016): seasons = {epi['tempo'] for epi in prod_list['items']}
        seasons = list(set([epi.get('tempo') or epi['capitulo']['tempo'] for epi in prod_list['items']]))

        if season:
            # list all episodes for a season
            for episode in prod_list['items']:
                add_film_item(episode, params)

        elif len(seasons) > 1:
            # list all seasons
            for season in sorted(seasons):
                query = 'list_subprods&source={0}&sid={1}&season={2}&full={3}'.format(params['source'], params['sid'], season, 1)
                art = {'fanart': image_url(prod_list.get('ban'), 'odeon_slider')}
                add_directory_item('Temporada {0}'.format(season), query, 'series.png', art=art, info=get_info(prod_list))
        else:
            # there is only one season
            params['full'] = '1'
            params['season'] = seasons[0]
            return list_subprods(params)

    else:
        # list compiled inside specials
        for compi in prod_list['items']:
            add_film_item(compi, params)

    xbmcplugin.endOfDirectory(addon_handle)


def get_info(prod):
    """ Arma toda la metadata de una producción """
    info = {}
    if 'serie' in prod['tags']:
        info['title'] = str(prod['capitulo']['capi']) + ' - ' + prod['tit']
        info['season'] = prod['capitulo']['tempo']
        info['episode'] = prod['capitulo']['capi']
        info['mediatype'] = 'episode'
    else:
        info['title'] = prod['tit']
        info['mediatype'] = 'movie'

    info['year'] = prod.get('an')
    info['plot'] = prod.get('sino')
    info['genre'] = ", ".join([genero['nom'] for genero in prod.get('gens',[])])

    if 'pers' in prod:
        info['cast'] = [pers['nom'] for pers in prod['pers']['01'] if pers['rol'] == 'INT']
        info['director'] = ", ".join([pers['nom'] for pers in prod['pers']['01'] if pers['rol'] == 'DIR'])
        info['writer'] = ", ".join([pers['nom'] for pers in prod['pers']['01'] if pers['rol'] == 'GUI'])

    if 'rProme' in prod: info['rating'] = prod['rProme']
    if 'rVotan' in prod: info['votes'] = str(prod['rVotan'])
    if 'usucalif' in prod: info['userrating'] = prod['usucalif']
    info['playcount'] = 1 if prod['vista']['completa'] else 0

    return info


def image_url(image, context):
    if not image: return None
    return f"{META['objsturi']}/{image}/context/{context}/normal"


def get_art(prod):
    afiche = prod['afis'][0] if 'afis' in prod and len(prod['afis']) > 0 else prod.get('afi', None)
    thumb  = image_url(afiche, 'odeon_afiche_suge')
    poster = image_url(afiche, 'odeon_afiche_prod')

    banner = image_url(prod['ban'], 'odeon_slider') if 'ban' in prod else None

    foto = prod['fotos'][0] if 'fotos' in prod and len(prod['fotos']) > 0 else prod.get('foto', None)
    fanart = image_url(foto, 'odeon_fotograma_ampli')

    return {'thumb': thumb, 'poster': poster, 'banner': banner, 'fanart': fanart}


def run_plugin(query, prod, params):
    return 'RunPlugin({0}?action={1}&pid={2}&source={3}&sid={4})'.format(
                    addon_url, query, PID, prod['id']['source'], prod['id']['sid'])


def add_film_item(prod, params):
    """ Arma un item de menu con sus menues contextuales """
    has_subprods = any(x in ['cabeserie', 'compi', 'espe'] for x in prod['tags'])

    info = get_info(prod)
    item = xbmcgui.ListItem(label=info['title'])
    item.setInfo('video', info)

    art = get_art(prod)
    if has_subprods: art.update({'fanart': None})
    item.setArt(art)

    percent = 100 * prod['vista']['secsTranscu'] / prod['vista']['secsDura'] if prod['vista']['secsDura'] > 0 else 0
    resumeTime = prod['vista']['secsTranscu'] if 1 < percent < 95 else 0
    item.setProperty('ResumeTime', str(resumeTime))
    item.setProperty('TotalTime', str(prod['vista']['secsDura']))

    context_menu = []

    # Add/Remove for Mi Sala should not be available for episodes
    if 'serie' not in prod['tags']:
        menu_text = translation(30021) if not prod.get('misala') else translation(30022)
        context_menu.append((menu_text, run_plugin('toggle_misala', prod, params)))

    # Qualify should not be available for episodes nor compiled (cabecera)
    if 'serie' not in prod['tags'] and 'compi' not in prod['tags']:
        context_menu.append((translation(30023), run_plugin('user_qualify', prod, params)))

    # Order by should not be available for episodes nor compiled elements
    if 'url' in params:
        context_menu.append((translation(30024), run_plugin('sort&url=%s' % quote(params['url']), prod, params)))

    item.addContextMenuItems(context_menu, replaceItems=True)

    if has_subprods:
        url = '{0}?action={1}&pid={2}&source={3}&sid={4}'.format(
                addon_url, 'list_subprods', PID, prod['id']['source'], prod['id']['sid'])
        url += '&full=1' if 'compi' in prod['tags'] else ''
        is_folder = True
    else:
        url = '{0}?action={1}&pid={2}&source={3}&sid={4}'.format(
                addon_url, 'play', PID, prod['id']['source'], prod['id']['sid'])
        item.setProperty('IsPlayable', 'true') # needed only when use with xbmcplugin.setResolvedUrl()
        item.addStreamInfo('video', {'codec': 'h264'})
        item.addStreamInfo('audio', {'codec': 'aac', 'language' : 'es'})
        is_folder = False

    xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=item, isFolder=is_folder)


def toggle_misala(params):
    path = f"{params['source']}/amisala/{PID}/{params['sid']}"
    json_request(path)
    xbmc.executebuiltin("Container.Refresh")


def user_qualify(params):
    voto = xbmcgui.Dialog().select(translation(30025), ['1', '2', '3', '4', '5'])
    if voto == -1: return
    path = '{0}/votar/{1}/{2}?voto={3}'.format(params['source'], PID, params['sid'], voto + 1)
    response = requests.post(make_url(path), headers=get_headers(addon.getSetting('token')))
    if response.status_code == 200:
        xbmc.executebuiltin("Container.Refresh")
    else:
        xbmcgui.Dialog().ok('Error ({0})'.format(response.status_code), response.content)
        sys.exit(0)


def sort(params):
    order_names = [ord['nom'] for ord in META['order']]
    order_ids = [ord['id'] for ord in META['order']]
    index = xbmcgui.Dialog().select(translation(30026), order_names)
    if index == -1: return
    query = '{0}?action={1}&pid={2}&url={3}&orden={4}'.format(addon_url, 'list_prods', PID, quote(params['url']), order_ids[index])
    xbmc.executebuiltin(f"Container.Update({query})")


def search(params):
    # search by title, director, actor...
    texto = xbmcgui.Dialog().input(translation(30027))
    if texto == '': return
    params['url'] = 'search/' + quote(texto)
    list_prods(params)


def heartbeat(source, sid, currentTime, totalTime):
    token = addon.getSetting('token')
    url = make_url('{0}/vista/{1}/{2}/{3}/{4}/{5}'.format(source, PID, sid, int(totalTime), int(currentTime), token))
    r = requests.get(url, headers=get_headers())
    # xbmc.executebuiltin('Notification(%s, %s, %d, %s)'%(addon_name, 'Beat ' + str(currentTime/60), 1000, addon_icon))


def monitor(source, sid):
    player = xbmc.Player()
    monitor = xbmc.Monitor()

    # wait for the player to start
    for i in range(60):
        if player.isPlayingVideo(): break
        if monitor.waitForAbort(1): break

    if monitor.abortRequested(): return
    if not player.isPlayingVideo():
        # not reproducing, must retry
        xbmcgui.Dialog().ok(addon_name, translation(30028))
        return

    lastTime = player.getTime()
    beatTime = lastTime - 60
    totalTime = player.getTotalTime()

    while player.isPlayingVideo() and not monitor.abortRequested():
        currentTime = player.getTime()
        if abs(currentTime - lastTime) > 15:
            # user seek
            heartbeat(source, sid, currentTime, totalTime)
            beatTime = currentTime

        elif currentTime >= beatTime + 60:
            # track minute seen to backend
            heartbeat(source, sid, currentTime, totalTime)
            beatTime += 60

        lastTime = currentTime
        monitor.waitForAbort(2)


def play(params):
    token = addon.getSetting('token')
    url = '{0}?s={1}&i={2}&p={3}&t={4}'.format(META["playeruri"], params['source'], params['sid'], PID, token)
    clave = params['source'] + params['sid'] + PID + token + 'ARSAT'
    response = requests.get(url, headers=get_headers(auth=digest(clave)))
    data, errmsg = decode_json(response)
    if data:
        response = requests.get(data["url"], headers=get_headers(auth=digest(clave)))
        if response.status_code == 200:
            item = xbmcgui.ListItem(path=data["url"])
            xbmcplugin.setResolvedUrl(addon_handle, True, item)
            monitor(params['source'], params['sid'])
        else:
            show_error(translation(30036), response.status_code, translation(30035))
            xbmc.sleep(1000)
    else:
        show_error(translation(30036), response.status_code, errmsg)


def get_headers(token=None, etag=None, auth=None, gzip=False):
    header = {'Content-type': 'application/json; charset=utf-8',
              'User-Agent': 'kodi/' + addon_version,
              'Accept': 'application/json, text/plain',
              'Referer': 'plugin://kodi.cine.ar'
             }
    if token: header.update({'Authorization': 'Bearer ' + token})
    if etag: header.update({'If-None-Match': etag})
    if auth: header.update({'x-auth-key': auth})
    if gzip: header.update({'Accept-Encoding': 'gzip'})
    return header


def make_url(path, data=None):
    url = f"{API_URL}/{path}"
    if data: url += f"?{urlencode(data)}"
    return url


def decode_json(response):
    try:
        data = json.loads(response.content)
        if response.status_code == 200:
            return data, ''
        errmsg = data['message'] or 'Error (json)'
    except:
        errmsg = response.content or 'Error (html)'
    return None, errmsg


def show_error(title, status, message):
    try:
        xbmc.log(f"ERROR [{PLUGIN_NAME}]: {title} - code ({status}) - {message.encode('utf8', 'ignore')}", level=xbmc.LOGDEBUG)
        xbmcgui.Dialog().ok(f"{title} ({status})", message)
    except:
        pass


def json_request(path, params=None):
    token = addon.getSetting('token')
    url = make_url(path, params)

    r = requests.get(url, headers=get_headers(token, gzip=True))

    if r.status_code == 401:
        # special case used during login to test a token
        if path == 'user': return None
        # in the very unlikely situation token expires, user must restart
        xbmcgui.Dialog().ok(translation(30029), translation(30030))
        close_session([])
        sys.exit(0)

    # raise for status
    elif r.status_code >= 400:
        show_error(translation(30037), r.status_code, r.content)
        close_session([])
        sys.exit(0)

    if not r.content: return None
    data, errmsg = decode_json(r)
    if not data:
        show_error(translation(30037), r.status_code, errmsg)
        sys.exit(0)
    return data


if __name__ == '__main__':
    params = dict(parse_qsl(sys.argv[2][1:]))
    if params:
        META = json.loads(addon.getSetting('metadata'))
        PID = params['pid']
        globals()[params['action']](params)
    else:
        META = json_request('metadata')
        addon.setSetting('metadata', json.dumps(META))
        list_profiles()
