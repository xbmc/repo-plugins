import argparse
import contextlib
import datetime
import errno
import json
import math
import os
import pipes
import re
import shlex
import subprocess
import sys
import threading
import urllib
import urllib2
import urlparse
import uuid
import xml.etree.ElementTree

import bs4
import xbmc
import xbmcplugin
import xbmcgui
import xbmcaddon


# If any of these packages are missing, the script will attempt to proceed
# without those features.
try:
    import alsaaudio
except ImportError:
    xbmc.log('Missing Python package: alsaaudio', xbmc.LOGDEBUG)
    alsaaudio = None
try:
    import pulsectl
except ImportError:
    xbmc.log('Missing Python package: pulsectl', xbmc.LOGDEBUG)
    pulsectl = None


DEFAULT_VOLUME = 50L
DEFAULT_LIRC_CONFIG = ('special://home/addons' +
                       '/plugin.program.remote.control.browser' +
                       '/resources/data/lircd/browser.lirc')


class JsonRpcError(RuntimeError):
    pass


class CompetingLaunchError(RuntimeError):
    pass


class VolumeError(RuntimeError):
    def __init__(self, cause):
        super(VolumeError, self).__init__(str(cause))


class InterminableProgressBar(object):
    """Acts as a spinner for work with an unknown duration"""

    DEFAULT_TICK_INTERVAL = datetime.timedelta(milliseconds=250)

    def __init__(self, title):
        self.title = title
        self.dialog = xbmcgui.DialogProgress()
        self.ticks = None

    def __enter__(self):
        self.ticks = 0
        self.dialog.create(self.title)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.dialog.close()

    def iscanceled(self):
        return self.dialog.iscanceled()

    def tick(self):
        self.ticks += 1
        # Use a function with an asymptote at 100%.
        percentage = math.atan(self.ticks / 8.) * 200 / math.pi
        self.dialog.update(int(percentage))


def makedirs(folder):
    try:
        os.makedirs(folder)
    except OSError as e:
        # The directory may already exist.
        if e.errno != errno.EEXIST or not os.path.isdir(folder):
            raise


def slurpLog(stream):
    for line in iter(stream.readline, b''):
        xbmc.log('BROWSER: ' + line, xbmc.LOGDEBUG)
    stream.close()


@contextlib.contextmanager
def suspendXbmcLirc():
    xbmc.log('Suspending XBMC LIRC', xbmc.LOGDEBUG)
    xbmc.executebuiltin('LIRC.Stop')
    try:
        yield
    finally:
        xbmc.log('Resuming XBMC LIRC', xbmc.LOGDEBUG)
        xbmc.executebuiltin('LIRC.Start')


@contextlib.contextmanager
def lockPidfile(browserLockPath, pid):
    isMine = False
    try:
        makedirs(os.path.dirname(browserLockPath))
        try:
            pidfile = os.open(
                browserLockPath, os.O_RDWR | os.O_CREAT | os.O_EXCL)
        except OSError as e:
            xbmc.log('Failed to acquire pidfile: ' + str(e), xbmc.LOGDEBUG)
            raise CompetingLaunchError()
        try:
            isMine = True
            os.write(pidfile, str(pid))
        finally:
            os.close(pidfile)

        yield
    finally:
        if isMine:
            try:
                os.remove(browserLockPath)
            except OSError as e:
                xbmc.log('Failed to remove pidfile: ' + str(e))


class AlsaWrapper(object):
    """Interchangable wrapper for Alsa"""

    def __init__(self, alsaControl):
        if alsaaudio is None:
            xbmc.log('Not initializing an alsaaudio mixer', xbmc.LOGDEBUG)
            raise VolumeError('No alsaaudio package')
        else:
            try:
                self.delegate = alsaaudio.Mixer(alsaControl)
            except alsaaudio.ALSAAudioError as e:
                xbmc.log('Failed to initialize alsaaudio: ' + str(e))
                raise VolumeError(e)

    def getChannels(self):
        try:
            return self.delegate.getvolume()
        except alsaaudio.ALSAAudioError as e:
            raise VolumeError(e)

    def setVolume(self, volume):
        try:
            self.delegate.setvolume(volume)
        except alsaaudio.ALSAAudioError as e:
            raise VolumeError(e)

    def setChannels(self, channels):
        try:
            for (channel, volume) in enumerate(channels):
                self.delegate.setvolume(volume, channel)
        except alsaaudio.ALSAAudioError as e:
            raise VolumeError(e)


