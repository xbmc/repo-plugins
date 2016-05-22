import sys
import routing
import urllib
from config import config
from api import API
from user import User
from xbmc import log, executebuiltin, Player
from xbmcgui import ListItem, Dialog
from xbmcplugin import addDirectoryItem, endOfDirectory
from xbmcaddon import Addon


plugin = routing.Plugin()
addon = Addon(config['addon']['id'])
api = API(addon)


@plugin.route('/')
def index():
    """
    Main addon page
    :return:
    """
    for item in api.get_categories():
        # list item:
        li = ListItem(item['name'], iconImage=item['image'], thumbnailImage=item['image'])
        li.setArt({
            'fanart': item['image']
        })
        # diretory item:
        addDirectoryItem(
            plugin.handle,
            plugin.url_for(show_subcategories, category_id=item['id'])
                                  if item['id'] != 99 else
                                  plugin.url_for(show_favorites),
            li,
            True
        )
    # end of directory:
    endOfDirectory(plugin.handle)


@plugin.route('/category/<category_id>')
def show_subcategories(category_id):
    """
    Sub-categories page
    :param category_id:
    :return:
    """
    for item in api.get_subcategories(int(category_id)):
        # list item:
        li = ListItem(item['name'].capitalize(),
            iconImage='{0}/{1}'.format(config['urls']['calm_arts_host'], item['image']),
            thumbnailImage='{0}/{1}'.format(config['urls']['calm_arts_host'], item['image']))
        li.setArt({
            'fanart': 'special://home/addons/{0}/resources/media/fanart/subcategory-{1}.jpg'
                .format(config['addon']['id'], item['id'])
        })
        # diretory item:
        addDirectoryItem(
            plugin.handle,
            plugin.url_for(show_channels, category_id=category_id, subcategory_id=item['id']),
            li,
            True
        )
    # end of directory:
    endOfDirectory(plugin.handle)


@plugin.route('/category/<category_id>/subcategory/<subcategory_id>')
def show_channels(category_id, subcategory_id):
    """
    Channels page
    :param category_id:
    :param subcategory_id:
    :return:
    """
    for item in api.get_channels(int(subcategory_id)):
        # list item:
        li = ListItem(u'{0} {1}'.format(item['title'].replace('CALM RADIO -', '').title(), '(VIP)' if 'free' not in item['streams'] else ''),
            iconImage='{0}/{1}'.format(config['urls']['calm_arts_host'], item['image']),
            thumbnailImage='{0}/{1}'.format(config['urls']['calm_arts_host'], item['image']))
        li.setArt({
            'fanart': 'special://home/addons/{0}/resources/media/fanart/channel-{1}.jpg'
                .format(config['addon']['id'], item['id'])
        })
        li.addContextMenuItems(
            [(addon.getLocalizedString(32300), 'RunPlugin(plugin://{0}/favorites/add/{1})'
              .format(config['addon']['id'], item['id']))]
        )
        # diretory item:
        addDirectoryItem(
            plugin.handle,
            plugin.url_for(play_channel,
                           category_id=category_id,
                           subcategory_id=subcategory_id,
                           channel_id=item['id']),
            li
        )
    # end of directory:
    endOfDirectory(plugin.handle)


@plugin.route('/favorites')
def show_favorites():
    """
    User's favorite channels list
    :return:
    """
    user = User(addon)
    is_authenticated = user.authenticate()

    if is_authenticated:
        favorites = api.get_favorites(user.username, user.token)
        if len(favorites) > 0:
            for item in favorites:
                path = api.get_url(item['streams'],
                                   user.username,
                                   user.token,
                                   user.is_authenticated()
                                   )
                # list item:
                li = ListItem(u'{0} {1}'.format(item['title'].replace('CALM RADIO -', '').title(), '(VIP)' if 'free' not in item['streams'] else ''),
                              iconImage='{0}/{1}'.format(config['urls']['calm_arts_host'], item['image']),
                              thumbnailImage='{0}/{1}'.format(config['urls']['calm_arts_host'], item['image']),
                              path=path
                              )
                li.setArt({'thumb': '{0}/{1}'.format(config['urls']['calm_arts_host'], item['image']),
                   'fanart': 'special://home/addons/{0}/resources/media/fanart/channel-{1}.jpg'
                          .format(config['addon']['id'], item['id']) })
                li.setInfo('music', {'Title': item['title'].replace('CALM RADIO -', '').title(), 'Artist': item['description']})
                li.setProperty('mimetype', 'audio/mpeg')
                li.setProperty('IsPlayable', 'true')
                li.setInfo('music', {
                    'Title': item['title'].replace('CALM RADIO -', '').title(),
                    'Artist_Description': item['description'],
                })
                li.addContextMenuItems(
                    [(addon.getLocalizedString(32301), 'RunPlugin(plugin://{0}/favorites/remove/{1})'
                      .format(config['addon']['id'], item['id']))]
                )
                # diretory item:
                addDirectoryItem(
                    plugin.handle,
                    path,
                    li
                )
            # end of directory:
            endOfDirectory(plugin.handle)
        # favorites list is empty:
        else:
            executebuiltin('Notification("{0}", "{1}")'
                           .format(addon.getLocalizedString(30000), addon.getLocalizedString(32306)))
    # user is not authenticated:
    else:
        executebuiltin('Notification("{0}", "{1}")'
                           .format(addon.getLocalizedString(30000), addon.getLocalizedString(32110)))


