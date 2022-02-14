# -*- coding: utf-8 -*-
from __future__ import absolute_import

import xbmc
import xbmcaddon
from xbmcgui import ListItem, Dialog, NOTIFICATION_ERROR, Window, WindowXML
from xbmcplugin import addDirectoryItem, addDirectoryItems, endOfDirectory, setContent, setResolvedUrl

import routing
import requests
import time

# python2 and 3
try:
    from urllib import quote,unquote,quote_plus,unquote_plus
except:
    from urllib.parse import quote,unquote,quote_plus,unquote_plus

from resources.lib.local import *
from resources.lib.exception import *

ADDON = xbmcaddon.Addon()
tr = ADDON.getLocalizedString
lbry_api_url = unquote(ADDON.getSetting('lbry_api_url'))
if lbry_api_url == '':
    raise Exception('Lbry API URL is undefined.')
using_lbry_proxy = lbry_api_url.find('api.lbry.tv') != -1

odysee_comment_api_url = 'https://comments.odysee.com/api/v2'

# assure profile directory exists
profile_path = ADDON.getAddonInfo('profile')
if not xbmcvfs.exists(profile_path):
    xbmcvfs.mkdir(profile_path)

items_per_page = ADDON.getSettingInt('items_per_page')
nsfw = ADDON.getSettingBool('nsfw')

plugin = routing.Plugin()
ph = plugin.handle
setContent(ph, 'videos')
dialog = Dialog()

def call_rpc(method, params={}, errdialog=True):
    try:
        xbmc.log('call_rpc: url=' + lbry_api_url + ', method=' + method + ', params=' + str(params))
        headers = {'content-type' : 'application/json'}
        json = { 'jsonrpc' : '2.0', 'id' : 1, 'method': method, 'params': params }
        result = requests.post(lbry_api_url, headers=headers, json=json)
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

def call_comment_rpc(method, params={}, errdialog=True):
    try:
        xbmc.log('call_comment_rpc: url=' + odysee_comment_api_url + ', method=' + method + ', params=' + str(params))
        headers = {'content-type' : 'application/json'}
        json = { 'jsonrpc' : '2.0', 'id' : 1, 'method': method, 'params': params }
        result = requests.post(odysee_comment_api_url, headers=headers, json=json)
        result.raise_for_status()
        rjson = result.json()
        if 'error' in rjson:
            raise PluginException(rjson['error']['message'])
        return result.json()['result']
    except requests.exceptions.ConnectionError as e:
        if errdialog:
            dialog.notification(tr(30105), tr(30108), NOTIFICATION_ERROR)
        raise PluginException(e)
    except requests.exceptions.HTTPError as e:
        if errdialog:
            dialog.notification(tr(30101), str(e), NOTIFICATION_ERROR)
        raise PluginException(e)
    except PluginException as e:
        if errdialog:
            dialog.notification(tr(30107), str(e), NOTIFICATION_ERROR)
        raise e
    except Exception as e:
        xbmc.log('call_comment_rpc exception:' + str(e))
        raise e

# Sign data if a user channel is selected
def sign(data):
    user_channel = get_user_channel()
    if not user_channel:
        return None

    # assume data type is str
    if type(data) is not str:
        raise Exception('attempt to sign non-str type')

    toHex = lambda x : "".join([format(ord(c),'02x') for c in x])

    return call_rpc('channel_sign', params={'channel_id': user_channel[1], 'hexdata': toHex(bdata)})


def serialize_uri(item):
    # all uris passed via kodi's routing system must be urlquoted
    if type(item) is dict:
        return quote(item['name'].encode('utf-8') + '#' + item['claim_id'].encode('utf-8'))
    else:
        return quote(item.encode('utf-8'))