class PulseWrapper(object):
    """Interchangable wrapper for Pulse"""

    def __init__(self):
        if pulsectl is None:
            xbmc.log('Not initializing a pulsectl mixer', xbmc.LOGDEBUG)
            raise VolumeError('No pulsectl package')
        else:
            try:
                self.pulse = pulsectl.Pulse()
                self.sink = next(iter(self.pulse.sink_list()))
            except pulsectl.PulseError as e:
                xbmc.log('Failed to initialize pulsectl: ' + str(e))
                raise VolumeError(e)

    def getChannels(self):
        try:
            return [int(round(channel * 100)) for channel in self.sink.volume.values]
        except pulsectl.PulseError as e:
            raise VolumeError(e)

    def setVolume(self, volume):
        try:
            volume_buffer = self.sink.volume
            volume_buffer.value_flat = volume / 100.
            self.pulse.volume_set(self.sink, volume_buffer)
        except pulsectl.PulseError as e:
            raise VolumeError(e)

    def setChannels(self, channels):
        try:
            volume_buffer = pulsectl.PulseVolumeInfo([channel / 100. for channel in channels])
            self.pulse.volume_set(self.sink, volume_buffer)
        except pulsectl.PulseError as e:
            raise VolumeError(e)


class VolumeGuard(object):
    """Hands off volume control between Kodi and Pulse or ALSA"""

    def __init__(self, alsaControl):
        self.alsaControl = alsaControl
        self.lastRpcId = 0
        self.kodiMute = None
        self.kodiVolume = None
        self.alsaChannels = None

    def __enter__(self):
        mixer = self.getMixer()
        if mixer is not None:
            try:
                result = self.executeJSONRPC(
                    'Application.GetProperties',
                    {'properties': ['muted', 'volume']})
                mute = bool(result['muted'])
                volume = long(result['volume'])
            except (JsonRpcError, KeyError, ValueError) as e:
                xbmc.log('Could not retrieve original Kodi volume: ' + str(e))
                mute = False
                volume = DEFAULT_VOLUME
            self.kodiMute = mute
            self.kodiVolume = volume

            try:
                self.alsaChannels = mixer.getChannels()
            except VolumeError as e:
                xbmc.log('Could not detect original system volume: ' + str(e))
                self.alsaChannels = None

            try:
                # Match the system volume to Kodi's last volume.
                # Muting the Master volume and then unmuting it is not a
                # symmetric operation, because other controls end up muted.
                # So a mute needs to be simulated by setting the volume level
                # to zero.
                if mute:
                    mixer.setVolume(0)
                else:
                    mixer.setVolume(volume)
            except VolumeError as e:
                xbmc.log('Could not set system volume: ' + str(e))

        return self

    def __exit__(self, exc_type, exc_value, traceback):
        mixer = self.getMixer()
        if mixer is not None:
            # Match Kodi's volume to the Master volume.
            try:
                channels = mixer.getChannels()
                volume = next(iter(channels))
                if volume:
                    mute = False
                else:
                    if self.kodiVolume:
                        # The volume was probably zero because it was muted.
                        mute = True
                    else:
                        # The volume and mute haven't changed.
                        mute = self.kodiMute
                    volume = self.kodiVolume
                try:
                    xbmc.log('Updating Kodi volume: ' + str(volume) +
                             ', mute=' + str(mute), xbmc.LOGDEBUG)
                    self.executeJSONRPC(
                        'Application.SetMute', {'mute': mute})
                    self.executeJSONRPC(
                        'Application.SetVolume', {'volume': volume})
                except (JsonRpcError, ValueError) as e:
                    xbmc.log('Could not update Kodi volume: ' + str(e))
            except VolumeError as e:
                xbmc.log('Could not detect final ALSA volume: ' + str(e))

            # Restore the master volume to its original level.
            try:
                mixer.setChannels(self.alsaChannels)
            except VolumeError as e:
                xbmc.log('Could not restore ALSA volume: ' + str(e))

    def getMixer(self):
        try:
            return PulseWrapper() if self.alsaControl is None else AlsaWrapper(self.alsaControl)
        except VolumeError:
            return None

    def getNextRpcId(self):
        self.lastRpcId = self.lastRpcId + 1
        return self.lastRpcId

    def executeJSONRPC(self, method, params):
        response = xbmc.executeJSONRPC(json.dumps({
            'jsonrpc': '2.0',
            'method': method,
            'params': params,
            'id': self.getNextRpcId()}))
        try:
            return json.loads(response)['result']
        except (KeyError, ValueError):
            raise JsonRpcError('Invalid JSON RPC response: ' + repr(response))


