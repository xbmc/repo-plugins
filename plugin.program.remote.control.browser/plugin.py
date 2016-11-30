import argparse
import bs4
import collections
import contextlib
import datetime
import json
import math
import os
import pipes
import re
import select
import shlex
import signal
import socket
import subprocess
import sys
import threading
import urllib
import urllib2
import urlparse
import uuid
import xbmc
import xbmcplugin
import xbmcgui
import xbmcaddon
import xml.etree.ElementTree


# If any of these packages are missing, the script will attempt to proceed
# without those features.
try:
    import alsaaudio
except ImportError:
    alsaaudio = None
try:
    import psutil
except ImportError:
    psutil = None
try:
    import pylirc
except ImportError:
    pylirc = None


DEFAULT_LIRC_CONFIG = ('special://home/addons' +
                       '/plugin.program.remote.control.browser' +
                       '/resources/data/lircd/browser.lirc')
VOLUME_MIN = 0L
VOLUME_MAX = 100L
DEFAULT_VOLUME_STEP = 1L
RELEASE_KEY_DELAY = datetime.timedelta(seconds=1)
BROWSER_EXIT_DELAY = datetime.timedelta(seconds=3)


PylircCode = collections.namedtuple('PylircCode', ('config', 'repeat'))


class JsonRpcError(RuntimeError):
    pass


class CompetingLaunchError(RuntimeError):
    pass


class KodiMixer:
    """Mixer that integrates tightly with Kodi volume controls"""

    def __init__(self):
        if alsaaudio is None:
            xbmc.log('Not initializing an alsaaudio mixer')
            self.delegate = None
        else:
            try:
                self.delegate = alsaaudio.Mixer()
            except alsaaudio.ALSAAudioError as e:
                xbmc.log('Failed to initialize alsaaudio: ' + str(e))
                self.delegate = None
        self.lastRpcId = 0
        try:
            result = self.executeJSONRPC(
                'Application.GetProperties',
                {'properties': ['muted', 'volume']})
            self.muted = bool(result['muted'])
            self.volume = int(result['volume'])
        except (JsonRpcError, KeyError, ValueError) as e:
            xbmc.log('Could not retrieve current volume: ' + str(e))
            self.muted = False
            self.volume = VOLUME_MAX

    def __enter__(self):
        if self.delegate is not None:
            self.original = self.delegate.getvolume()
        # Match the current volume to Kodi's last volume.
        self.realizeVolume()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        # Restore the master volume to its original level.
        if self.delegate is not None:
            for (channel, volume) in enumerate(self.original):
                self.delegate.setvolume(volume, channel)

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

    def realizeVolume(self):
        # Muting the Master volume and then unmuting it is not a symmetric
        # operation, because other controls end up muted. So a mute needs to be
        # simulated by setting the volume level to zero.
        if self.delegate is not None:
            if self.muted:
                self.delegate.setvolume(0)
            else:
                self.delegate.setvolume(self.volume)

    def toggleMute(self):
        try:
            result = self.executeJSONRPC(
                'Application.SetMute', {'mute': 'toggle'})
            self.muted = bool(result)
        except (JsonRpcError, ValueError) as e:
            xbmc.log('Could not toggle mute: ' + str(e))
            self.muted = not self.muted
        self.realizeVolume()

    def incrementVolume(self):
        self.muted = False
        try:
            result = self.executeJSONRPC(
                'Application.SetVolume', {'volume': 'increment'})
            self.volume = int(result)
        except (JsonRpcError, ValueError) as e:
            xbmc.log('Could not increase volume: ' + str(e))
            self.volume = min(self.volume + DEFAULT_VOLUME_STEP, VOLUME_MAX)
        if self.delegate is not None:
            self.delegate.setvolume(self.volume)

    def decrementVolume(self):
        try:
            result = self.executeJSONRPC(
                'Application.SetVolume', {'volume': 'decrement'})
            self.volume = int(result)
        except (JsonRpcError, ValueError) as e:
            xbmc.log('Could not decrease volume: ' + str(e))
            self.volume = max(self.volume - DEFAULT_VOLUME_STEP, VOLUME_MIN)
        if self.delegate is not None and not self.muted:
            self.delegate.setvolume(self.volume)