def deserialize_uri(item):
    # all uris passed via kodi's routing system must be utf-8 encoded and urlquoted
    item = str(item) # we get item as unicode
    return unquote(item).decode('utf-8')

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
        if 'signing_channel' in item and 'name' in item['signing_channel']:
            comment_uri = item['signing_channel']['name'] + '#' + item['signing_channel']['claim_id'] + '#' + item['claim_id']
            menu.append((
                tr(30238), 'RunPlugin(%s)' % plugin.url_for(plugin_comment_show, uri=serialize_uri(comment_uri))
            ))

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
        if item['value_type'] == 'stream' and 'stream_type' in item['value'] and item['value']['stream_type'] == 'video':
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
            li = ListItem('[B]%s[/B] [I]#%s[/I]' % (item['name'], item['claim_id'][0:4]))
            li.setProperty('IsFolder','true')
            if 'thumbnail' in item['value'] and 'url' in item['value']['thumbnail']:
                li.setArt({
                    'thumb': item['value']['thumbnail']['url'],
                    'poster': item['value']['thumbnail']['url'],
                    'fanart': item['value']['thumbnail']['url']
                })
            url = plugin.url_for(lbry_channel, uri=serialize_uri(item),page=1)

            menu = []
            ch_name = item['name']
            menu.append((
                tr(30205) % ch_name, 'RunPlugin(%s)' % plugin.url_for(plugin_follow, uri=serialize_uri(item))
            ))
            li.addContextMenuItems(menu)

            items.append((url, li, True))
        else:
            xbmc.log('ignored item, value_type=' + item['value_type'])
            xbmc.log('item name=' + item['name'].encode('utf-8'))

    return items

def get_user_channel():
    user_channel_str = ADDON.getSettingString('user_channel')
    if user_channel_str:
        toks = user_channel_str.split('#')
        if len(toks) == 2:
            return (toks[0], toks[1])
    return None

def set_user_channel(channel_name, channel_id):
    ADDON.setSettingString('user_channel', "%s#%s" % (channel_name, channel_id))
    ADDON.setSettingString('user_channel_vis', "%s#%s" % (channel_name, channel_id[:5]))

@plugin.route('/clear_user_channel')
def clear_user_channel():
    ADDON.setSettingString('user_channel', '')
    ADDON.setSettingString('user_channel_vis', '')

@plugin.route('/select_user_channel')
def select_user_channel():
    progressDialog = xbmcgui.DialogProgress()
    progressDialog.create(tr(30231))

    page = 1
    total_pages = 1
    items = []
    while page <= total_pages:
        if progressDialog.iscanceled():
            break

        try:
            params = {'page' : page}
            result = call_rpc('channel_list', params, errdialog=not using_lbry_proxy)
            total_pages = max(result['total_pages'], 1) # Total pages returns 0 if empty
            if 'items' in result:
                items += result['items']
            else:
                break
        except:
            pass

        page = page + 1
        progressDialog.update(int(100.0*page/total_pages), tr(30220) + ' %s/%s' % (page, total_pages))

    selected_item = None

    if len(items) == 0:
        progressDialog.update(100, tr(30232)) # No owned channels found
        xbmc.sleep(1000)
        progressDialog.close()
        return
    elif len(items) == 1:
        progressDialog.update(100, tr(30233)) # Found single user
        xbmc.sleep(1000)
        progressDialog.close()

        selected_item = items[0]
    else:
        progressDialog.update(100, tr(30234)) # Multiple users found
        xbmc.sleep(1000)
        progressDialog.close()

        names = []
        for item in items:
            names.append(item['name'])

        selected_name_index = dialog.select(tr(30239), names) # Post As

        if selected_name_index >= 0: # If not cancelled
            selected_item = items[selected_name_index]

    if selected_item:
        set_user_channel(selected_item['name'], selected_item['claim_id'])

