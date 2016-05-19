import sys
import urllib
from xbmcswift2 import Plugin, xbmc, xbmcgui, xbmcaddon, actions
from config import config
from api import API
from user import User


plugin = Plugin()
api = API(plugin)


@plugin.route('/')
def index():
    return plugin.finish([{
        'label': item['name'],
        'icon': item['image'],
        'path': plugin.url_for('show_subcategories', category_id=item['id'])
                              if item['id'] != 99 else
                              plugin.url_for('show_favorites'),
        'properties': {
            'fanart_image': item['image']
        },
        'info': {
            'Title': item['name'],
            'Artist': 'Calm Radio',
            'Artist_Description': item['description']
        }
    } for item in api.get_categories()])


@plugin.route('/category/<category_id>')
def show_subcategories(category_id):
    return plugin.finish([{
        'label': item['name'].capitalize(),
        'icon': '{0}/{1}'.format(config['urls']['calm_arts_host'], item['image']),
        'path': plugin.url_for('show_channels', category_id=category_id, subcategory_id=item['id']),
        'properties': {
            'fanart_image': 'special://home/addons/plugin.audio.calmradio/resources/media/fanart/subcategory-{0}.jpg'.format(item['id'])
        },
        'info': {
            'Title': item['name'],
            'Artist': plugin.get_string(30000)
        }
    } for item in api.get_subcategories(int(category_id))])


@plugin.route('/category/<category_id>/subcategory/<subcategory_id>')
def show_channels(category_id, subcategory_id):
    return plugin.finish([{
        'label': u'{0} {1}'.format(item['title'].replace('CALM RADIO -', '').title(), '(VIP)' if 'free' not in item['streams'] else ''),
        'icon': '{0}/{1}'.format(config['urls']['calm_arts_host'], item['image']),
        'path': plugin.url_for('play_channel',
                               category_id=category_id,
                               subcategory_id=subcategory_id,
                               channel_id=item['id']),
        'context_menu': [
            make_favorite_ctx(item['id'])
        ],
        'properties': {
            'fanart_image': 'special://home/addons/plugin.audio.calmradio/resources/media/fanart/channel-{0}.jpg'.format(item['id'])
        },
        'info': {
            'Title': item['title'],
            'Artist': plugin.get_string(30000),
            'Artist_Description': item['description']
        }
    } for item in api.get_channels(int(subcategory_id))])


@plugin.route('/favorites')
def show_favorites():
    user = User(plugin)
    is_authenticated = user.authenticate()

    if is_authenticated:
        favorites = api.get_favorites(user.username, user.token)
        if len(favorites) > 0:
            return plugin.finish([{
                'label': u'{0} {1}'.format(item['title'].replace('CALM RADIO -', '').title(), '(VIP)' if 'free' not in item['streams'] else ''),
                'icon': '{0}/{1}'.format(config['urls']['calm_arts_host'], item['image']),
                'path': api.get_url(item['streams'],
                              user.username,
                              user.token,
                              user.is_authenticated()),
                'context_menu': [
                    make_unfavorite_ctx(item['id'])
                ],
                'properties': {
                    'fanart_image': 'special://home/addons/plugin.audio.calmradio/resources/media/fanart/channel-{0}.jpg'.format(item['id'])
                },
                'info': {
                    'Title': item['title'],
                    'Artist': plugin.get_string(30000),
                    'Artist_Description': item['description']
                }
            } for item in favorites])
        else:
            plugin.notify(plugin.get_string(32306))
    else:
        plugin.notify(plugin.get_string(32110))


@plugin.route('/category/<category_id>/subcategory/<subcategory_id>/channel/<channel_id>')
def play_channel(category_id, subcategory_id, channel_id):
    user = User(plugin)
    user.authenticate()
    channel = [item for item in api.get_channels(int(subcategory_id))
               if item['id'] == int(channel_id)][0]
    url = api.get_url(channel['streams'],
                      user.username,
                      user.token,
                      user.is_authenticated())

    # is there a va;id URL for channel?
    if url:
        url = urllib.quote(url, safe=':/?=@')
        li = xbmcgui.ListItem(channel['title'], channel['description'], channel['image'])
        li.setArt({'thumb': '{0}/{1}'.format(config['urls']['calm_arts_host'], channel['image']),
                   'fanart': 'special://home/addons/plugin.audio.calmradio/resources/media/fanart/channel-{0}.jpg'.format(channel['id']) })
        li.setInfo('music', {'Title': channel['title'].replace('CALM RADIO -', '').title(), 'Artist': channel['description']})
        li.setProperty('mimetype', 'audio/mpeg')
        li.setProperty('IsPlayable', 'true')
        li.setInfo('music', {
            'Title': channel['title'].replace('CALM RADIO -', '').title(),
            'Artist_Description': channel['description'],
        })
        xbmc.Player().play(item=url, listitem=li)
        # xbmc.executebuiltin('ActivateScreensaver')
        # xbmc.executebuiltin('PlayMedia("special://home/addons/plugin.audio.calmradio/resources/media/video/clouds.mp4")')
        # xbmc.executebuiltin('AlarmClock(Test, Notification("bla", "Blue"), 00:05, True, True)')
    else:
        dialog = xbmcgui.Dialog()
        ret = dialog.yesno('Members Only Channel', 'To enjoy this channel and many other VIP channels:\n'
                                               '1. Open add-on settings and fill in your Calm Radio account details\n'
                                               '2. Verify that the account details you enetered are correct.\n'
                                               '3. Open http://calmradio.com and purchase a subscription\n\n'
                                               'Would you like to open the add-on settings window?')
        if ret == 1:
            plugin.open_settings()


@plugin.route('/favorites/add/<channel_id>')
def add_to_favorites(channel_id):
    """
    Adds a channels to user's favorites list
    :param channel_id: Channel ID
    :return:
    """
    user = User(plugin)
    is_authenticated = user.authenticate()
    if is_authenticated:
        result = api.add_to_favorites(user.username, user.token, channel_id)
        plugin.notify(plugin.get_string(32302) if result else plugin.get_string(32304))
    else:
        plugin.notify(plugin.get_string(32110))


@plugin.route('/favorites/remove/<channel_id>')
def remove_from_favorites(channel_id):
    """
    Removes a channels from user's favorites list
    :param channel_id: Channel ID
    :return:
    """
    user = User(plugin)
    is_authenticated = user.authenticate()
    if is_authenticated:
        result = api.remove_from_favorites(user.username, user.token, channel_id)
        plugin.redirect(plugin.url_for('index'))
        plugin.notify(plugin.get_string(32303) if result else plugin.get_string(32305))
    else:
        plugin.notify(plugin.get_string(32110))


def make_favorite_ctx(channel_id):
    return (plugin.get_string(32300),
            actions.background(plugin.url_for('add_to_favorites', channel_id=channel_id)))


def make_unfavorite_ctx(channel_id):
    return (plugin.get_string(32301),
            actions.background(plugin.url_for('remove_from_favorites', channel_id=channel_id)))


if __name__ == '__main__':
    plugin.run(plugin)
    # if not plugin.get_setting('username'):
    if sys.argv[0] == 'plugin://plugin.audio.calmradio/' and not plugin.get_setting('username'):
        plugin.notify(plugin.get_string(32202),
                      plugin.get_string(30000),
                      6000,
                      'special://home/addons/plugin.audio.calmradio/icon.png')
