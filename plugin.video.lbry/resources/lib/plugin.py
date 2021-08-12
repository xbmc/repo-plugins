# -*- coding: utf-8 -*-
from __future__ import absolute_import

import xbmc
import xbmcaddon
from xbmcgui import ListItem, Dialog, NOTIFICATION_ERROR
from xbmcplugin import addDirectoryItem, addDirectoryItems, endOfDirectory, setContent, setResolvedUrl

import routing
import requests
import time

from urllib.parse import quote,unquote,quote_plus,unquote_plus

from resources.lib.local import *
from resources.lib.exception import *

ADDON = xbmcaddon.Addon()
tr = ADDON.getLocalizedString
lbry_api_url = unquote(ADDON.getSetting('lbry_api_url'))
if lbry_api_url == '':
    raise Exception('Lbry API URL is undefined.')

items_per_page = ADDON.getSettingInt('items_per_page')
nsfw = ADDON.getSettingBool('nsfw')

plugin = routing.Plugin()
ph = plugin.handle
setContent(ph, 'videos')
dialog = Dialog()

def call_rpc(method, params={}, errdialog=True):
    try:
        xbmc.log('call_rpc: url=' + lbry_api_url + ', method=' + method + ', params=' + str(params))
        result = requests.post(lbry_api_url, json={'method': method, 'params': params})
        result.raise_for_status()
        rjson = result.json()
        if 'error' in rjson:
            raise PluginException(rjson['error']['message'])
        return result.json()['result']
    except requests.exceptions.ConnectionError as e:
        if errdialog:
            dialog.notification(tr(30105), tr(30106), NOTIFICATION_ERROR)
        raise PluginException(e)
    except requests.exceptions.HTTPError as e:
        if errdialog:
            dialog.notification(tr(30101), str(e), NOTIFICATION_ERROR)
        raise PluginException(e)
    except PluginException as e:
        if errdialog:
            dialog.notification(tr(30102), str(e), NOTIFICATION_ERROR)
        raise e
    except Exception as e:
        xbmc.log('call_rpc exception:' + str(e))
        raise e

def serialize_uri(item):
    # all uris passed via kodi's routing system must be urlquoted
    if type(item) is dict:
        return quote(item['name'] + '#' + item['claim_id'])
    else:
        return quote(item)

def deserialize_uri(item):
    # all uris passed via kodi's routing system must be urlquoted
    return unquote(item)

def to_video_listitem(item, playlist='', channel='', repost=None):
    li = ListItem(item['value']['title'] if 'title' in item['value'] else item['file_name'] if 'file_name' in item else '')
    li.setProperty('IsPlayable', 'true')
    if 'thumbnail' in item['value'] and 'url' in item['value']['thumbnail']:
        li.setArt({
            'thumb': item['value']['thumbnail']['url'],
            'poster': item['value']['thumbnail']['url'],
            'fanart': item['value']['thumbnail']['url']
        })

    infoLabels = {}
    menu = []
    plot = ''
    if 'description' in item['value']:
        plot = item['value']['description']
    if 'author' in item['value']:
        infoLabels['writer'] = item['value']['author']
    elif 'channel_name' in item:
        infoLabels['writer'] = item['channel_name']
    if 'timestamp' in item:
        timestamp = time.localtime(item['timestamp'])
        infoLabels['year'] = timestamp.tm_year
        infoLabels['premiered'] = time.strftime('%Y-%m-%d',timestamp)
    if 'video' in item['value'] and 'duration' in item['value']['video']:
        infoLabels['duration'] = str(item['value']['video']['duration'])

    if playlist == '':
        menu.append((
            tr(30212) % tr(30211), 'RunPlugin(%s)' % plugin.url_for(plugin_playlist_add, name=quote(tr(30211)), uri=serialize_uri(item))
        ))
    else:
        menu.append((
            tr(30213) % tr(30211), 'RunPlugin(%s)' % plugin.url_for(plugin_playlist_del, name=quote(tr(30211)), uri=serialize_uri(item))
        ))

    menu.append((
        tr(30208), 'RunPlugin(%s)' % plugin.url_for(claim_download, uri=serialize_uri(item))
    ))

    if 'signing_channel' in item and 'name' in item['signing_channel']:
        ch_name = item['signing_channel']['name']
        ch_claim = item['signing_channel']['claim_id']
        ch_title = ''
        if 'value' in item['signing_channel'] and 'title' in item['signing_channel']['value']:
            ch_title = item['signing_channel']['value']['title']

        plot = '[B]' + (ch_title if ch_title.strip() != '' else ch_name) + '[/B]\n' + plot

        infoLabels['studio'] = ch_name

        if channel == '':
            menu.append((
                tr(30207) % ch_name, 'Container.Update(%s)' % plugin.url_for(lbry_channel, uri=serialize_uri(item['signing_channel']),page=1)
            ))
        menu.append((
            tr(30205) % ch_name, 'RunPlugin(%s)' % plugin.url_for(plugin_follow, uri=serialize_uri(item['signing_channel']))
        ))

    if repost != None:
        if 'signing_channel' in repost and 'name' in repost['signing_channel']:
            plot = (('[COLOR yellow]%s[/COLOR]\n' % tr(30217)) % repost['signing_channel']['name']) + plot
        else:
            plot = ('[COLOR yellow]%s[/COLOR]\n' % tr(30216)) + plot

    infoLabels['plot'] = plot
    li.setInfo('video', infoLabels)
    li.addContextMenuItems(menu)

    return li