class CommentWindow(WindowXML):
    def __init__(self, *args, **kwargs):
        self.channel_name = kwargs['channel_name']
        self.channel_id = kwargs['channel_id']
        self.claim_id = kwargs['claim_id']
        self.last_selected_position = -1
        WindowXML.__init__(self, args, kwargs)

    def onInit(self):
        self.refresh()

    def onAction(self, action):
        if action == xbmcgui.ACTION_CONTEXT_MENU:
            # Commenting is not supported
            if using_lbry_proxy:
                ret = dialog.contextmenu([tr(30240)]) # Only allow refreshing
                if ret == 0:
                    self.refresh()
                return

            # No user channel. Allow user to select an account or refresh.
            if not get_user_channel():
                ret = dialog.contextmenu([tr(30240)])
                if ret == 0:
                    self.refresh()
                return

            # User channel selected. Allow comment manipulation.
            user_channel = get_user_channel()
            if get_user_channel():
                ccl = self.get_comment_control_list()
                selected_pos = ccl.getSelectedPosition()
                item = ccl.getSelectedItem()

                menu = []
                offsets = []
                offset = 0
                invalid_offset = 10000
                if item:
                    comment_id = item.getProperty('id')

                    menu.append(tr(30226)) # Like
                    offsets.append(0)

                    menu.append(tr(30227)) # Dislike
                    offsets.append(1)

                    menu.append(tr(30228)) # Clear Vote
                    offsets.append(2)

                    offset = 3
                else:
                    offsets.append(invalid_offset)
                    offsets.append(invalid_offset)
                    offsets.append(invalid_offset)
                    offset = 0

                menu.append(tr(30221)) # New comment
                offsets.append(offset)
                offset = offset + 1

                if item:
                    menu.append(tr(30222)) # Reply
                    offsets.append(offset)
                    offset = offset + 1

                    if item.getProperty('channel_id') == get_user_channel()[1]:

                        menu.append(tr(30223)) # Edit
                        offsets.append(offset)
                        offset = offset + 1

                        menu.append(tr(30224)) # Remove
                        offsets.append(offset)
                        offset = offset + 1
                    else:
                        offsets.append(invalid_offset)
                        offsets.append(invalid_offset)
                else:
                    offsets.append(invalid_offset)
                    offsets.append(invalid_offset)
                    offsets.append(invalid_offset)

                menu.append(tr(30240)) # Refresh
                offsets.append(offset)

                ret = dialog.contextmenu(menu)

                if ret == offsets[0]: # Like
                    self.like(comment_id)
                    item.setProperty('my_vote', str(1))
                    self.refresh_label(item)

                elif ret == offsets[1]: # Dislike
                    self.dislike(comment_id)
                    item.setProperty('my_vote', str(-1))
                    self.refresh_label(item)

                elif ret == offsets[2]: # Clear Vote
                    self.neutral(comment_id, item.getProperty('my_vote'))
                    item.setProperty('my_vote', str(0))
                    self.refresh_label(item)

                elif ret == offsets[3]: # New Comment
                    comment = dialog.input(tr(30221), type=xbmcgui.INPUT_ALPHANUM)
                    if comment:
                        comment_id = self.create_comment(comment)

                        # Remove 'No Comments' item
                        if ccl.size() == 1 and ccl.getListItem(0).getLabel() == tr(30230):
                            ccl.reset()

                        # Add new comment item
                        ccl.addItem(self.create_list_item(comment_id, user_channel[0], user_channel[1], 0, 0, comment, 0, 1))
                        ccl.selectItem(ccl.size()-1)

                elif ret == offsets[4]: # Reply
                    comment = dialog.input(tr(30222), type=xbmcgui.INPUT_ALPHANUM)
                    if comment:
                        comment_id = self.create_comment(comment, comment_id)

                        # Insert new item by copying the list (no XMBC method to allow a fast insertion).
                        newItems = []
                        for i in range(selected_pos+1):
                            newItems.append(self.copy_list_item(ccl.getListItem(i)))
                        newItems.append(self.create_list_item(comment_id, user_channel[0], user_channel[1], 0, 0, comment, int(item.getProperty('indent'))+1, 1))
                        for i in range(selected_pos+1, ccl.size()):
                            newItems.append(self.copy_list_item(ccl.getListItem(i)))

                        ccl.reset()
                        ccl.addItems(newItems)
                        ccl.selectItem(selected_pos+1)

                elif ret == offsets[5]: # Edit
                    id = item.getProperty('id');
                    comment = item.getProperty('comment')
                    comment = dialog.input(tr(30223), type=xbmcgui.INPUT_ALPHANUM, defaultt=comment)
                    if comment:
                        self.edit_comment(id, comment)
                        item.setProperty('comment', comment)
                        self.refresh_label(item)

                elif ret == offsets[6]: # Change User
                    indentRemoved = item.getProperty('indent')
                    self.remove_comment(comment_id)
                    ccl.removeItem(selected_pos)

                    while True:
                        if selected_pos == ccl.size():
                            break
                        indent = ccl.getListItem(selected_pos).getProperty('indent')
                        if indent <= indentRemoved:
                            break
                        ccl.removeItem(selected_pos)

                    if selected_pos > 0:
                        ccl.selectItem(selected_pos-1)

                    if ccl.size() == 0:
                        ccl.addItem(ListItem(label=tr(30230)))

                elif ret == offsets[7]: # Refresh
                    self.refresh()

        else:
            WindowXML.onAction(self, action)

        # If an action changes the selected item position refresh the label
        ccl = self.get_comment_control_list()
        if self.last_selected_position != ccl.getSelectedPosition():
            if self.last_selected_position >= 0 and self.last_selected_position < ccl.size():
                oldItem = ccl.getListItem(self.last_selected_position)
                if oldItem:
                    self.refresh_label(oldItem, False)
            newItem = ccl.getSelectedItem()
            if newItem:
                self.refresh_label(newItem, True)
            self.last_selected_position = ccl.getSelectedPosition()

    def fetch_comment_list(self, page):
        return call_comment_rpc('comment.List', params={"page":page,"page_size":50,'include_replies':True,'visible':False,'hidden':False,'top_level':False,'channel_name':self.channel_name,'channel_id':self.channel_id,'claim_id':self.claim_id,'sort_by':0})

    def fetch_react_list(self, comment_ids):
        user_channel = get_user_channel()
        params = {'comment_ids' : comment_ids }
        if user_channel:
            params['channel_name'] = user_channel[0]
            params['channel_id'] = user_channel[1]
            self.sign(user_channel[0], params)
        return call_comment_rpc('reaction.List', params=params)

    def refresh(self):
        self.last_selected_position = -1
        progressDialog = xbmcgui.DialogProgress()
        progressDialog.create(tr(30219), tr(30220) + ' 1')

        ccl = self.get_comment_control_list()

        page = 1
        result = self.fetch_comment_list(page)
        total_pages = result['total_pages']

        while page < total_pages:
            if progressDialog.iscanceled():
                break
            progressDialog.update(int(100.0*page/total_pages), tr(30220) + " %s/%s" % (page + 1, total_pages))
            page = page+1
            result['items'] += self.fetch_comment_list(page)['items']

        if 'items' in result:
            ccl.reset()
            items = result['items']

            # Grab the likes and dislikes.
            comment_ids = ''
            for item in items:
                comment_ids += item['comment_id'] + ','
            result = self.fetch_react_list(comment_ids)
            others_reactions = result['others_reactions']

            # Items are returned newest to oldest which implies that child comments are always before their parents.
            # Iterate from oldest to newest comments building up a pre-order traversal ordering of the comment tree. Order
            # the tree roots by decreasing score (likes-dislikes).
            sort_indices = []
            i = len(items)-1
            while i >= 0:
                item = items[i]
                comment_id = item['comment_id']
                if 'parent_id' in item and item['parent_id'] != 0:
                    for j in range(len(sort_indices)): # search for the parent in the sorted index list
                        sorted_item = items[sort_indices[j][0]]
                        indent = sort_indices[j][1]
                        if sorted_item['comment_id'] == item['parent_id']: # found the parent
                            # Insert at the end of the subtree of the parent. Use the indentation to figure
                            # out where the end is.
                            while j+1 < len(sort_indices):
                                if sort_indices[j+1][1] > indent: # Item with index j+1 is in the child subtree
                                    j = j+1
                                else: # Item with index j+1 is not in the child subtree. Break and insert before this item.
                                    break
                            sort_indices.insert(j+1, (i, indent+1, 0))
                            break
                else:
                    reaction = others_reactions[comment_id]
                    likes = reaction['like']
                    dislikes = reaction['dislike']
                    score = likes-dislikes

                    j = 0
                    insert_index = len(sort_indices)
                    while j < len(sort_indices):
                        if sort_indices[j][1] == 0 and score > sort_indices[j][2]:
                            insert_index = j
                            break
                        j = j+1

                    sort_indices.insert(insert_index, (i, 0, score))

                i -= 1

            for (index,indent,score) in sort_indices:
                item = items[index]
                channel_name = item['channel_name']
                channel_id = item['channel_id']
                comment = item['comment']
                comment_id = item['comment_id']
                reaction = result['others_reactions'][comment_id]
                likes = reaction['like']
                dislikes = reaction['dislike']

                if 'my_reactions' in result:
                    my_reaction = result['my_reactions'][comment_id]
                    my_vote = my_reaction['like'] - my_reaction['dislike']
                else:
                    my_vote = 0

                ccl.addItem(self.create_list_item(comment_id, channel_name, channel_id, likes, dislikes, comment, indent, my_vote))
        else:
            if ccl.size() == 0:
                ccl.addItem(ListItem(label=tr(30230))) # No Comments

        progressDialog.update(100)
        progressDialog.close()

    def get_comment_control_list(self):
        return self.getControl(1)

    def create_list_item(self, comment_id, channel_name, channel_id, likes, dislikes, comment, indent, my_vote):
        li = ListItem(label=self.create_label(channel_name, channel_id, likes, dislikes, comment, indent, my_vote))
        li.setProperty('id', comment_id)
        li.setProperty('channel_name', channel_name)
        li.setProperty('channel_id', channel_id)
        li.setProperty('likes', str(likes))
        li.setProperty('dislikes', str(dislikes))
        li.setProperty('comment', comment)
        li.setProperty('indent', str(indent))
        li.setProperty('my_vote', str(my_vote))
        return li

    def copy_list_item(self, li):
        li_copy = ListItem(label=li.getLabel())
        li_copy.setProperty('id', li.getProperty('id'))
        li_copy.setProperty('channel_name', li.getProperty('channel_name'))
        li_copy.setProperty('channel_id', li.getProperty('channel_id'))
        li_copy.setProperty('likes', li.getProperty('likes'))
        li_copy.setProperty('dislikes', li.getProperty('dislikes'))
        li_copy.setProperty('comment', li.getProperty('comment'))
        li_copy.setProperty('indent', li.getProperty('indent'))
        li_copy.setProperty('my_vote', li.getProperty('my_vote'))
        return li_copy

    def refresh_label(self, li, selected=True):
        li.getProperty('id');
        channel_name = li.getProperty('channel_name')
        channel_id = li.getProperty('channel_id')
        likes = int(li.getProperty('likes'))
        dislikes = int(li.getProperty('dislikes'))
        comment = li.getProperty('comment')
        indent = int(li.getProperty('indent'))
        my_vote = int(li.getProperty('my_vote'))
        li.setLabel(self.create_label(channel_name, channel_id, likes, dislikes, comment, indent, my_vote, selected))

    def create_label(self, channel_name, channel_id, likes, dislikes, comment, indent, my_vote, selected=False):
        user_channel = get_user_channel()
        if user_channel and user_channel[1] == channel_id:
            color = 'red' if selected else 'green'
            channel_name = '[COLOR ' + color + ']' + channel_name + '[/COLOR]'

        if my_vote == 1:
            likes = '[COLOR green]' + str(likes+1) + '[/COLOR]'
            dislikes = str(dislikes)
        elif my_vote == -1:
            likes = str(likes)
            dislikes = '[COLOR green]' + str(dislikes+1) + '[/COLOR]'
        else:
            likes = str(likes)
            dislikes = str(dislikes)

        lilabel = channel_name + ' [COLOR orange]' + likes + '/' + dislikes + '[/COLOR] [COLOR white]' + comment + '[/COLOR]'

        padding = ''
        for i in range(indent):
            padding += '   '
        lilabel = padding + lilabel

        return lilabel

    def sign(self, data, params):
        res = sign(data)
        params['signature'] = res['signature']
        params['signing_ts'] = res['signing_ts']

    def create_comment(self, comment, parent_id=None):
        user_channel = get_user_channel()
        progressDialog = xbmcgui.DialogProgress()
        progressDialog.create(tr(30241), tr(30242))
        params = { 'claim_id' : self.claim_id, 'comment' : comment, 'channel_id' : user_channel[1] }
        if parent_id:
            params['parent_id'] = parent_id
        self.sign(comment, params)
        res = call_comment_rpc('comment.Create', params)
        self.like(res['comment_id'])
        progressDialog.close()
        return res['comment_id']

    def edit_comment(self, comment_id, comment):
        user_channel = get_user_channel()
        params = { 'comment_id' : comment_id, 'comment' : comment }
        self.sign(comment, params)
        return call_comment_rpc('comment.Edit', params)

    def remove_comment(self, comment_id):
        params = { 'comment_id' : comment_id }
        self.sign(comment_id, params)
        call_comment_rpc('comment.Abandon', params)

    def react(self, comment_id, current_vote=0, type=None):
        # No vote to clear
        if current_vote == '0' and type == None:
            return

        user_channel = get_user_channel()
        params = { 'comment_ids' : comment_id,
                'channel_name' : user_channel[0],
                'channel_id' : user_channel[1]
                }
        if type == 'like':
            params['clear_types'] = 'dislike'
            params['type'] = 'like'
        elif type == 'dislike':
            params['clear_types'] = 'like'
            params['type'] = 'dislike'
        else:
            params['remove'] = True
            params['type'] = 'dislike' if current_vote == '-1' else 'like'

        self.sign(user_channel[0], params)
        call_comment_rpc('reaction.React', params)

    def like(self, comment_id):
        self.react(comment_id, type='like')

    def dislike(self, comment_id):
        self.react(comment_id, type='dislike')

    def neutral(self, comment_id, current_vote):
        self.react(comment_id, current_vote=current_vote)