class RemoteControlBrowserPlugin(xbmcaddon.Addon):

    def __new__(cls, *args, **kwargs):
        # The Addon.__new__ override doesn't accept additional arguments.
        return super(RemoteControlBrowserPlugin, cls).__new__(cls)

    def __init__(self, handle):
        super(RemoteControlBrowserPlugin, self).__init__()
        self.handle = handle
        self.pluginId = self.getAddonInfo('id')
        self.addonFolder = xbmc.translatePath(
            self.getAddonInfo('path')).decode('utf_8')
        self.profileFolder = xbmc.translatePath(
            self.getAddonInfo('profile')).decode('utf_8')
        self.bookmarksPath = os.path.join(self.profileFolder, 'bookmarks.xml')
        self.defaultBookmarksPath = os.path.join(
            self.addonFolder, 'resources/data/bookmarks.xml')
        self.thumbsFolder = os.path.join(self.profileFolder, 'thumbs')
        self.defaultThumbsFolder = os.path.join(
            self.addonFolder, 'resources/data/thumbs')

    def buildPluginUrl(self, query):
        return urlparse.ParseResult(
            scheme='plugin',
            netloc=self.pluginId,
            path='/',
            params=None,
            query=urllib.urlencode(query),
            fragment=None).geturl()

    def getThumbPath(self, thumbId, thumbsFolder=None):
        if thumbsFolder is None:
            thumbsFolder = self.thumbsFolder
        return os.path.join(thumbsFolder, thumbId + '.png')

    def escapeLabel(self, label):
        # A zero-width space is used to escape label metacharacters. Other
        # means of escaping, such as "$LBRACKET", don't work in the context of
        # ListItem labels.
        return re.sub(u'[][$]', u'\\g<0>\u200B', label)

    def escapeNotification(self, message):
        # A notification needs to be encoded into a quoted byte string.
        return message.encode('utf_8').replace('"', r'\"')

    def readBookmarks(self):
        try:
            return xml.etree.ElementTree.parse(self.bookmarksPath)
        except (IOError, xml.etree.ElementTree.ParseError) as e:
            xbmc.log(
                'Falling back to default bookmarks: ' + str(e), xbmc.LOGDEBUG)
            return xml.etree.ElementTree.parse(self.defaultBookmarksPath)

    def getBookmarkElement(self, tree, bookmarkId):
        bookmark = tree.find('bookmark[@id="{}"]'.format(bookmarkId))
        if bookmark is None:
            raise ValueError('Unrecognized bookmark ID: ' + bookmarkId)
        return bookmark

    def getBookmarkDirectoryItem(self, bookmarkId, title, thumbId):
        url = self.buildPluginUrl({'mode': 'launchBookmark', 'id': bookmarkId})
        listItem = xbmcgui.ListItem(label=self.escapeLabel(title))
        if thumbId is not None:
            thumbPath = self.getThumbPath(thumbId)
            if not os.path.isfile(thumbPath):
                thumbPath = self.getThumbPath(
                    thumbId, self.defaultThumbsFolder)
            if os.path.isfile(thumbPath):
                listItem.setArt({
                    'thumb': thumbPath,
                })
        listItem.addContextMenuItems([
            (self.getLocalizedString(30025),
             'RunPlugin({})'.format(self.buildPluginUrl(
                 {'mode': 'launchBookmark', 'id': bookmarkId}))),
            (self.getLocalizedString(30006),
             'RunPlugin({})'.format(self.buildPluginUrl(
                 {'mode': 'editBookmark', 'id': bookmarkId}))),
            (self.getLocalizedString(30027),
             'RunPlugin({})'.format(self.buildPluginUrl(
                 {'mode': 'editKeymap', 'id': bookmarkId}))),
            (self.getLocalizedString(30002),
             'RunPlugin({})'.format(self.buildPluginUrl(
                 {'mode': 'removeBookmark', 'id': bookmarkId}))),
        ])
        return (url, listItem)

    def index(self):
        tree = self.readBookmarks()
        items = [self.getBookmarkDirectoryItem(
            bookmark.get('id'),
            bookmark.get('title'),
            bookmark.get('thumb'))
                 for bookmark in tree.iter('bookmark')]

        url = self.buildPluginUrl({'mode': 'addBookmark'})
        listItem = xbmcgui.ListItem(
            u'[B]{}[/B]'.format(self.getLocalizedString(30001)))
        listItem.setArt({
            'thumb': 'DefaultFile.png',
        })
        items.append((url, listItem))

        success = xbmcplugin.addDirectoryItems(
            handle=self.handle, items=items, totalItems=len(items))
        if not success:
            raise RuntimeError('Failed addDirectoryItem')
        xbmcplugin.endOfDirectory(self.handle)

    def removeThumb(self, thumbId):
        if thumbId is not None:
            try:
                os.remove(self.getThumbPath(thumbId))
            except OSError:
                xbmc.log(
                    'Failed to remove thumbnail: ' + thumbId, xbmc.LOGINFO)

    def scrapeWebpage(
            self, url, thumbId, isAborting, isTitleReady, fetchedTitleSlot):
        webpage = None
        try:
            try:
                if isAborting.is_set():
                    xbmc.log('Aborting fetch of webpage', xbmc.LOGINFO)
                    return
                xbmc.log('Fetching webpage: ' + url, xbmc.LOGINFO)
                webpage = urllib2.urlopen(url)

                if isAborting.is_set():
                    xbmc.log('Aborting parse of webpage', xbmc.LOGINFO)
                    return
                xbmc.log('Parsing webpage: ' + url, xbmc.LOGDEBUG)
                soup = bs4.BeautifulSoup(webpage, 'html.parser')

                if isAborting.is_set():
                    xbmc.log('Aborting scrape of webpage title', xbmc.LOGINFO)
                    return
                # Search for the title.
                titleElement = soup.find('title')
                if titleElement is not None:
                    fetchedTitleSlot.append(titleElement.text)
            finally:
                isTitleReady.set()

            if isAborting.is_set():
                xbmc.log('Aborting scrape of webpage links', xbmc.LOGINFO)
                return
            # Search for a rel="icon" attribute.
            linkElements = soup.findAll('link', rel='icon', href=True)
            # Prefer the icon with the best quality.
            linkElement = next(
                iter(sorted(
                    linkElements,
                    key=lambda element: (
                        # Prefer large images.
                        reduce(
                            lambda prev, cur: prev * int(cur, 10),
                            re.findall(r'\d+', element['sizes']),
                            1)
                        if 'sizes' in element.attrs else 0,
                        # Prefer PNG format.
                        'type' in element.attrs and
                        element['type'] == 'image/png',
                        # Prefer "icon" to "shortcut icon".
                        element['rel'] == ['icon']),
                    reverse=True)),
                None)
        except (ValueError, IOError) as e:
            xbmc.log('Failed to scrape bookmarked page: ' + str(e))
            linkElement = None

        # Try to download the icon.
        try:
            if webpage is not None:
                base = webpage.url
            else:
                base = url
            if linkElement is None:
                xbmc.log('Falling back to default favicon path', xbmc.LOGDEBUG)
                link = '/favicon.ico'
            else:
                link = linkElement['href']
            thumbUrl = urlparse.urljoin(base, link)

            if isAborting.is_set():
                xbmc.log('Aborting creation of thumbs folder', xbmc.LOGINFO)
                return
            makedirs(self.thumbsFolder)

            # The Pillow module needs to be isolated to its own subprocess
            # because many distributions are prone to deadlock.
            retrievePath = os.path.join(self.addonFolder, 'retrieve.py')
            thumbPath = self.getThumbPath(thumbId)
            if isAborting.is_set():
                xbmc.log('Aborting retrieval of favicon', xbmc.LOGINFO)
                return
            xbmc.log('Retrieving favicon: ' + thumbUrl, xbmc.LOGINFO)
            subprocess.check_call(
                [sys.executable, retrievePath, thumbUrl, thumbPath])
        except (ValueError, IOError, subprocess.CalledProcessError) as e:
            xbmc.log('Failed to retrieve favicon: ' + str(e))

    def inputBookmark(
            self, bookmarkId=None, defaultUrl='https://', defaultTitle=None):
        keyboard = xbmc.Keyboard(defaultUrl, self.getLocalizedString(30004))
        keyboard.doModal()
        if not keyboard.isConfirmed():
            xbmc.log('User aborted URL input', xbmc.LOGDEBUG)
            return
        url = keyboard.getText()

        # The old thumb ID can't be reused, because then the cached copy of the
        # old image would never be replaced.
        thumbId = str(uuid.uuid1())

        # Asynchronously scrape information from the webpage while the user
        # types.
        isAborting = threading.Event()
        isTitleReady = threading.Event()
        fetchedTitleSlot = []
        scraper = threading.Thread(
            target=self.scrapeWebpage,
            args=(url, thumbId, isAborting, isTitleReady, fetchedTitleSlot))
        scraper.start()
        try:
            if defaultTitle is None:
                if not isTitleReady.is_set():
                    xbmc.log('Waiting for scrape of title', xbmc.LOGDEBUG)
                    with InterminableProgressBar(
                        self.getLocalizedString(30029)) as progress:
                        while not isTitleReady.wait(
                                progress.DEFAULT_TICK_INTERVAL
                                .total_seconds()):
                            if progress.iscanceled():
                                xbmc.log(
                                    'User aborted scrape of title',
                                    xbmc.LOGDEBUG)
                                return
                            progress.tick()
                defaultTitle = next(iter(fetchedTitleSlot), None)
                xbmc.log(
                    'Received scraped title: ' + str(defaultTitle),
                    xbmc.LOGDEBUG)
                if defaultTitle is None:
                    defaultTitle = urlparse.urlparse(url).netloc

            keyboard = xbmc.Keyboard(
                defaultTitle, self.getLocalizedString(30003))
            keyboard.doModal()
            if not keyboard.isConfirmed():
                xbmc.log('User aborted title input', xbmc.LOGDEBUG)
                return
            title = keyboard.getText()

            if scraper.isAlive():
                xbmc.log('Waiting for scrape of thumbnail', xbmc.LOGDEBUG)
                with InterminableProgressBar(
                    self.getLocalizedString(30029)) as progress:
                    while True:
                        scraper.join(
                            progress.DEFAULT_TICK_INTERVAL.total_seconds())
                        if not scraper.isAlive():
                            break
                        if progress.iscanceled():
                            xbmc.log(
                                'User aborted scrape of thumbnail',
                                xbmc.LOGDEBUG)
                            return
                        progress.tick()
                xbmc.log('Finished scrape of thumbnail', xbmc.LOGDEBUG)
        finally:
            if scraper.isAlive():
                isAborting.set()
                xbmc.log('Joining with aborted scraper thread', xbmc.LOGDEBUG)
                scraper.join()
                xbmc.log('Joined with aborted scraper thread', xbmc.LOGDEBUG)

        # Save the bookmark metadata.
        tree = self.readBookmarks()
        if bookmarkId is None:
            bookmarkId = str(uuid.uuid1())
            bookmark = xml.etree.ElementTree.SubElement(
                tree.getroot(),
                'bookmark',
                {
                    'id': bookmarkId,
                    'title': title,
                    'url': url,
                    'lircrc': DEFAULT_LIRC_CONFIG,
                })
        else:
            bookmark = self.getBookmarkElement(tree, bookmarkId)
            bookmark.set('title', title)
            bookmark.set('url', url)
        if os.path.isfile(self.getThumbPath(thumbId)):
            removeThumbId = bookmark.get('thumb')
            bookmark.set('thumb', thumbId)
        else:
            removeThumbId = None
        makedirs(self.profileFolder)
        tree.write(self.bookmarksPath)
        xbmc.executebuiltin('Container.Refresh')
        if removeThumbId is not None:
            self.removeThumb(removeThumbId)

    def addBookmark(self):
        self.inputBookmark()

    def editBookmark(self, bookmarkId):
        tree = self.readBookmarks()
        bookmark = self.getBookmarkElement(tree, bookmarkId)
        self.inputBookmark(
            bookmarkId, bookmark.get('url'), bookmark.get('title'))

    def editKeymap(self, bookmarkId):
        tree = self.readBookmarks()
        bookmark = self.getBookmarkElement(tree, bookmarkId)
        defaultLircrc = bookmark.get('lircrc')

        ShowAndGetFile = 1
        lircrc = xbmcgui.Dialog().browseSingle(
            type=ShowAndGetFile,
            heading=self.getLocalizedString(30028),
            shares='files',
            mask='.lirc',
            defaultt=defaultLircrc)

        tree = self.readBookmarks()
        bookmark = self.getBookmarkElement(tree, bookmarkId)
        bookmark.set('lircrc', lircrc)
        makedirs(self.profileFolder)
        tree.write(self.bookmarksPath)

    def removeBookmark(self, bookmarkId):
        tree = self.readBookmarks()
        bookmark = self.getBookmarkElement(tree, bookmarkId)
        thumbId = bookmark.get('thumb')
        tree.getroot().remove(bookmark)
        makedirs(self.profileFolder)
        tree.write(self.bookmarksPath)
        self.removeThumb(thumbId)

        xbmc.executebuiltin('Container.Refresh')

    def launchBookmark(self, bookmarkId):
        tree = self.readBookmarks()
        bookmark = self.getBookmarkElement(tree, bookmarkId)
        url = bookmark.get('url')
        lircConfig = xbmc.translatePath(bookmark.get('lircrc')).decode('utf_8')
        self.launchUrl(url, lircConfig)

    def linkcast(self, url):
        lircConfig = xbmc.translatePath(DEFAULT_LIRC_CONFIG).decode('utf_8')
        self.launchUrl(url, lircConfig)

    def launchUrl(self, url, lircConfig):
        browserLockPath = os.path.join(self.profileFolder, 'browser.pid')
        browserPath = self.getSetting('browserPath').decode('utf_8')
        browserArgs = self.getSetting('browserArgs').decode('utf_8')
        xdotoolPath = self.getSetting('xdotoolPath').decode('utf_8')
        soundServer = self.getSetting('soundServer').decode('utf_8')
        alsaControl = self.getSetting('alsaControl').decode('utf_8') if soundServer == '1' else None
        suspendKodi = self.unmarshalBool(self.getSetting('suspendKodi'))

        if not browserPath or not os.path.isfile(browserPath):
            xbmc.executebuiltin('XBMC.Notification(Info:,"{}",5000)'.format(
                self.escapeNotification(self.getLocalizedString(30005))))
            self.openSettings()
            return

        # Flashing a white screen looks bad, but it is improved with a black
        # interstitial page.
        blackPath = os.path.join(self.addonFolder, 'resources/data/black.html')
        blackUrl = urlparse.ParseResult(
            scheme='file',
            netloc=None,
            path=blackPath,
            params=None,
            query=urllib.quote_plus(url),
            fragment=None).geturl()

        browserCmd = [browserPath] + shlex.split(browserArgs) + [blackUrl]

        player = xbmc.Player()
        if player.isPlaying() and not xbmc.getCondVisibility('Player.Paused'):
            player.pause()
        try:
            with (
                    suspendXbmcLirc()), (
                    VolumeGuard(alsaControl)):
                self.spawnBrowser(
                    suspendKodi,
                    browserCmd,
                    browserLockPath,
                    lircConfig,
                    xdotoolPath,
                    alsaControl)
        except CompetingLaunchError:
            xbmc.log('A competing browser instance is already running')
            xbmc.executebuiltin('XBMC.Notification(Info:,"{}",5000)'.format(
                self.escapeNotification(self.getLocalizedString(30038))))


    def spawnBrowser(
            self,
            suspendKodi,
            browserCmd,
            browserLockPath,
            lircConfig,
            xdotoolPath,
            alsaControl):
        # The browser runs in its own subprocess so that it can continue after
        # Kodi stops.
        suspendKodiFlags = ['--suspend-kodi'] if suspendKodi else []
        browsePath = os.path.join(self.addonFolder, 'browse.py')
        alsaCmd = [] if alsaControl is None else [
                '--alsa-control', alsaControl,
            ]
        if xbmc.getCondVisibility('System.Platform.Windows'):
            # On Windows, the Popen will block unless close_fds is True and
            # creationflags is DETACHED_PROCESS.
            xbmc.log('Using Windows creation flags', xbmc.LOGDEBUG)
            creationflags = 0x00000008
        else:
            creationflags = 0
        xbmc.log(
            'Launching wrapper for browser: ' +
            ' '.join(pipes.quote(arg) for arg in browserCmd),
            xbmc.LOGINFO)
        proc = subprocess.Popen(
            [
                sys.executable,
                browsePath,
            ] +
            suspendKodiFlags +
            alsaCmd +
            [
                '--lirc-config', lircConfig,
                '--xdotool-path', xdotoolPath,
                '--',
            ] +
            browserCmd,
            creationflags=creationflags,
            # Closing stdin will inform the child of its parent's death.
            stdin=subprocess.PIPE,
            # The child will publish log lines via stderr.
            stderr=subprocess.PIPE)
        try:
            slurper = threading.Thread(target=slurpLog, args=(proc.stderr,))
            slurper.start()

            with lockPidfile(browserLockPath, proc.pid):
                monitor = xbmc.Monitor()
                while proc.poll() is None and not monitor.abortRequested():
                    # The only way to register for an event is to use this
                    # blocking method, even though that prevents this thread
                    # from waiting on the subprocess.
                    monitor.waitForAbort(1)

        finally:
            proc.stderr.close()
            proc.wait()
            slurper.join()

        if proc.returncode:
            xbmc.log(
                'Failed to spawn browser: errno=' + str(proc.returncode),
                xbmc.LOGINFO)
            xbmc.executebuiltin('XBMC.Notification(Info:,"{}",5000)'.format(
                self.escapeNotification(self.getLocalizedString(30040))))

    def unmarshalBool(self, val):
        STRING_ENCODING = {'false': False, 'true': True}
        unmarshalled = STRING_ENCODING.get(val)
        if unmarshalled is None:
            raise ValueError('Invalid Boolean: ' + str(val))
        return unmarshalled