def result_to_itemlist(result, playlist='', channel=''):
    items = []
    for item in result:
        if not 'value_type' in item:
            xbmc.log(str(item))
            continue
        if item['value_type'] == 'stream' and item['value']['stream_type'] == 'video':
            # nsfw?
            if 'tags' in item['value']:
                if 'mature' in item['value']['tags'] and not nsfw:
                    continue

            li = to_video_listitem(item, playlist, channel)
            url = plugin.url_for(claim_play, uri=serialize_uri(item))

            items.append((url, li))
        elif item['value_type'] == 'repost' and 'reposted_claim' in item and item['reposted_claim']['value_type'] == 'stream' and item['reposted_claim']['value']['stream_type'] == 'video':
            stream_item = item['reposted_claim']
            # nsfw?
            if 'tags' in stream_item['value']:
                if 'mature' in stream_item['value']['tags'] and not nsfw:
                    continue

            li = to_video_listitem(stream_item, playlist, channel, repost=item)
            url = plugin.url_for(claim_play, uri=serialize_uri(stream_item))

            items.append((url, li))
        elif item['value_type'] == 'channel':
            li = ListItem('[B]%s[/B]' % item['name'])
            li.setProperty('IsFolder','true')
            if 'thumbnail' in item['value'] and 'url' in item['value']['thumbnail']:
                li.setArt({
                    'thumb': item['value']['thumbnail']['url'],
                    'poster': item['value']['thumbnail']['url'],
                    'fanart': item['value']['thumbnail']['url']
                })
            url = plugin.url_for(lbry_channel, uri=serialize_uri(item['name'] + '#' + item['claim_id']),page=1)
            items.append((url, li, True))
        else:
            xbmc.log('ignored item, value_type=' + item['value_type'])
            xbmc.log('item name=' + item['name'])

    return items

@plugin.route('/')
def lbry_root():
    addDirectoryItem(ph, plugin.url_for(plugin_follows), ListItem(tr(30200)), True)
    #addDirectoryItem(ph, plugin.url_for(plugin_playlists), ListItem(tr(30210)), True)
    addDirectoryItem(ph, plugin.url_for(plugin_playlist, name=quote_plus(tr(30211))), ListItem(tr(30211)), True)
    addDirectoryItem(ph, plugin.url_for(lbry_new, page=1), ListItem(tr(30202)), True)
    addDirectoryItem(ph, plugin.url_for(lbry_search), ListItem(tr(30201)), True)
    endOfDirectory(ph)

#@plugin.route('/playlists')
#def plugin_playlists():
#    addDirectoryItem(ph, plugin.url_for(plugin_playlist, name=quote_plus(tr(30211))), ListItem(tr(30211)), True)
#    endOfDirectory(ph)

