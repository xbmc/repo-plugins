# -*- coding: utf-8 -*-
from kodiswift import Plugin, actions
from kodiswift import xbmc, xbmcgui
import xbmcaddon
import requests
import copy
import platform
import os


# Global vars
plugin = Plugin()
addon = plugin.addon

USER_AGENT = "Kodi ("+platform.system() + ") hearthis.at-Plugin/" + addon.getAddonInfo('version')
HEARTHIS = 'hearthis.at'
API_BASE_URL = "https://api-v2.hearthis.at/"
USER = plugin.get_storage('user_data')
ADDON_PATH = xbmc.translatePath(addon.getAddonInfo('path')).decode('utf-8')

STRINGS = {
        'genres'        : 30000,
        'playlists'     : 30001,
        'show_artist'   : 30002,
        'recently_added': 30003,
        'search'        : 30004,
        'search_artist' : 30005,
        'next'          : 30006,
        'likes'         : 30007,
        'popular'       : 30008,
        'search_track'  : 30009,
        'previous'      : 30010,
        'no_elements'   : 30011,
        'add_like'      : 30012,
        'rm_like'       : 30013,
        'my_likes'      : 30014,
        'following'     : 30015,
        'add_follow'    : 30016,
        'rm_follow'     : 30017,
        'tracks'        : 30018,
        'reshared'      : 30019,
        'add_reshared'  : 30020,
        'rm_reshared'   : 30021,
        'login_failed'  : 30022
}


def get_image(img):
    return os.path.join(ADDON_PATH,'resources','images', img)


def _(string):
    tstring = STRINGS.get(string)
    if tstring == None:
        return None
    else:
        return addon.getLocalizedString(tstring)


def api_call(path, params=None, rtype='GET', data=None, json=True):
    if logged_in():
        if params == None:
            params = {}
        params['key'] = USER['data']['key']
        params['secret'] = USER['data']['secret']
    url = API_BASE_URL+path
    headers = {'user-agent': USER_AGENT}
    plugin.log.info('api-call: %s with data %s' % (url, str(data)))
    if rtype == 'GET':
        r = requests.get(url, params=params, headers=headers)
    else:
        plugin.log.info("doing post")
        r = requests.post(url, params=params, data=data, headers=headers)
    if json:
        return r.json()
    else:
        return r.text
    

def list_users(userlist, pagination = None, first=False, pre=[], post=[]):
    if isinstance(userlist, dict) or len(userlist) == 0:
        plugin.notify(_('no_elements'))
        return None
    items = pre
    items.append(pn_button(pagination, -1, len(userlist)))
    for u in userlist:
        items.append({'label': '%s%s (%s %s)' % ((u'[\u2665] ' if u.get('following', False)  else u''), u['username'], str(u['track_count']), _('tracks')), 
                      'icon': u['avatar_url'], 
                      'context_menu':   [
                                            context_item_toggle('follow', u['following'], {'user': u['permalink']})
                                        ],
                      'path': plugin.url_for('show_user_first', user=u['permalink'], page=1, first=True)})
    items = items + post
    items.append(pn_button(pagination, 1, len(userlist)))
    #only skip history if turning pages, not if opening first page initially
    if pagination != None and first != 'True':
        ul=True
    else:
        ul=False
    return plugin.finish(items, update_listing=ul)


def list_tracks(tracklist, pagination = None, first=False, pre=[], post=[]):
    if isinstance(tracklist, dict) or len(tracklist) == 0:
        plugin.notify(_('no_elements'))
        return None
    items = pre
    items.append(pn_button(pagination, -1, len(tracklist)))
    for t in tracklist:
        plugin.log.info('fav: '+str(t['permalink'])+str(type(t['favorited']))+'/'+str(t['favorited']) )
        
        like_res = ''
        if t.get('favorited', False):
            like_res +=  u'\u2665'
        if t.get('reshared', False):
            like_res += u' \u00bb'
        items.append({
                'label': u'%s%s - %s' % ((u'[%s] ' % (like_res) if like_res != ''  else u''), t['user']['username'], t['title']),
                'icon': t['artwork_url'],
                'thumbnail': t['artwork_url'],
                'info_type': 'music',
                'info': {
                            'duration': t.get('duration', None),
                            'date': t.get('created_at', None),
                            'artist': t['user']['username'],
                            'title': t['title'],
                            'genre': t.get('genre', None),
                            'playcount': int(t.get('playback_count', None))
                         },
                'context_menu': 
                                    show_user_context_item(t['user']['permalink']) +
                                    context_item_toggle('like', t['favorited'], {'user':t['user']['permalink'], 'trackid': t['permalink']}) +
                                    context_item_toggle('reshared', t['reshared'], {'user':t['user']['permalink'], 'trackid': t['permalink']})
                              ,
                'path': plugin.url_for('play_track', trackid=t['permalink'], user=t['user']['permalink']),
                'is_playable': True
        })
    items = items + post
    items.append(pn_button(pagination, 1, len(tracklist)))
    #only skip history if turning pages, not if opening first page initially
    if pagination != None and first != 'True':
        ul=True
    else:
        ul=False
    return plugin.finish(items, update_listing=ul)