def parsedParams(search):
    query = urlparse.urlparse(search).query
    return urlparse.parse_qs(query, strict_parsing=True) if query else {}


def getUrl(args):
    url = next(iter(args.params.get('url', [])), None)
    if url is None:
        raise ValueError('Missing URL')
    return url


def getBookmarkId(args):
    bookmarkId = next(iter(args.params.get('id', [])), None)
    if bookmarkId is None:
        raise ValueError('Missing bookmark ID')
    # Validate the ID.
    uuid.UUID(bookmarkId)
    return bookmarkId


def main():
    xbmc.log(
        'Plugin called: ' + ' '.join(pipes.quote(arg) for arg in sys.argv),
        xbmc.LOGDEBUG)
    parser = argparse.ArgumentParser()
    parser.add_argument('handle', type=int)
    parser.add_argument('params', type=parsedParams)
    args = parser.parse_args()

    plugin = RemoteControlBrowserPlugin(args.handle)

    mode = next(iter(args.params.get('mode', ['index'])), None)
    xbmc.log('Parsed mode: ' + mode, xbmc.LOGDEBUG)
    HANDLERS = {
        'index': lambda args: plugin.index(),
        'linkcast': lambda args: plugin.linkcast(getUrl(args)),
        'launchBookmark': lambda args: plugin.launchBookmark(
            getBookmarkId(args)),
        'addBookmark': lambda args: plugin.addBookmark(),
        'editBookmark': lambda args: plugin.editBookmark(getBookmarkId(args)),
        'editKeymap': lambda args: plugin.editKeymap(getBookmarkId(args)),
        'removeBookmark': lambda args: plugin.removeBookmark(
            getBookmarkId(args)),
    }
    handler = HANDLERS.get(mode)
    if handler is None:
        raise ValueError('Unrecognized mode: ' + mode)
    handler(args)


if __name__ == "__main__":
    main()