class InterminableProgressBar:
    """Acts as a spinner for work with an unknown duration"""

    DEFAULT_TICK_INTERVAL = datetime.timedelta(milliseconds=250)

    def __init__(self, title):
        self.title = title
        self.dialog = xbmcgui.DialogProgress()

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
    except OSError:
        # The directory may already exist.
        xbmc.log('Failed to create directory: ' + folder, xbmc.LOGDEBUG)


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
def runPylirc(configuration):
    if pylirc is None:
        xbmc.log('Not initializing pylirc')
        yield
        return
    xbmc.log(
        'Initializing pylirc with configuration: ' + configuration,
        xbmc.LOGDEBUG)
    fd = pylirc.init('browser', configuration)
    if not fd:
        raise RuntimeError('Failed to initialize pylirc')
    try:
        yield fd
    finally:
        pylirc.exit()


def monitorProcess(proc, exitSocket):
    proc.wait()
    exitSocket.shutdown(socket.SHUT_RDWR)


def getProcessTree(parent):
    if psutil is None:
        xbmc.log('Not searching for process descendents', xbmc.LOGDEBUG)
        return [parent]
    try:
        process = psutil.Process(parent)
        try:
            children = process.children
        except AttributeError:
            children = process.get_children
        processes = [process] + children(recursive=True)
        return [node.pid for node in processes]
    except psutil.NoSuchProcess:
        xbmc.log('Failed to find process tree', xbmc.LOGDEBUG)
        return []


def killBrowser(proc, sig):
    for pid in getProcessTree(proc.pid):
        try:
            os.kill(pid, sig)
        except OSError:
            pass


@contextlib.contextmanager
def runBrowser(browserCmd):
    (sink, source) = socket.socketpair()
    with contextlib.closing(sink), contextlib.closing(source):
        waiter = None
        try:
            if xbmc.getCondVisibility('System.Platform.Windows'):
                # On Windows, the Popen will block unless close_fds is True and
                # creationflags is DETACHED_PROCESS.
                xbmc.log('Using Windows creation flags', xbmc.LOGDEBUG)
                creationflags = 0x00000008
            else:
                creationflags = 0
            xbmc.log(
                'Launching browser: ' +
                ' '.join(pipes.quote(arg) for arg in browserCmd),
                xbmc.LOGINFO)
            proc = subprocess.Popen(
                browserCmd, creationflags=creationflags, close_fds=True)
            try:
                # Monitor the browser and kick the socket when it exits.
                waiterStarting = threading.Thread(
                    target=monitorProcess, args=(proc, source))
                waiterStarting.start()
                waiter = waiterStarting

                yield (proc, sink.fileno())

                # Ask each child process to exit.
                xbmc.log('Terminating the browser', xbmc.LOGDEBUG)
                killBrowser(proc, signal.SIGTERM)

                # Give the browser a few seconds to shut down gracefully.
                def terminateBrowser():
                    xbmc.log(
                        'Forcefully killing the browser at the deadline',
                        xbmc.LOGINFO)
                    killBrowser(proc, signal.SIGKILL)
                terminator = threading.Timer(
                    BROWSER_EXIT_DELAY.total_seconds(), terminateBrowser)
                terminator.start()
                try:
                    proc.wait()
                    proc = None
                    xbmc.log('Waited for the browser to quit', xbmc.LOGDEBUG)
                finally:
                    terminator.cancel()
                    terminator.join()
            finally:
                if proc is not None:
                    # As a last resort, forcibly kill the browser.
                    xbmc.log('Forcefully killing the browser', xbmc.LOGINFO)
                    killBrowser(proc, signal.SIGKILL)
                    proc.wait()
                    xbmc.log('Waited for the browser to die', xbmc.LOGDEBUG)
        finally:
            if waiter is not None:
                xbmc.log(
                    'Joining with browser monitoring thread', xbmc.LOGDEBUG)
                waiter.join()
                xbmc.log(
                    'Joined with browser monitoring thread', xbmc.LOGDEBUG)


