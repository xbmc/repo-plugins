import sys
import routing
from urllib import quote
from time import time
from config import config
from api import API
from user import User
from xbmc import executebuiltin, Player, sleep, translatePath, log, getSkinDir, getCondVisibility
from xbmcgui import ListItem, Dialog, getCurrentWindowDialogId, WindowDialog
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

@PLUGIN.route('/')
def index():
    """
    Main add-on popup
    :return:
    """
    api = API()

    # check if current window is arwork or intro:
    window_id = getCurrentWindowDialogId()
    window = WindowDialog(window_id)

    if isinstance(window, IntroWindow) or isinstance(window, ArtworkWindow):
        log('Either IntroWindow or ArtworkWindow are already open')
    else:
        intro_window = IntroWindow(api)
        intro_window.doModal()
        section_id = intro_window.getProperty('section')
        if section_id:
            section_id = int(section_id)
            category_id = int(intro_window.getProperty('category'))
            del intro_window

            if section_id == 1:  # channels
                show_channels(section_id, category_id) if section_id != 99 else show_favorites()
            elif section_id == 3:  # atmospheres
                show_categories(section_id)
            else:
                show_favorites()  # favorites
        else:
            del intro_window


@PLUGIN.route('/section/<section_id>')
def show_categories(section_id):
    """
    Categories page
    :param section_id: Selected section ID
    :return:
    """
    api = API()

    for item in api.get_categories(int(section_id)):
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
                PLUGIN.url_for(show_channels, section_id=section_id, category_id=item['id']),
                li,
                True
        )
    # end of directory:
    endOfDirectory(PLUGIN.handle)
    executebuiltin('Container.SetViewMode({0})'.format(
            config['viewmodes']['thumbnail'][getSkinDir()
            if getSkinDir() in config['viewmodes']['thumbnail'] else 'skin.confluence']
    ))


@PLUGIN.route('/section/<section_id>/category/<category_id>')
def show_channels(section_id, category_id):
    """
    Channels page (playable)
    :param section_id: Selected section ID
    :param category_id: Selected category ID
    :return:
    """
    api = API()

    for item in api.get_channels(int(category_id)):
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
                               channel_id=item['id']),
                li
        )
    # set the content of the directory
    setContent(ADDON_HANDLE, 'songs')
    # end of directory:
    endOfDirectory(PLUGIN.handle)
    executebuiltin('Container.SetViewMode({0})'.format(
            config['viewmodes']['thumbnail'][getSkinDir()
            if getSkinDir() in config['viewmodes']['thumbnail'] else 'skin.confluence']
    ))


@PLUGIN.route('/favorites')
def show_favorites():
    """
    User's favorite channels list
    :return:
    """
    api = API()
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
                                       category_id=item['category'],
                                       channel_id=item['id']),
                        li
                )
            # set the content of the directory
            setContent(ADDON_HANDLE, 'songs')
            # end of directory:
            endOfDirectory(PLUGIN.handle)
            executebuiltin('Container.SetViewMode({0})'.format(
                    config['viewmodes']['thumbnail'][getSkinDir()
                    if getSkinDir() in config['viewmodes']['thumbnail'] else 'skin.confluence']
            ))
        # favorites list is empty:
        else:
            executebuiltin('Notification("{0}", "{1}")'
                           .format(ADDON.getLocalizedString(30000), ADDON.getLocalizedString(32306)))
    # user is not authenticated:
    else:
        executebuiltin('Notification("{0}", "{1}")'
                       .format(ADDON.getLocalizedString(30000), ADDON.getLocalizedString(32110)))