@plugin.route('/')
def lbry_root():
    addDirectoryItem(ph, plugin.url_for(plugin_follows), ListItem(tr(30200)), True)
    addDirectoryItem(ph, plugin.url_for(plugin_recent, page=1), ListItem(tr(30218)), True)
    #addDirectoryItem(ph, plugin.url_for(plugin_playlists), ListItem(tr(30210)), True)
    addDirectoryItem(ph, plugin.url_for(plugin_playlist, name=quote_plus(tr(30211))), ListItem(tr(30211)), True)
    #addDirectoryItem(ph, plugin.url_for(lbry_new, page=1), ListItem(tr(30202)), True)
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

@plugin.route('/recent/<page>')
def plugin_recent(page):
    page = int(page)
    channels = load_channel_subs()
    channel_ids = []
    for (name,claim_id) in channels:
        channel_ids.append(claim_id)
    query = {'page': page, 'page_size': items_per_page, 'order_by': 'release_time', 'channel_ids': channel_ids}
    if not ADDON.getSettingBool('server_filter_disable'):
        query['stream_types'] = ['video']
    result = call_rpc('claim_search', query)
    items = result_to_itemlist(result['items'])
    addDirectoryItems(ph, items, result['page_size'])
    total_pages = int(result['total_pages'])
    if total_pages > 1 and page < total_pages:
        addDirectoryItem(ph, plugin.url_for(plugin_recent, page=page+1), ListItem(tr(30203)), True)
    endOfDirectory(ph)

@plugin.route('/comments/show/<uri>')
def plugin_comment_show(uri):
    params = deserialize_uri(uri).split('#')
    win = CommentWindow('addon-lbry-comments.xml', xbmcaddon.Addon().getAddonInfo('path'), 'Default', channel_name=params[0], channel_id=params[1], claim_id=params[2])
    win.doModal()
    del win

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

    call_rpc('get', {'uri': uri, 'save_file': True})

def run():
    try:
        plugin.run()
    except PluginException as e:
        xbmc.log("PluginException: " + str(e))