@plugin.route('/playlist/list/<name>')
def plugin_playlist(name):
    name = unquote_plus(name)
    uris = load_playlist(name)
    claim_info = call_rpc('resolve', {'urls': uris})
    items = []
    for uri in uris:
        items.append(claim_info[uri])
    items = result_to_itemlist(items, playlist=name)
    addDirectoryItems(ph, items, items_per_page)
    endOfDirectory(ph)

@plugin.route('/playlist/add/<name>/<uri>')
def plugin_playlist_add(name,uri):
    name = unquote_plus(name)
    uri = deserialize_uri(uri)
    items = load_playlist(name)
    if not uri in items:
        items.append(uri)
    save_playlist(name, items)

@plugin.route('/playlist/del/<name>/<uri>')
def plugin_playlist_del(name,uri):
    name = unquote_plus(name)
    uri = deserialize_uri(uri)
    items = load_playlist(name)
    items.remove(uri)
    save_playlist(name, items)
    xbmc.executebuiltin('Container.Refresh')

@plugin.route('/follows')
def plugin_follows():
    channels = load_channel_subs()
    resolve_uris = []
    for (name,claim_id) in channels:
        resolve_uris.append(name+'#'+claim_id)
    channel_infos = call_rpc('resolve', {'urls': resolve_uris})

    for (name,claim_id) in channels:
        uri = name+'#'+claim_id
        channel_info = channel_infos[uri]
        li = ListItem(name)
        if not 'error' in channel_info:
            plot = ''
            if 'title' in channel_info['value'] and channel_info['value']['title'].strip() != '':
                plot = '[B]%s[/B]\n' % channel_info['value']['title']
            else:
                plot = '[B]%s[/B]\n' % channel_info['name']
            if 'description' in channel_info['value']:
                plot = plot + channel_info['value']['description']
            infoLabels = { 'plot': plot }
            li.setInfo('video', infoLabels)

            if 'thumbnail' in channel_info['value'] and 'url' in channel_info['value']['thumbnail']:
                li.setArt({
                    'thumb': channel_info['value']['thumbnail']['url'],
                    'poster': channel_info['value']['thumbnail']['url'],
                    'fanart': channel_info['value']['thumbnail']['url']
                })

        menu = []
        menu.append((
            tr(30206) % name, 'RunPlugin(%s)' % plugin.url_for(plugin_unfollow, uri=serialize_uri(uri))
        ))
        li.addContextMenuItems(menu)
        addDirectoryItem(ph, plugin.url_for(lbry_channel, uri=serialize_uri(uri), page=1), li, True)
    endOfDirectory(ph)

@plugin.route('/follows/add/<uri>')
def plugin_follow(uri):
    uri = deserialize_uri(uri)
    channels = load_channel_subs()
    channel = (uri.split('#')[0],uri.split('#')[1])
    if not channel in channels:
        channels.append(channel)
    save_channel_subs(channels)

@plugin.route('/follows/del/<uri>')
def plugin_unfollow(uri):
    uri = deserialize_uri(uri)
    channels = load_channel_subs()
    channels.remove((uri.split('#')[0],uri.split('#')[1]))
    save_channel_subs(channels)
    xbmc.executebuiltin('Container.Refresh')

@plugin.route('/new/<page>')
def lbry_new(page):
    page = int(page)
    query = {'page': page, 'page_size': items_per_page, 'order_by': 'release_time'}
    if not ADDON.getSettingBool('server_filter_disable'):
        query['stream_types'] = ['video']
    result = call_rpc('claim_search', query)
    items = result_to_itemlist(result['items'])
    addDirectoryItems(ph, items, result['page_size'])
    total_pages = int(result['total_pages'])
    if total_pages > 1 and page < total_pages:
        addDirectoryItem(ph, plugin.url_for(lbry_new, page=page+1), ListItem(tr(30203)), True)
    endOfDirectory(ph)

@plugin.route('/channel/<uri>')
def lbry_channel_landing(uri):
    lbry_channel(uri,1)