@PLUGIN.route('/category/<category_id>/channel/<channel_id>')
def play_channel(category_id, channel_id):
    """
    Plays selected song
    :param category_id: Selected category ID
    :param channel_id: Selected channel ID
    :return:
    """
    api = API()
    user = User()
    is_authenticated = user.authenticate()
    recent_tracks_url = ''
    channel = [item for item in api.get_channels(int(category_id))
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
                   'fanart': '{0}{1}'.format(config['urls']['calm_blurred_arts_host'], channel['image'])})
        li.setInfo('music', {'Title': channel['title'].replace('CALM RADIO -', '').title(),
                             'Artist': channel['description']})
        li.setProperty('mimetype', 'audio/mpeg')
        li.setProperty('IsPlayable', 'true')
        li.setInfo('music', {
            'Title': channel['title'].replace('CALM RADIO -', '').title()
        })
        Player().play(item=url, listitem=li)

        log('Playing url: {0}'.format(url))
        update_artwork(channel, recent_tracks_url)
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
    api = API()
    user = User()
    is_authenticated = user.authenticate()
    if is_authenticated:
        api.add_to_favorites(user.username, user.token, channel_id)
        executebuiltin('Notification("{0}", "{1}"'.format(ADDON.getLocalizedString(30000),
                                                          ADDON.getLocalizedString(32302)))
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
    api = API()
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
            if file_name.endswith('.jpg') or file_name.endswith('.png'):
                file_path = os.path.join(folder_path, file_name)
                try:
                    if os.path.isfile(file_path):
                        os.unlink(file_path)
                except Exception as e:
                    print(e)


def update_artwork(channel, recent_tracks_url):
    """
    Update current channel info
    :param channel: Channel object
    :param recent_tracks_url: Recent tracks URL
    :return:
    """
    artwork = ArtworkWindow()
    api = API()
    last_album_cover = ''

    # update now playing fanart, channel name & description:
    artwork.channel.setLabel('[B]' + channel['title'] + '[/B]')
    artwork.description.setText(channel['description'])
    artwork.show()
    artwork_id = getCurrentWindowDialogId()

    while getCondVisibility('Window.IsVisible({0})'.format(artwork_id)):
        recent_tracks = api.get_json('{0}?{1}'.format(recent_tracks_url, str(int(time()))))
        if last_album_cover != recent_tracks['now_playing']['album_art']:
            last_album_cover = recent_tracks['now_playing']['album_art']
            # urlretrieve('{0}/{1}'.format(config['urls']['calm_arts_host'],
            #                              recent_tracks['now_playing']['album_art']),
            #             '{0}{1}'.format(ADDON_DATA_FOLDER, recent_tracks['now_playing']['album_art']))
            # artwork.cover.setImage('{0}/{1}'.format(ADDON_DATA_FOLDER, recent_tracks['now_playing']['album_art']))
            artwork.cover.setImage('{0}/{1}'.format(config['urls']['calm_arts_host'],
                                         recent_tracks['now_playing']['album_art']))
            artwork.song.setLabel('[B]' + recent_tracks['now_playing']['title'] + '[/B]')
            artwork.album.setLabel('[B]Album[/B]: ' + (recent_tracks['now_playing']['album']
                                                       if recent_tracks['now_playing']['album'] else 'N/A'))
            artwork.artist.setLabel('[B]Artist[/B]: ' + recent_tracks['now_playing']['artist'])
            # next track:
            artwork.next_1.setLabel('- [B]{0}[/B] by {1}'.format(
                recent_tracks['next_playing']['title'], recent_tracks['next_playing']['artist']
            ))
            # recent tracks:
            artwork.recent_1.setLabel('- [B]{0}[/B] by {1}'.format(
                recent_tracks['recently_played'][0]['title'], recent_tracks['recently_played'][0]['artist']
            ))
            artwork.recent_2.setLabel('- [B]{0}[/B] by {1}'.format(
                recent_tracks['recently_played'][1]['title'], recent_tracks['recently_played'][1]['artist']
            ))
            artwork.recent_3.setLabel('- [B]{0}[/B] by {1}'.format(
                recent_tracks['recently_played'][2]['title'], recent_tracks['recently_played'][2]['artist']
            ))
        sleep(5000)

    log('Artwork closed')
    del artwork


if __name__ == '__main__':
    PLUGIN.run()
    # empty previous thumbnails or create add-on data folder:
    if os.path.exists(ADDON_DATA_FOLDER):
        empty_directory(ADDON_DATA_FOLDER)
    else:
        os.makedirs(ADDON_DATA_FOLDER)

    if sys.argv[0] == 'PLUGIN://{0}/'.format(ADDON_ID) and not ADDON.getSetting('username'):
        executebuiltin('Notification("{0}", "{1}", 6000, "special://home/addons/{2}/icon.png")'
                       .format(ADDON.getLocalizedString(30000),
                               ADDON.getLocalizedString(32202),
                               ADDON_ID))