@plugin.route('/category/<category_id>/subcategory/<subcategory_id>/channel/<channel_id>')
def play_channel(category_id, subcategory_id, channel_id):
    """
    Plays selected song
    :param category_id:
    :param subcategory_id:
    :param channel_id:
    :return:
    """
    user = User(addon)
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
        li = ListItem(channel['title'], channel['description'], channel['image'])
        li.setArt({'thumb': '{0}/{1}'.format(config['urls']['calm_arts_host'], channel['image']),
                   'fanart': 'special://home/addons/{0}/resources/media/fanart/channel-{1}.jpg'
                  .format(config['addon']['id'], channel['id']) })
        li.setInfo('music', {'Title': channel['title'].replace('CALM RADIO -', '').title(), 'Artist': channel['description']})
        li.setProperty('mimetype', 'audio/mpeg')
        li.setProperty('IsPlayable', 'true')
        li.setInfo('music', {
            'Title': channel['title'].replace('CALM RADIO -', '').title(),
            'Artist_Description': channel['description'],
        })
        Player().play(item=url, listitem=li)
        # xbmc.executebuiltin('AlarmClock(Test, Notification("bla", "Blue"), 00:05, True, True)')
    else:
        dialog = Dialog()
        ret = dialog.yesno(addon.getLocalizedString(32200), addon.getLocalizedString(32201))
        if ret == 1:
            addon.openSettings()


@plugin.route('/favorites/add/<channel_id>')
def add_to_favorites(channel_id):
    """
    Adds a channels to user's favorites list
    :param channel_id: Channel ID
    :return:
    """
    user = User(addon)
    is_authenticated = user.authenticate()
    if is_authenticated:
        result = api.add_to_favorites(user.username, user.token, channel_id)
        executebuiltin('Notification("{0}", "{1}"'.format(addon.getLocalizedString(30000),
                                                      addon.getLocalizedString(32302) if result
                                                      else addon.getLocalizedString(32304)))
    else:
        executebuiltin('Notification("{0}", "{1}")'.format(addon.getLocalizedString(30000),
                                                           addon.getLocalizedString(32110)))


@plugin.route('/favorites/remove/<channel_id>')
def remove_from_favorites(channel_id):
    """
    Removes a channels from user's favorites list
    :param channel_id: Channel ID
    :return:
    """
    user = User(addon)
    is_authenticated = user.authenticate()
    if is_authenticated:
        result = api.remove_from_favorites(user.username, user.token, channel_id)
        executebuiltin('Container.Refresh')
        executebuiltin('Notification("{0}", "{1}")'.format(
            addon.getLocalizedString(30000),
            addon.getLocalizedString(32303) if result else addon.getLocalizedString(32305)
        ))
    else:
        executebuiltin('Notification("{0}", "{1}")'.format(
            addon.getLocalizedString(30000),
            addon.getLocalizedString(32110)
        ))

if __name__ == '__main__':
    plugin.run()
    if sys.argv[0] == 'plugin://{0}/'.format(config['addon']['id']) and not addon.getSetting('username'):
        executebuiltin('Notification("{0}", "{1}", 6000, "special://home/addons/{2}/icon.png")'
                       .format(addon.getLocalizedString(30000),
                               addon.getLocalizedString(32202),
                               config['addon']['id']))