@plugin.route('/channel/<uri>/<page>')
def lbry_channel(uri,page):
    uri = deserialize_uri(uri)
    page = int(page)
    query = {'page': page, 'page_size': items_per_page, 'order_by': 'release_time', 'channel': uri}
    if not ADDON.getSettingBool('server_filter_disable'):
        query['stream_types'] = ['video']
    result = call_rpc('claim_search', query)
    items = result_to_itemlist(result['items'], channel=uri)
    addDirectoryItems(ph, items, result['page_size'])
    total_pages = int(result['total_pages'])
    if total_pages > 1 and page < total_pages:
        addDirectoryItem(ph, plugin.url_for(lbry_channel, uri=serialize_uri(uri), page=page+1), ListItem(tr(30203)), True)
    endOfDirectory(ph)

@plugin.route('/search')
def lbry_search():
    query = dialog.input(tr(30209))
    lbry_search_pager(quote_plus(query), 1)

@plugin.route('/search/<query>/<page>')
def lbry_search_pager(query, page):
    query = unquote_plus(query)
    page = int(page)
    if query != '':
        params = {'text': query, 'page': page, 'page_size': items_per_page, 'order_by': 'release_time'}
        #always times out on server :(
        #if not ADDON.getSettingBool('server_filter_disable'):
        #    params['stream_types'] = ['video']
        result = call_rpc('claim_search', params)
        items = result_to_itemlist(result['items'])
        addDirectoryItems(ph, items, result['page_size'])
        total_pages = int(result['total_pages'])
        if total_pages > 1 and page < total_pages:
            addDirectoryItem(ph, plugin.url_for(lbry_search_pager, query=quote_plus(query), page=page+1), ListItem(tr(30203)), True)
        endOfDirectory(ph)
    else:
        endOfDirectory(ph, False)

def user_payment_confirmed(claim_info):
    # paid for claim already?
    purchase_info = call_rpc('purchase_list', {'claim_id': claim_info['claim_id']})
    if len(purchase_info['items']) > 0:
        return True

    account_list = call_rpc('account_list')
    for account in account_list['items']:
        if account['is_default']:
            balance = float(str(account['satoshis'])[:-6]) / float(100)
    dtext = tr(30214) % (float(claim_info['value']['fee']['amount']), str(claim_info['value']['fee']['currency']))
    dtext = dtext + '\n\n' + tr(30215) % (balance, str(claim_info['value']['fee']['currency']))
    return dialog.yesno(tr(30204), dtext)

@plugin.route('/play/<uri>')
def claim_play(uri):
    uri = deserialize_uri(uri)

    claim_info = call_rpc('resolve', {'urls': uri})[uri]
    if 'error' in claim_info:
        dialog.notification(tr(30102), claim_info['error']['name'], NOTIFICATION_ERROR)
        return

    if 'fee' in claim_info['value']:
        if claim_info['value']['fee']['currency'] != 'LBC':
            dialog.notification(tr(30204), tr(30103), NOTIFICATION_ERROR)
            return

        if not user_payment_confirmed(claim_info):
            return

    result = call_rpc('get', {'uri': uri, 'save_file': False})
    stream_url = result['streaming_url'].replace('0.0.0.0','127.0.0.1')

    (url,li) = result_to_itemlist([claim_info])[0]
    li.setPath(stream_url)
    setResolvedUrl(ph, True, li)

@plugin.route('/download/<uri>')
def claim_download(uri):
    uri = deserialize_uri(uri)

    claim_info = call_rpc('resolve', {'urls': uri})[uri]
    if 'error' in claim_info:
        dialog.notification(tr(30102), claim_info['error']['name'], NOTIFICATION_ERROR)
        return

    if 'fee' in claim_info['value']:
        if claim_info['value']['fee']['currency'] != 'LBC':
            dialog.notification(tr(30204), tr(30103), NOTIFICATION_ERROR)
            return

        if not user_payment_confirmed(claim_info):
            return

    result = call_rpc('get', {'uri': uri, 'save_file': True})

def run():
    try:
        plugin.run()
    except PluginException as e:
        xbmc.log("PluginException: " + str(e))
