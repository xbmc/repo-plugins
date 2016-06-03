import sys
import routing
from urllib import quote, urlretrieve
from time import time
from config import config
from api import API
from user import User
from xbmc import executebuiltin, Player, sleep, translatePath, log
from xbmcgui import ListItem, Dialog
from xbmcplugin import addDirectoryItem, endOfDirectory, setContent
from xbmcaddon import Addon
from intro import IntroWindow
from artwork import ArtworkWindow
import os


ADDON = Addon()
ADDON_HANDLE = int(sys.argv[1])
ADDON_ID = ADDON.getAddonInfo('id')
ADDON_NAME = ADDON.getAddonInfo('name')
ADDON_DATA_FOLDER = translatePath(ADDON.getAddonInfo('profile')).decode('utf-8')
PLUGIN = routing.Plugin()
api = API()
artwork = ArtworkWindow()


@PLUGIN.route('/')
def index():
    """
    Main add-on popup
    :return:
    """
    intro_window = IntroWindow(api)
    intro_window.doModal()
    category = intro_window.getProperty('category')
    if category:
        category = int(category)
        sub_category = int(intro_window.getProperty('sub_category'))
        del intro_window

        if category == 1:       # channels
            show_channels(category, sub_category) if category != 99 else show_favorites()
        elif category == 3:     # atmospheres
            show_subcategories(category)
        else:
            show_favorites()    # favorites


@PLUGIN.route('/category/<category_id>')
def show_subcategories(category_id):
    """
    Sub-categories page
    :param category_id: Selected category ID
    :return:
    """
    for item in api.get_subcategories(int(category_id)):
        # list item:
        li = ListItem(item['name'].capitalize(),
            iconImage='{0}/{1}'.format(config['urls']['calm_arts_host'], item['image']),
            thumbnailImage='{0}/{1}'.format(config['urls']['calm_arts_host'], item['image']))
        li.setArt({
            'fanart': '{0}{1}'.format(config['urls']['calm_blurred_arts_host'], item['image'])
        })
        # directory item:
        addDirectoryItem(
            PLUGIN.handle,
            PLUGIN.url_for(show_channels, category_id=category_id, subcategory_id=item['id']),
            li,
            True
        )
    # end of directory:
    endOfDirectory(PLUGIN.handle)
    executebuiltin('Container.SetViewMode(50)')


@PLUGIN.route('/category/<category_id>/subcategory/<subcategory_id>')
def show_channels(category_id, subcategory_id):
    """
    Channels page (playable)
    :param category_id: Selected category ID
    :param subcategory_id: Selected sub-category ID
    :return:
    """
    for item in api.get_channels(int(subcategory_id)):
        # list item:
        li = ListItem(u'{0} {1}'.format(item['title'].replace('CALM RADIO -', '').title(),
                                               ADDON.getLocalizedString(322023) if 'free' not in item['streams'] else '',
                                               item['description']),
            iconImage='{0}/{1}'.format(config['urls']['calm_arts_host'], item['image']),
            thumbnailImage='{0}/{1}'.format(config['urls']['calm_arts_host'], item['image']))
        li.setArt({
            'fanart': '{0}{1}'.format(config['urls']['calm_blurred_arts_host'], item['image'])
        })
        li.addContextMenuItems(
            [(ADDON.getLocalizedString(32300), 'RunPlugin(plugin://{0}/favorites/add/{1})'
              .format(ADDON_ID, item['id']))]
        )
        li.setInfo('music', {
            'Title': item['title'].replace('CALM RADIO -', '').title()
        })
        # directory item:
        addDirectoryItem(
            PLUGIN.handle,
            PLUGIN.url_for(play_channel,
                           category_id=category_id,
                           subcategory_id=subcategory_id,
                           channel_id=item['id']),
            li
        )
    # set the content of the directory
    setContent(ADDON_HANDLE, 'songs')
    # end of directory:
    endOfDirectory(PLUGIN.handle)
    executebuiltin('Container.SetViewMode(50)')


@PLUGIN.route('/favorites')
def show_favorites():
    """
    User's favorite channels list
    :return:
    """
    user = User()
    is_authenticated = user.authenticate()

    if is_authenticated:
        favorites = api.get_favorites(user.username, user.token)
        if len(favorites) > 0:
            for item in favorites:
                # list item:
                li = ListItem(u'{0} {1}'.format(item['title'].replace('CALM RADIO -', '').title(),
                                                       '(VIP)' if 'free' not in item['streams'] else '',
                                                       item['description']),
                    iconImage='{0}/{1}'.format(config['urls']['calm_arts_host'], item['image']),
                    thumbnailImage='{0}/{1}'.format(config['urls']['calm_arts_host'], item['image']))
                li.setArt({
                    'fanart': '{0}{1}'.format(config['urls']['calm_blurred_arts_host'], item['image'])
                })
                li.addContextMenuItems(
                    [(ADDON.getLocalizedString(32301), 'RunPlugin(plugin://{0}/favorites/remove/{1})'
                      .format(ADDON_ID, item['id']))]
                )
                # directory item:
                addDirectoryItem(
                    PLUGIN.handle,
                    PLUGIN.url_for(play_channel,
                                   category_id=None,
                                   subcategory_id=item['sub_category'],
                                   channel_id=item['id']),
                    li
                )
            # set the content of the directory
            setContent(ADDON_HANDLE, 'songs')
            # end of directory:
            endOfDirectory(PLUGIN.handle)
            executebuiltin('Container.SetViewMode(50)')
        # favorites list is empty:
        else:
            executebuiltin('Notification("{0}", "{1}")'
                           .format(ADDON.getLocalizedString(30000), ADDON.getLocalizedString(32306)))
    # user is not authenticated:
    else:
        executebuiltin('Notification("{0}", "{1}")'
                           .format(ADDON.getLocalizedString(30000), ADDON.getLocalizedString(32110)))


