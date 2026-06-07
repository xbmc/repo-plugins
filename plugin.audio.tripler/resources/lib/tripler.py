from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import time, sys, os, json, re
import pytz
from xbmcaddon import Addon
import xbmcgui
import xbmcplugin
import xbmc

from resources.lib.scraper import Scraper
from resources.lib.website import TripleRWebsite
from resources.lib.media   import Media

from urllib.parse import parse_qs, urlencode, unquote_plus, quote_plus

class TripleR():
    def __init__(self):
        self.matrix     = '19.' in xbmc.getInfoLabel('System.BuildVersion')
        self.handle     = int(sys.argv[1])
        self.id         = 'plugin.audio.tripler'
        self.url        = 'plugin://' + self.id
        self.tz         = pytz.timezone('Australia/Melbourne')
        self.addon      = Addon()
        self.dialog     = xbmcgui.Dialog()
        self._respath   = os.path.join(self.addon.getAddonInfo('path'), 'resources')
        self.icon       = os.path.join(self._respath, 'icon.png')
        self.fanart     = os.path.join(self._respath, 'fanart.png')
        self.website    = TripleRWebsite(os.path.join(self._respath, 'cookies.lwp'))
        self._signed_in = -1
        self.supported_plugins = Media.RE_MEDIA_URLS.keys()
        quality         = self.addon.getSetting('image_quality')
        self.quality    = int(quality) if quality else 1
        self.media      = Media(self.quality)

        self.nextpage   = self.get_string(30004)
        self.lastpage   = self.get_string(30005)

    def get_string(self, string_id):
        return self.addon.getLocalizedString(string_id)

    def _notify(self, title, message):
        xbmc.log(f'TripleR plugin notification: {title} - {message}', xbmc.LOGDEBUG)
        self.dialog.notification(title, message, icon=self.icon)

    def parse(self):
        args = parse_qs(sys.argv[2][1:])
        segments = sys.argv[0].split('/')[3:]
        xbmc.log("TripleR plugin called: " + str(sys.argv), xbmc.LOGDEBUG)

        if 'schedule' in segments and args.get('picker'):
            date = self.select_date(args.get('picker')[0])
            if date:
                args['date'] = date

        k_title = args.get('k_title', [None])[0]
        if k_title:
            xbmcplugin.setPluginCategory(self.handle, k_title)
            del args['k_title']

        if args.get('picker'):
            del args['picker']

        if 'search' in segments and not args.get('q'):
            search = self.search(tracks=('tracks' in segments))
            if search:
                args['q'] = search
            else:
                return

        if 'ext_search' in segments:
            self.ext_search(args)
            return

        path = '/' + '/'.join(segments)
        if args:
            path += '?' + urlencode(args, doseq=True)

        if len(segments[0]) < 1:
            return self.main_menu()
        elif 'subscribe' in segments:
            self._notify(self.get_string(30084), self.get_string(30083))
        elif 'settings' in segments:
            self.login()
            Addon().openSettings()
        elif 'sign-in' in segments:
            if self.sign_in():
                xbmc.executebuiltin("Container.Refresh")
        elif 'sign-out' in segments:
            self.sign_out()
            xbmc.executebuiltin("Container.Refresh")
        elif 'entries' in segments:
            if self.addon.getSettingBool('authenticated'):
                self.subscriber_giveaway(path=path)
            else:
                self._notify(self.get_string(30073), self.get_string(30076))
        elif 'play' in args:
            self.play_stream(handle=self.handle, args=args, segments=segments)
            return None
        else:
            scraped = Scraper.call(path)
            parsed = self.parse_programs(**scraped, args=args, segments=segments, k_title=k_title)
            if parsed:
                return parsed

    def main_menu(self):
        items = [
            self.livestream_item(),
            {'label': self.get_string(30032), 'path': self.url + '/programs', 'icon': 'DefaultPartyMode.png'},
            {'label': self.get_string(30033), 'path': self.url + '/schedule', 'icon': 'DefaultYear.png'},
            # {'label': self.get_string(30034), 'path': self.url + '/broadcasts', 'icon': 'DefaultPlaylist.png'},
            {'label': self.get_string(30035), 'path': self.url + '/segments', 'icon': 'DefaultPlaylist.png'},
            {'label': self.get_string(30036), 'path': self.url + '/archives', 'icon': 'DefaultPlaylist.png'},
            {'label': self.get_string(30037), 'path': self.url + '/featured_albums', 'icon': 'DefaultMusicAlbums.png'},
            {'label': self.get_string(30038), 'path': self.url + '/soundscapes', 'icon': 'DefaultSets.png'},
            {'label': self.get_string(30042), 'path': self.url + '/videos', 'icon': 'DefaultMusicVideos.png'},
            {'label': self.get_string(30039), 'path': self.url + '/events', 'icon': 'DefaultPVRGuide.png'},
            {'label': self.get_string(30040), 'path': self.url + '/giveaways', 'icon': 'DefaultAddonsRecentlyUpdated.png'},
            {'label': self.get_string(30041), 'path': self.url + '/search', 'icon': 'DefaultMusicSearch.png'},
        ]
        if self.login():
            emailaddress = self.addon.getSetting('emailaddress')
            fullname = self.addon.getSetting('fullname')
            name = fullname if fullname else emailaddress
            items.append(
                {
                    'label': f'{self.get_string(30014)} ({name})',
                    'path': self.url + '/sign-out',
                    'icon': 'DefaultUser.png',
                }
            )
        else:
            items.append(
                {
                    'label': self.get_string(30013),
                    'path': self.url + '/sign-in',
                    'icon': 'DefaultUser.png',
                }
            )

        listitems = []

        for item in items:
            path = self._k_title(item['path'], item['label'])
            li = xbmcgui.ListItem(item['label'], '', path, True)
            li.setArt(
                {
                    'icon': item['icon'],
                    'fanart': self.fanart,
                }
            )
            if 'properties' in item:
                li.setProperties(item['properties'])
            listitems.append((path, li, item.get('properties') == None))

        xbmcplugin.addDirectoryItems(self.handle, listitems, len(listitems))
        xbmcplugin.addSortMethod(self.handle, xbmcplugin.SORT_METHOD_UNSORTED)
        xbmcplugin.endOfDirectory(self.handle)

    def livestream_item(self):
        item = {
            'label': self.get_string(30001),
            'path': 'https://ondemand.rrr.org.au/stream/ws-hq.m3u',
            'icon': self.icon,
            'properties': {
                'StationName': self.get_string(30000),
                'IsPlayable': 'true'
            },
        }
        return item

    def _sub_item(self, text):
        path = self.url + '/settings'
        li = xbmcgui.ListItem(text, '', path, True)
        li.setArt({'thumbnail': os.path.join(self._respath, 'qr-subscribe.png')})
        return (path, li, True)

    def _k_title(self, url, title):
        if title:
            return url + ('?' if '?' not in url else '&') + 'k_title=' + quote_plus(title)
        else:
            return url

    def select_date(self, self_date):
        self_date_str   = '/'.join([i for i in self_date.split('-')[::-1]])
        dialog_title    = self.get_string(30065) % (self.get_string(30033))
        picked_date_str = self.dialog.input(dialog_title, defaultt=str(self_date_str), type=xbmcgui.INPUT_DATE)

        if picked_date_str:
            date_str    = '-'.join([i.zfill(2) for i in picked_date_str.replace(' ', '').split('/')[::-1]])
            current     = datetime(*(time.strptime(date_str, '%Y-%m-%d')[0:6]), tzinfo=self.tz)
            daydelta    = datetime.now(self.tz) - current - timedelta(hours=6)
            if daydelta.days != 0:
                return date_str

        return None

    def context_item(self, label, path, plugin=None):
        plugin = plugin if plugin else self.id
        return (self.get_string(label), f'Container.Update(plugin://{plugin}{path})')

    def play_stream(self, handle, args, segments):
        li = xbmcgui.ListItem(
            label = args.get('title', [''])[0],
            path  = unquote_plus(args.get('play', [''])[0]),
            offscreen=True,
        )
        li.setArt(
            {
                'thumb':  unquote_plus(args.get('thumbnail', [''])[0]).replace(' ', '%20'),
                'fanart': unquote_plus(args.get('fanart', [''])[0]).replace(' ', '%20'),
            }
        )
        if not self.matrix:
            vi = li.getVideoInfoTag()
            vi.setTitle(args.get('title', [''])[0])
            vi.setMediaType('song')
        else:
            li.setInfo('video',
                {
                    'title':     args.get('title', [''])[0],
                    'mediatype': 'song',
                }
            )
        xbmcplugin.setResolvedUrl(self.handle, True, li)

    def parse_programs(self, data, args, segments, links=None, k_title=None):
        items = []

        for menuitem in data:
            if menuitem is None:
                continue
            m_id, m_type = menuitem.get('id', ''), menuitem.get('type', '')
            m_links      = menuitem.get('links', {})
            m_self       = m_links.get('self', '/')
            m_sub        = m_links.get('subscribe')
            m_playlist   = m_links.get('playlist')
            attributes   = menuitem.get('attributes', {})
            if attributes is None:
                continue

            textbody        = attributes.get('textbody', '')
            thumbnail       = attributes.get('thumbnail', '')
            fanart          = attributes.get('background', self.fanart)
            pathurl         = None

            if attributes.get('subtitle') and not ('soundscapes' in segments and len(segments) > 1):
                textbody    = '\n'.join((self.get_string(30007) % (attributes.get('subtitle')), textbody))

            if attributes.get('venue'):
                textbody    = '\n'.join((attributes['venue'], textbody))

            if m_type in self.supported_plugins:
                title       = attributes.get('title', '')
                artist      = attributes.get('artist')
                if artist:
                    title   = f'{artist} - {title}'
                pathurl     = self.media.parse_media_id(m_type, m_id, quote_plus(title.split('(')[0].strip()))

                name        = Media.RE_MEDIA_URLS[m_type].get('name')
                title       = f'{title} ({name})'
                textbody    = self.get_string(30008) % (name) + '\n' + textbody

                if 'bandcamp' in m_type or 'apple' in m_type:
                    thumbnail = self.media.parse_art(thumbnail)
                    if fanart != self.fanart:
                        fanart    = self.media.parse_art(fanart)

                if not thumbnail:
                    thumbnail = 'DefaultMusicSongs.png'

                if m_type in ['bandcamp_track', 'youtube']:
                    is_playable = True
                else:
                    is_playable = False
            else:
                title       = attributes.get('title', '')
                artist      = attributes.get('artist')
                pathurl     = attributes.get('url')
                if artist:
                    title   = f'{artist} - {title}'
                if m_type == 'broadcast' and pathurl:
                    title   = f'{title} ({self.get_string(30050)})'
                if m_type == 'broadcast_index' and 'schedule' in segments:
                    title   = f'{title} ({self.get_string(30049)})'
                if m_type == 'segment':
                    title   = f'{title} ({self.get_string(30051)})'
                on_air = attributes.get('on_air')
                if on_air:
                    title   = f'{title} ({on_air})'
                is_playable = True

            if m_type == 'program_broadcast_track':
                title   = f'{title} ({self.get_string(30052)})'
                thumbnail   = 'DefaultMusicSongs.png'
                ext_search  = m_links.get('broadcast_track').replace('search', 'ext_search')
                pathurl     = self._k_title(self.url + ext_search, attributes.get('title'))
                is_playable = False

            icon = thumbnail

            if m_sub:
                if not self.login() or not self.subscribed():
                    icon        =  'OverlayLocked.png'
                    title       = f'{self.get_string(30081)} - {title}'
                    textbody    = f'{self.get_string(30081)}\n{textbody}'
                    pathurl     = self.url + m_sub
                    is_playable = False
                else:
                    title       = f'{self.get_string(30084)} - {title}'

            if m_type == 'giveaway' and 'entries' in m_self.split('/'):
                title      += ' ({})'.format(self.get_string(30069))
                textbody    = '\n'.join((self.get_string(30070), textbody))

            if attributes.get('start') and attributes.get('end'):
                datestart   = datetime.fromisoformat(attributes['start'])
                dateend     = datetime.fromisoformat(attributes['end'])
                start       = datetime.strftime(datestart, '%H:%M')
                end         = datetime.strftime(dateend,   '%H:%M')
                textbody    = f'{start} - {end}\n{textbody}'
                title       = ' - '.join((start, end, title))

            if attributes.get('aired'):
                aired       = self.get_string(30006) % (attributes['aired'])
            else:
                aired       = attributes.get('date', '')

            if pathurl:
                is_playable = not pathurl.startswith('plugin://')
                if is_playable:
                    encodedurl = quote_plus(pathurl)
                    pathurl = '{}/{}?play={}&title={}&thumbnail={}&fanart={}'.format(
                        self.url,
                        '/'.join(segments),
                        quote_plus(encodedurl),
                        quote_plus(title),
                        quote_plus(thumbnail),
                        quote_plus(fanart),
                    )
                mediatype = 'song'
                info_type = 'video'
            else:
                pathurl     = self._k_title(self.url + m_self, attributes.get('title'))
                is_playable = False
                mediatype   = ''
                info_type   = 'video'

            date, year = attributes.get('date', ''), attributes.get('year', '')
            if date:
                date = time.strftime('%d.%m.%Y', time.strptime(date, '%Y-%m-%d'))
                year = date[0]
            else:
                # prevents log entries regarding empty date string
                date = time.strftime('%d.%m.%Y', time.localtime())


            li = xbmcgui.ListItem(title, aired, pathurl, True)
            li.setArt(
                {
                    'icon':      icon,
                    'thumb':     thumbnail,
                    'fanart':    fanart,
                }
            )
            li.setProperties({
                'StationName': self.get_string(30000),
                'IsPlayable': 'true' if is_playable else 'false',
            })

            context_menu = []

            if m_playlist:
                textbody += f'\n\n{self.get_string(30100)}' % (self.get_string(30101))
                context_menu.append(self.context_item(30101, m_playlist))

            if 'broadcast_track' in m_links:
                if m_type != 'program_broadcast_track':
                    textbody += f'\n{self.get_string(30100)}' % (self.get_string(30102))
                ext_search = m_links.get('broadcast_track').replace('search', 'ext_search')
                context_menu.append(self.context_item(30102, ext_search))

            if context_menu:
                li.addContextMenuItems(context_menu)

            if not self.matrix:
                vi = li.getVideoInfoTag()
                # vi.setDbId((abs(hash(m_id)) % 2147083647) + 400000)
                vi.setTitle(title)
                vi.setPlot(textbody)
                vi.setDateAdded(date)
                if year.isdecimal():
                    vi.setYear(int(year))
                vi.setFirstAired(aired)
                vi.setPremiered(aired)
                if attributes.get('duration', 0) > 0:
                    vi.setDuration(attributes.get('duration'))
                if mediatype:
                    vi.setMediaType(mediatype)
            else: # Matrix v19.0
                vi = {
                    'title':     title,
                    'plot':      textbody,
                    'date':      date,
                    'year':      year,
                    'premiered': aired,
                    'aired':     aired,
                }

                if attributes.get('duration', 0) > 0:
                    vi['duration'] = attributes.get('duration')
                if mediatype:
                    vi['mediatype'] = mediatype

                li.setInfo('video', vi)

            items.append((pathurl, li, not is_playable))


        if 'schedule' in segments:
            self_date = links.get('self', '?date=').split('?date=')[-1]
            next_date = links.get('next', '?date=').split('?date=')[-1]

            if links.get('next'):
                path = self.url + self._k_title(links['next'], k_title)
                li = xbmcgui.ListItem(self.get_string(30061) % (next_date), '', path, True)
                items.insert(0, (path, li, True))

            path = self.url + self._k_title(f'/schedule?picker={self_date}', k_title)
            li = xbmcgui.ListItem(self.get_string(30065) % (self_date), '', path, True)
            li.setArt({'icon': 'DefaultPVRGuide.png'})
            items.insert(0, (path, li, True))

        elif 'giveaways' in segments:
            if not self.login() or not self.subscribed():
                items.insert(0, self._sub_item(self.get_string(30082)))

        elif links and links.get('next'):
            if len(items) > 0:
                if links.get('next'):
                    path = self.url + self._k_title(links['next'], k_title)
                    li = xbmcgui.ListItem(self.nextpage, '', path, True)
                    items.append((path, li, True))
                if links.get('last'):
                    path = self.url + self._k_title(links['last'], k_title)
                    li = xbmcgui.ListItem(self.lastpage, '', path, True)
                    items.append((path, li, True))


        if 'archives' in segments:
            if not self.login() or not self.subscribed():
                items.insert(0, self._sub_item(self.get_string(30083)))

        elif 'search' in segments and 'tracks' not in segments:
            link = links.get('self').split('?page=')[0]
            path = self.url + '/tracks' + link
            li = xbmcgui.ListItem(self.get_string(30066), '', path, True)
            li.setArt({'icon': 'DefaultMusicSearch.png'})
            items.insert(0, (path, li, True))

        xbmcplugin.addSortMethod(self.handle, xbmcplugin.SORT_METHOD_UNSORTED, labelMask='%L', label2Mask='%D')
        if len(segments) > 3 and 'broadcasts' in segments[2]:
            # broadcast playlist
            xbmcplugin.setContent(self.handle, 'episodes')
        elif 'segments' in segments or 'archives' in segments:
            # any segment or archive listing
            xbmcplugin.setContent(self.handle, 'episodes')
        elif len(segments) == 3 and 'broadcasts' in segments:
            # index of broadcasts
            xbmcplugin.setContent(self.handle, 'songs')
        elif len(segments) == 2 and 'soundscapes' in segments:
            # soundscape
            xbmcplugin.setContent(self.handle, 'songs')
        elif len(segments) == 2 and 'featured_albums' in segments:
            # featured albums
            xbmcplugin.setContent(self.handle, 'songs')
        else:
            xbmcplugin.setContent(self.handle, '')

        xbmcplugin.addDirectoryItems(self.handle, items, len(items))
        xbmcplugin.endOfDirectory(self.handle)

    def search(self, tracks=False):
        prompt = self.get_string(30068 if tracks else 30067)
        return self.dialog.input(prompt, type=xbmcgui.INPUT_ALPHANUM)

    def ext_search(self, args):
        q = args.get('q', [''])
        title = q[0]
        opts = q
        if ' - ' in q[0]:
            qsplit = q[0].split(' - ')
            opts.append(qsplit[0])
            opts.append(qsplit[1])

        yt_addon = 'special://home/addons/plugin.video.youtube/'
        yt_icon = yt_addon + ('icon.png' if self.matrix else 'resources/media/icon.png')

        options = []
        for opt in opts:
            query = urlencode({'q': [opt]}, doseq=True)
            options.append({
                'label': self.get_string(30105) % opt,
                'path': self.url + '/tracks/search?' + query,
                'icon': self.icon,
            })
        for opt in opts:
            query_sub = urlencode({'query': [opt]}, doseq=True)
            options.append({
                'label': self.get_string(30106) % opt,
                'path': 'plugin://plugin.audio.kxmxpxtx.bandcamp/?mode=search&action=search&' + query_sub,
                'icon': 'special://home/addons/plugin.audio.kxmxpxtx.bandcamp/icon.png',
            })
        for opt in opts:
            query = urlencode({'q': [opt]}, doseq=True)
            options.append({
                'label': self.get_string(30107) % opt,
                'path': 'plugin://plugin.video.youtube/kodion/search/query/?' + query,
                'icon': yt_icon,
            })

        listitems = []
        for item in options:
            li = xbmcgui.ListItem(item['label'], '', item['path'], True)
            li.setArt(
                {
                    'thumb': item.get('icon', 'DefaultMusicSearch.png'),
                    'icon': 'DefaultMusicSearch.png',
                    'fanart': self.fanart,
                }
            )
            listitems.append((item['path'], li, True))

        xbmcplugin.setPluginCategory(self.handle, self.get_string(30104) % title)
        xbmcplugin.addDirectoryItems(self.handle, listitems, len(listitems))
        xbmcplugin.addSortMethod(self.handle, xbmcplugin.SORT_METHOD_UNSORTED)
        xbmcplugin.endOfDirectory(self.handle)

    def sign_in(self):
        emailaddress = self.dialog.input(self.get_string(30015), type=xbmcgui.INPUT_ALPHANUM)
        if emailaddress == '':
            return False
        password = self.dialog.input(self.get_string(30016), type=xbmcgui.INPUT_ALPHANUM, option=xbmcgui.ALPHANUM_HIDE_INPUT)
        if password == '':
            return False
        return self.login(prompt=True, emailaddress=emailaddress, password=password)

    def login(self, prompt=False, emailaddress=None, password=None):
        if self._signed_in != -1:
            return self._signed_in
        if self.addon.getSettingBool('authenticated') and self.website.logged_in():
            return True

        emailSetting = self.addon.getSetting('emailaddress')
        if emailaddress is None:
            emailaddress = emailSetting

        logged_in = self.website.login(emailaddress, password)

        if logged_in:
            if prompt:
                self._notify(self.get_string(30077) % (emailaddress), self.get_string(30078))
            if not self.addon.getSettingBool('authenticated'):
                self.addon.setSetting('subscribed-check', '0')
                self.addon.setSettingBool('authenticated', True)
                self.subscribed()

            if emailSetting == '':
                self.addon.setSetting('emailaddress', emailaddress)
            for cookie in logged_in:
                if cookie.name == 'account':
                    fullname = json.loads(unquote_plus(cookie.value)).get('name')
                    if fullname:
                        self.addon.setSetting('fullname', fullname)
            self._signed_in = logged_in
        else:
            if prompt:
                self._notify(self.get_string(30085), self.get_string(30086) % (emailaddress))
            self.addon.setSettingBool('authenticated', False)
            self.addon.setSetting('emailaddress', '')
            self.addon.setSetting('fullname', '')

        return logged_in

    def sign_out(self, emailaddress=None):
        if emailaddress is None:
            emailaddress = self.addon.getSetting('emailaddress')
        if self.website.logout():
            self.addon.setSettingBool('authenticated', False)
            self.addon.setSetting('subscribed-check', '0')
            self.addon.setSettingInt('subscribed', 0)
            self._signed_in = -1
            if emailaddress:
                self._notify(self.get_string(30079) % (emailaddress), self.get_string(30078))
            self.addon.setSetting('emailaddress', '')
            self.addon.setSetting('fullname', '')
            return True
        else:
            if emailaddress:
                self._notify(self.get_string(30087), self.get_string(30088) % (emailaddress))
            return False

    def subscribed(self):
        if not self.addon.getSettingBool('authenticated'):
            return False
        check          = int(self.addon.getSetting('subscribed-check'))
        now            = int(time.time())
        if now - check < (15*60):
            setting    = self.addon.getSettingInt('subscribed')
            subscribed = (setting == 1)
        else:
            subscribed = self.website.subscribed()
            self.addon.setSettingInt('subscribed', 1 if subscribed else 0)
            self.addon.setSetting('subscribed-check', str(now))
        return subscribed

    def subscriber_giveaway(self, path):
        if self.login():
            source = self.website.enter(path)

            if 'Thank you! You have been entered' in source:
                self._notify(self.get_string(30071), self.get_string(30072))
            elif 'already entered this giveaway' in source:
                self._notify(self.get_string(30073), self.get_string(30074))
            else:
                self._notify(self.get_string(30073), self.get_string(30075))

        else:
            self._notify(self.get_string(30073), self.get_string(30076))

instance = TripleR()