def pn_button(pagination, direction, length):
    page = pagination['args']['page']
    if pagination != None :
        args = copy.deepcopy(pagination['args'])
        args['page'] += direction
        if direction == -1:
            if page <= 1:
                return None
            lbl=_("previous")
        else:
            if length < int(addon.getSetting('page_count')):
                return None
            lbl=_("next")
        return {'label': '[%s ...]' % (lbl), 'path': plugin.url_for(pagination['call'], **args)}
    else:
        return None


def add_pp(obj, page):
    obj['page'] = int(page)
    obj['count'] = int(addon.getSetting('page_count'))
    return obj


def login():
    if addon.getSetting('login_enabled') == 'false':
        if logged_in():
            result = api_call('logout/')
            USER['data'] = None
            plugin.log.info("Logging out: "+str(result))
        return
    password = addon.getSetting('password')
    email = addon.getSetting('email')
    if logged_in():
        return
    result = api_call('login/', rtype='POST', data={'email': email, 'password': password})
    plugin.log.info("res: "+str(result))
    if result.get('success', True):
        plugin.log.info("login successful")
        USER['data'] = result
    else:
        plugin.notify(_('login_failed'))


def logged_in():
    return USER.get('data', None) != None


def context_item_toggle(prop, state, parms):
    if logged_in():
        if state:
            lbl = 'rm_'+prop
        else:
            lbl = 'add_'+prop
        parms['prop'] = prop
        ar_follow = [( _(lbl), actions.update_view(plugin.url_for('toggle_prop', **parms)))]
    else:
        ar_follow = []
    return ar_follow


def show_user_context_item(user):
    show_user_url = plugin.url_for('show_user_first', user=user, page=1, first='True')
    return [ ( _('show_artist'), actions.update_view(show_user_url)) ]


@plugin.route('/')
def main_menu():
    login()
    items1 = [
                {'label': _('recently_added'), 'icon': get_image('new.png'), 'path': plugin.url_for('show_feed_first', ftype='new')},
                {'label': _('popular'), 'icon': get_image('popular.png'), 'path': plugin.url_for('show_feed_first', ftype='popular')},
                {'label': _('genres'), 'icon': get_image('genres.png'), 'path': plugin.url_for('show_genres')},
            ]
    if logged_in():
        items_private = [   
                {'label': _('my_likes'), 'icon': get_image('likes.png'), 'path': plugin.url_for('show_users_likes_first', user=USER['data']['permalink'])},
                {'label': _('following'), 'icon': get_image('following.png'), 'path': plugin.url_for('show_following_first', user=USER['data']['permalink'])},
                {'label': _('reshared'), 'icon': get_image('reshared.png'), 'path': plugin.url_for('show_reshared_first', user=USER['data']['permalink'])},
                        ]
    else:
        items_private = []
    items2 = [
                {'label': _('search'), 'icon': get_image('search.png'),  'path': plugin.url_for('search')}
            ]
    return plugin.finish(items1 + items_private + items2)


@plugin.route('/playlist/<plink>')
def show_playlist(plink):
    plist = api_call('set/'+plink)
    return list_tracks(plist)


@plugin.route('/user/<user>/playlists', name='show_users_playlists_first', options={'page': '1', 'first': 'True'})
@plugin.route('/user/<user>/playlists/<page>')
def show_users_playlists(user, page, first=False):
    results = api_call(user, add_pp({'type': 'playlists'}, page))  
    items = []
    for l in results:
        items.append({'label': l['title'], 'path': plugin.url_for('show_playlist', plink=l['permalink'])})
    pagination={'call': 'show_users_playlists', 'args':{'user': user, 'page': int(page)}}
    return list_tracks(results, pagination, first)


@plugin.route('/user/<user>/likes', name='show_users_likes_first', options={'page': '1', 'first': 'True'})
@plugin.route('/user/<user>/likes/<page>')
def show_users_likes(user, page, first=False):
    results = api_call(user, add_pp({'type': 'likes'}, page))    
    pagination={'call': 'show_users_likes', 'args':{'user': user, 'page': int(page)}}
    return list_tracks(results, pagination, first)


@plugin.route('/user/<user>/reshared', name='show_reshared_first', options={'page': '1', 'first': 'True'})
@plugin.route('/user/<user>/reshared/<page>')
def show_reshared(user, page, first=False):
    results = api_call(user, add_pp({'type': 'reshares'}, page))    
    pagination={'call': 'show_reshared', 'args':{'user': user, 'page': int(page)}}
    return list_tracks(results, pagination, first)