def activateWindow(cmd, proc, isAborting, xdotoolPath):
    (output, error) = proc.communicate()
    if isAborting.is_set():
        xbmc.log('Aborting search for browser PID', xbmc.LOGDEBUG)
        return
    if proc.returncode != 0:
        xbmc.log('Failed search for browser PID', xbmc.LOGINFO)
        raise subprocess.CalledProcessError(proc.returncode, cmd, output)
    wids = [wid for wid in output.split('\n') if wid]
    for wid in wids:
        if isAborting.is_set():
            xbmc.log('Aborting activation of windows', xbmc.LOGDEBUG)
            return
        xbmc.log('Activating window with WID: ' + wid, xbmc.LOGDEBUG)
        subprocess.call([xdotoolPath, 'WindowActivate', wid])
    xbmc.log('Finished activating windows', xbmc.LOGDEBUG)


@contextlib.contextmanager
def raiseBrowser(pid, xdotoolPath):
    if not xdotoolPath:
        xbmc.log('Not raising the browser')
        yield
        return
    activator = None
    # With the "sync" flag, the command could block indefinitely.
    cmd = [xdotoolPath, 'search', '--sync', '--onlyvisible', '--pid', str(pid)]
    xbmc.log(
        'Searching for browser PID: ' +
        ' '.join(pipes.quote(arg) for arg in cmd),
        xbmc.LOGINFO)
    proc = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, universal_newlines=True)
    try:
        isAborting = threading.Event()
        activatorStarting = threading.Thread(
            target=activateWindow, args=(cmd, proc, isAborting, xdotoolPath))
        activatorStarting.start()
        activator = activatorStarting

        yield
    finally:
        isAborting.set()
        if proc.poll() is None:
            proc.kill()
        proc.wait()
        if activator is not None:
            activator.join()


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


def monitorKodiDaemon(abortSocket, stopEvent):
    monitor = xbmc.Monitor()
    while not stopEvent.is_set() and not monitor.abortRequested():
        # The only way to register for an event is to use this blocking
        # method, even though that prevents this thread from waiting on the
        # stop event.
        monitor.waitForAbort(1)
    try:
        abortSocket.shutdown(socket.SHUT_RDWR)
    except socket.error:
        # The socket may already be closed.
        pass


@contextlib.contextmanager
def abortContext():
    stopEvent = threading.Event()
    (sink, source) = socket.socketpair()
    with contextlib.closing(sink), contextlib.closing(source):
        # Monitor Kodi and kick the socket when it exits.
        waiter = threading.Thread(
            target=monitorKodiDaemon, args=(source, stopEvent))
        # The waiter is a daemon so that the main thread does not have to wait
        # for it to finish.
        waiter.daemon = True
        waiter.start()
        try:
            yield sink.fileno()
        finally:
            # The monitor daemon is not joined because it takes a second to
            # terminate.
            stopEvent.set()