@PLUGIN.route('/category/<category_id>/subcategory/<subcategory_id>/channel/<channel_id>')
def play_channel(category_id, subcategory_id, channel_id):
    """
    Plays selected song
    :param category_id: Selected category ID
    :param subcategory_id: Selected sub-category ID
    :param channel_id: Selected channel ID
    :return:
    """
    global artwork
    last_album_cover = ''

    user = User()
    is_authenticated = user.authenticate()
    channel = [item for item in api.get_channels(int(subcategory_id))
               if item['id'] == int(channel_id)][0]
    url = api.get_streaming_url(channel['streams'],
                      user.username,
                      user.token,
                      user.is_authenticated())

    if is_authenticated:
        recent_tracks_url = channel['recent_tracks']['vip']
    elif 'free' in channel['recent_tracks']:
        recent_tracks_url = channel['recent_tracks']['free']

    # is there a valid URL for channel?
    if url:
        url = quote(url, safe=':/?=@')
        li = ListItem(channel['title'], channel['description'], channel['image'])
        li.setArt({'thumb': '{0}/{1}'.format(config['urls']['calm_arts_host'], channel['image']),
                   'fanart': '{0}{1}'.format(config['urls']['calm_blurred_arts_host'], channel['image']) })
        li.setInfo('music', {'Title': channel['title'].replace('CALM RADIO -', '').title(), 'Artist': channel['description']})
        li.setProperty('mimetype', 'audio/mpeg')
        li.setProperty('IsPlayable', 'true')
        li.setInfo('music', {
            'Title': channel['title'].replace('CALM RADIO -', '').title()
        })
        Player().play(item=url, listitem=li)

        log('Playing url: {0}'.format(url))

        # update now playing fanrt, channel name & description:
        artwork.overlay.setImage('{0}{1}'.format(config['urls']['calm_blurred_arts_host'], channel['image']))
        artwork.channel.setLabel(channel['title'])
        artwork.description.setLabel(channel['description'])
        artwork.show()

        while(artwork.getProperty('Closed') != 'True'):
            recent_tracks = api.get_json('{0}?{1}'.format(recent_tracks_url, str(int(time()))))
            if (last_album_cover != recent_tracks['now_playing']['album_art']):
                last_album_cover = recent_tracks['now_playing']['album_art']
                urlretrieve('{0}/{1}'.format(config['urls']['calm_arts_host'], recent_tracks['now_playing']['album_art']),
                                   '{0}{1}'.format(ADDON_DATA_FOLDER, recent_tracks['now_playing']['album_art']))
                artwork.cover.setImage('{0}/{1}'.format(ADDON_DATA_FOLDER, recent_tracks['now_playing']['album_art']))
                artwork.song.setLabel(recent_tracks['now_playing']['title'])
                artwork.album.setLabel(recent_tracks['now_playing']['album'])
                artwork.artist.setLabel(recent_tracks['now_playing']['artist'])
            sleep(10000)

        del artwork
    else:
        # members only access
        dialog = Dialog()
        ret = dialog.yesno(ADDON.getLocalizedString(32200), ADDON.getLocalizedString(32201))
        if ret == 1:
            ADDON.openSettings()


@PLUGIN.route('/favorites/add/<channel_id>')
def add_to_favorites(channel_id):
    """
    Adds a channels to user's favorites list
    :param channel_id: Channel ID
    :return:
    """
    user = User()
    is_authenticated = user.authenticate()
    if is_authenticated:
        result = api.add_to_favorites(user.username, user.token, channel_id)
        executebuiltin('Notification("{0}", "{1}"'.format(ADDON.getLocalizedString(30000),
                                                      ADDON.getLocalizedString(32302) if result
                                                      else ADDON.getLocalizedString(32304)))
    else:
        executebuiltin('Notification("{0}", "{1}")'.format(ADDON.getLocalizedString(30000),
                                                           ADDON.getLocalizedString(32110)))


@PLUGIN.route('/favorites/remove/<channel_id>')
def remove_from_favorites(channel_id):
    """
    Removes a channels from user's favorites list
    :param channel_id: Channel ID
    :return:
    """
    user = User()
    is_authenticated = user.authenticate()
    if is_authenticated:
        result = api.remove_from_favorites(user.username, user.token, channel_id)
        executebuiltin('Container.Refresh')
        executebuiltin('Notification("{0}", "{1}")'.format(
            ADDON.getLocalizedString(30000),
            ADDON.getLocalizedString(32303) if result else ADDON.getLocalizedString(32305)
        ))
    else:
        executebuiltin('Notification("{0}", "{1}")'.format(
            ADDON.getLocalizedString(30000),
            ADDON.getLocalizedString(32110)
        ))


def empty_directory(folder_path):
    if os.path.exists(folder_path) and os.path.isdir(folder_path):
        for file_name in os.listdir(folder_path):
            file_path = os.path.join(folder_path, file_name)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
            except Exception as e:
                print(e)


if __name__ == '__main__':
    PLUGIN.run()
    # empty previous thumbnails or create addon data folder:
    if os.path.exists(ADDON_DATA_FOLDER):
        empty_directory(ADDON_DATA_FOLDER)
    else:
        os.makedirs(ADDON_DATA_FOLDER)

    if sys.argv[0] == 'PLUGIN://{0}/'.format(ADDON_ID) and not ADDON.getSetting('username'):
        executebuiltin('Notification("{0}", "{1}", 6000, "special://home/addons/{2}/icon.png")'
                       .format(ADDON.getLocalizedString(30000),
                               ADDON.getLocalizedString(32202),
                               ADDON_ID))