@plugin.route('/user/<user>/following', name='show_following_first', options={'page': '1', 'first': 'True'})
@plugin.route('/user/<user>/following/<page>')
def show_following(user, page, first=False):
    results = api_call(user+'/following', add_pp({}, page))    
    pagination={'call': 'show_following', 'args':{'user': user, 'page': int(page)}}
    return list_users(results, pagination, first)


@plugin.route('/user/<user>/<page>/<first>', name='show_user_first', options={'page': '1', 'first': 'True'})
@plugin.route('/user/<user>/<page>')
def show_user(user, page, first=False):
    u = api_call(user)
    results = api_call(user, add_pp({'type': 'tracks'}, page))  
    pagination={'call': 'show_user', 'args':{'user': user, 'page': int(page)}}
    selectors = [
                    {'label': '%s (%s)' % (_('playlists'), str(u['playlist_count'])), 'icon': get_image('playlist.png'), 'path': plugin.url_for('show_users_playlists_first', user=user)},
                    {'label': '%s (%s)' % (_('likes'), str(u['likes_count'])), 'icon': get_image('likes.png'), 'path': plugin.url_for('show_users_likes_first', user=user)},
                    {'label': _('reshared'), 'icon': get_image('reshared.png'), 'path': plugin.url_for('show_reshared_first', user=user)}
                ]
    return list_tracks(results, pagination, first, pre=selectors)

    
@plugin.route('/genres')
def show_genres():
    results = api_call('categories')
    items = []
    for g in results:
        items.append({
            'label': g['name'],
            'path': plugin.url_for('show_genre_first', genre=g['id'])
        })
    return plugin.finish(items)


@plugin.route('/feeds/<ftype>/<page>/<first>', name='show_feed_first', options={'page': '1', 'first': 'True'})
@plugin.route('/feeds/<ftype>/<page>')
def show_feed(ftype, page, first=False):
    results = api_call('feed', add_pp({'type': ftype}, page))  
    pagination={'call': 'show_feed', 'args':{'ftype': ftype, 'page': int(page)}}
    return list_tracks(results, pagination, first)


@plugin.route('/genre/<genre>/<page>/<first>', name='show_genre_first', options={'page': '1', 'first': 'True'})
@plugin.route('/genre/<genre>/<page>')
def show_genre(genre, page, first=False):
    results = api_call('categories/'+genre, add_pp({}, page))  
    pagination={'call': 'show_genre', 'args':{'genre': genre, 'page': int(page)}}
    return list_tracks(results, pagination, first)


@plugin.route('/search_for/<stype>/<skey>/<page>/<first>', name='search_for_first')
@plugin.route('/search_for/<stype>/<skey>/<page>')
def search_for(stype, skey, page, first=False):
    results = api_call('search', add_pp({'type': stype, 't': skey}, page))  
    pagination={'call': 'search_for', 'args':{'stype': stype, 'skey': skey, 'page': int(page)}}
    if stype == 'tracks':
        return list_tracks(results, pagination, first)
    elif stype == 'user':
        return list_users(results, pagination, first)


@plugin.route('/search')
def search():
    kb = xbmc.Keyboard ('', _('Search'), False)
    kb.doModal()
    if kb.isConfirmed():
        skey = kb.getText()
    else:
        return None
    selectors = [
                        {'label': _('search_artist'), 'icon': get_image('search_artist.png'), 'path': plugin.url_for('search_for_first', stype='user', skey=skey, page=1, first='True')},
                        {'label': _('search_track'), 'icon': get_image('search_track.png'), 'path': plugin.url_for('search_for_first', stype='tracks', skey=skey, page=1, first='True')}
                ]
    return plugin.finish(selectors)
    
   
@plugin.route('/play/<user>/<trackid>')
def play_track(user, trackid):
    playurl='https://hearthis.at/'+user+'/'+trackid+'/listen'
    plugin.log.info('Playing: %s' % playurl)
    return plugin.set_resolved_url(playurl)   


@plugin.route('/logged_in/toggle/<prop>')
def toggle_prop(prop):
    parms = plugin.request.args
    if prop == 'like':
        results = api_call(parms['user'][0]+'/'+parms['trackid'][0]+'/like')
        r = results['liked']
    elif prop == 'follow':
        results = api_call(parms['user'][0]+'/follow')
        r = results['follow']
    elif prop == 'reshared':
        results = api_call(parms['user'][0]+'/'+parms['trackid'][0]+'/reshare')
    plugin.log.info(str(results))
    #plugin.notify('set' if r else 'reset')
    return None


if __name__ == '__main__':
    plugin.run()