def runRemoteControlBrowser(
        browserCmd, browserLockPath, lircConfig, xdotoolPath):
    with (
            suspendXbmcLirc()), (
            runPylirc(lircConfig)) as lircFd, (
            KodiMixer()) as mixer, (
            runBrowser(browserCmd)) as (browser, browserExitFd), (
            lockPidfile(browserLockPath, browser.pid)), (
            raiseBrowser(browser.pid, xdotoolPath)), (
            abortContext()) as kodiAbortFd:

        polling = [browserExitFd, kodiAbortFd]
        if lircFd is not None:
            polling.append(lircFd)
        releaseKeyTime = None
        repeatKeys = None
        isExiting = False
        while not isExiting:
            if releaseKeyTime is None:
                timeout = None
            else:
                timeout = max(
                    (releaseKeyTime - datetime.datetime.now()).total_seconds(),
                    0)
            (rlist, wlist, xlist) = select.select(polling, [], [], timeout)
            if browserExitFd in rlist:
                xbmc.log(
                    'Exiting because the browser stopped prematurely',
                    xbmc.LOGINFO)
                break
            if kodiAbortFd in rlist:
                xbmc.log('Exiting because Kodi is aborting', xbmc.LOGINFO)
                break
            if lircFd is not None and lircFd in rlist:
                buttons = pylirc.nextcode(True)
            else:
                buttons = None
            codes = ([PylircCode(**button) for button in buttons]
                     if buttons else [])
            if (releaseKeyTime is not None and
                    releaseKeyTime <= datetime.datetime.now()):
                codes.append(PylircCode(config='RELEASE', repeat=0))

            for code in codes:
                xbmc.log('Received LIRC code: ' + str(code), xbmc.LOGDEBUG)
                tokens = shlex.split(code.config)
                (command, args) = (tokens[0], tokens[1:])
                isReleasing = False
                nextReleaseKeyTime = None
                inputs = None

                if command == 'VOLUME_UP':
                    mixer.incrementVolume()
                elif command == 'VOLUME_DOWN':
                    mixer.decrementVolume()
                elif command == 'MUTE':
                    mixer.toggleMute()
                elif command == 'MULTITAP':
                    if releaseKeyTime is not None and repeatKeys == args:
                        repeatIndex += 1
                    else:
                        isReleasing = True
                        repeatKeys = args
                        repeatIndex = 0
                    nextReleaseKeyTime = (datetime.datetime.now() +
                                          RELEASE_KEY_DELAY)
                    current = args[repeatIndex % len(args)]
                    inputs = [
                        'key', '--clearmodifiers', '--', current, 'Shift+Left']
                elif command == 'KEY':
                    isReleasing = True
                    inputs = ['key', '--clearmodifiers', '--'] + args
                elif command == 'CLICK':
                    isReleasing = True
                    inputs = ['click', '--clearmodifiers', '1']
                elif command == 'MOUSE':
                    step = min(code.repeat, 10)
                    (horizontal, vertical) = args
                    acceleratedHorizontal = str(int(horizontal) * step ** 2)
                    acceleratedVertical = str(int(vertical) * step ** 2)
                    inputs = [
                        'mousemove_relative',
                        '--',
                        acceleratedHorizontal,
                        acceleratedVertical]
                elif command == 'EXIT':
                    isExiting = True
                    break
                elif command == 'RELEASE':
                    isReleasing = True
                else:
                    raise RuntimeError('Unrecognized LIRC config: ' + command)

                if isReleasing and releaseKeyTime is not None:
                    if xdotoolPath:
                        # Deselect the current multi-tap character.
                        xbmc.log(
                            'Executing xdotool for multi-tap release',
                            xbmc.LOGDEBUG)
                        subprocess.check_call(
                            [xdotoolPath, 'key', '--clearmodifiers', 'Right'])
                    else:
                        xbmc.log(
                            'Ignoring xdotool for multi-tap release',
                            xbmc.LOGDEBUG)
                releaseKeyTime = nextReleaseKeyTime

                if inputs is not None:
                    if xdotoolPath:
                        cmd = [xdotoolPath] + inputs
                        xbmc.log('Executing: ' + ' '.join(cmd), xbmc.LOGDEBUG)
                        subprocess.check_call(cmd)
                    else:
                        xbmc.log(
                            'Ignoring xdotool inputs: ' + str(inputs),
                            xbmc.LOGDEBUG)


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
            self, bookmarkId=None, defaultUrl='http://', defaultTitle=None):
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
            runRemoteControlBrowser(
                browserCmd, browserLockPath, lircConfig, xdotoolPath)
        except CompetingLaunchError:
            xbmc.log('A competing browser instance is already running')
            xbmc.executebuiltin('XBMC.Notification(Info:,"{}",5000)'.format(
                self.escapeNotification(self.getLocalizedString(30038))))


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
