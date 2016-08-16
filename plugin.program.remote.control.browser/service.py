import BaseHTTPServer
import cgi
import collections
import json
import os
import re
import subprocess
import sys
import threading
import urllib
import urlparse
import xbmc
import xbmcaddon
import xml.etree.ElementTree


# These libraries must be installed manually instead of through a Kodi module
# because they are platform-dependent. The user will be shown a warning if they
# are not present.
try:
    import alsaaudio
except ImportError:
    xbmc.log('Missing Python package: pyalsaaudio')
    alsaaudio = None
try:
    import psutil
except ImportError:
    xbmc.log('Missing Python package: psutil')
    psutil = None
try:
    import pylirc
except ImportError:
    xbmc.log('Missing Python package: pylirc2')
    pylirc = None


DEFAULT_LINKCAST_PORT = 49029


DetectedDefaults = collections.namedtuple(
    'DetectedDefaults', ('browserPath', 'browserArgs', 'xdotoolPath'))


class LinkcastMonitor(xbmc.Monitor):

    def __init__(self, addon):
        super(LinkcastMonitor, self).__init__()
        self.addon = addon

    def onSettingsChanged(self):
        self.addon.reloadLinkcastServer()


class LinkcastServer(BaseHTTPServer.HTTPServer):

    def __init__(self, addon, server_address):
        BaseHTTPServer.HTTPServer.__init__(
            self, server_address, LinkcastRequestHandler)
        self.addon = addon


class LinkcastRequestHandler(BaseHTTPServer.BaseHTTPRequestHandler):

    def do_GET(self):
        xbmc.log('Received GET request: ' + self.path, xbmc.LOGINFO)
        components = urlparse.urlparse(self.path)
        handler = self.GET_HANDLERS.get(components.path)
        if handler is None:
            self.send_error(404)
            return

        query = components.query
        params = urlparse.parse_qs(query, strict_parsing=True) if query else {}

        handler(self, params)

    def do_POST(self):
        xbmc.log('Received POST request: ' + self.path, xbmc.LOGINFO)
        components = urlparse.urlparse(self.path)
        handler = self.POST_HANDLERS.get(components.path)
        if handler is None:
            self.send_error(404)
            return

        contentType = self.headers.getheader('Content-Type')
        if contentType is None:
            self.send_error(400, 'Missing content type: {}')
            return
        (ctype, pdict) = cgi.parse_header(contentType)
        if ctype != 'application/x-www-form-urlencoded':
            self.send_error(400, 'Unsupported content type: {}'.format(ctype))
            return
        length = int(self.headers.getheader('Content-Length'))
        payload = self.rfile.read(length)
        params = urlparse.parse_qs(payload, keep_blank_values=True)

        handler(self, params)

    def serveMethodNotAllowed(self, params):
        """Serves an error if the GET or POST method should be the opposite"""
        self.send_error(405)

    def serveIndex(self, params):
        """Serves a human-friendly webpage"""
        url = next(iter(params.get('url', [])), None)

        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.end_headers()

        if url is None:
            url = ''
            status = ''
        else:
            status = u'<div id="status">{}</div>\n'.format(
                cgi.escape(self.server.addon.getLocalizedString(30034)))

        indexPath = os.path.join(
            self.server.addon.addonFolder, 'resources/data/index.html')
        self.serveTemplate(indexPath, {
            'TITLE_HTML': cgi.escape(
                self.server.addon.getLocalizedString(30032)),
            'SUBTITLE_HTML': cgi.escape(
                self.server.addon.getLocalizedString(30033)),
            'STATUS': status,
            'URL_ATTR': cgi.escape(url, quote=True),
            'SUBMIT_ATTR': cgi.escape(
                self.server.addon.getLocalizedString(30035), quote=True),
            'INSTRUCTIONS_HTML': cgi.escape(
                self.server.addon.getLocalizedString(30036)),
            'UNSUPPORTED_SCHEME_CSTR': json.dumps(
                self.server.addon.getLocalizedString(30037)),
        })

    def serveCloseLinkcast(self, params):
        """Serves a webpage that automatically closes itself

        When a linkcast is requested from a secure webpage, no communication is
        normally allowed to unsecure (HTTP) webpages. This webserver does not
        have a certificate, so all its pages are unsecure. The workaround is to
        open a separate window and request the linkcast from there. Then the
        page needs to close itself as soon as it opens.
        """
        url = next(iter(params.get('url', [])), None)
        if url is None:
            self.send_error(400, 'Missing parameter: url')
            return

        self.linkcast(url)

        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.end_headers()

        closePath = os.path.join(
            self.server.addon.addonFolder, 'resources/data/close.html')
        self.serveTemplate(closePath, {
            'TITLE_HTML': cgi.escape(
                self.server.addon.getLocalizedString(30032)),
        })

    def serveXhpLinkcast(self, params):
        """Serves an XmlHttpRpc response for CORS requests"""
        url = next(iter(params.get('url', [])), None)
        if url is None:
            self.send_error(400, 'Missing parameter: url')
            return

        self.linkcast(url)

        self.send_response(200)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        origin = self.headers.getheader('Origin')
        if origin is not None:
            self.send_header('Access-Control-Allow-Origin', origin)
        self.end_headers()

        self.wfile.write(u'{}'.encode('utf_8'))

    def serveHtmlLinkcast(self, params):
        url = next(iter(params.get('url', [])), None)
        if url is None:
            self.send_error(400, 'Missing parameter: url')
            return

        self.linkcast(url)

        self.send_response(302)
        location = urlparse.ParseResult(
            scheme=None,
            netloc=None,
            path=self.INDEX_PATH,
            params=None,
            query=urllib.urlencode({'url': url}),
            fragment=None).geturl()
        self.send_header('Location', location)
        self.end_headers()

    def serveTemplate(self, path, params):
        META_VARIABLES = {
            'LEFT_CURLY_BRACKET': u'{{',
            'RIGHT_CURLY_BRACKET': u'}}',
        }
        vars = dict(META_VARIABLES.items() + params.items())

        def repl(match):
            return vars[match.group(1)]

        with open(path) as file:
            template = file.read()
        expanded = re.sub(u'{{([^{}]+)}}', repl, template)
        self.wfile.write(expanded.encode('utf_8'))

    def linkcast(self, url):
        plugin = self.server.addon.buildPluginUrl(
            {'mode': 'linkcast', 'url': url})
        xbmc.log('Running plugin: ' + plugin)
        xbmc.executebuiltin('RunPlugin({})'.format(plugin))

    def log_message(self, format, *args):
        xbmc.log('Linkcast server log: ' + (format % args), xbmc.LOGDEBUG)

    INDEX_PATH = '/'
    LINKCAST_CLOSE_PATH = '/linkcast.close'
    LINKCAST_XHP_PATH = '/linkcast.xhp'
    LINKCAST_HTML_PATH = '/linkcast.html'

    GET_HANDLERS = {
        INDEX_PATH: serveIndex,
        LINKCAST_CLOSE_PATH: serveCloseLinkcast,
        LINKCAST_XHP_PATH: serveMethodNotAllowed,
        LINKCAST_HTML_PATH: serveMethodNotAllowed,
    }

    POST_HANDLERS = {
        INDEX_PATH: serveMethodNotAllowed,
        LINKCAST_CLOSE_PATH: serveMethodNotAllowed,
        LINKCAST_XHP_PATH: serveXhpLinkcast,
        LINKCAST_HTML_PATH: serveHtmlLinkcast,
    }


class RemoteControlBrowserService(xbmcaddon.Addon):

    def __init__(self):
        super(RemoteControlBrowserService, self).__init__()
        self.pluginId = self.getAddonInfo('id')
        self.addonFolder = xbmc.translatePath(
            self.getAddonInfo('path')).decode('utf_8')
        self.profileFolder = xbmc.translatePath(
            self.getAddonInfo('profile')).decode('utf_8')
        self.settingsChangeLock = threading.Lock()
        self.isShutdown = False
        self.linkcastServer = None
        self.linkcastServerThread = None

    def clearBrowserLock(self):
        """Clears the pidfile in case the last shutdown was not clean"""
        browserLockPath = os.path.join(self.profileFolder, 'browser.pid')
        try:
            os.remove(browserLockPath)
        except OSError:
            pass

    def buildPluginUrl(self, query):
        return urlparse.ParseResult(
            scheme='plugin',
            netloc=self.pluginId,
            path='/',
            params=None,
            query=urllib.urlencode(query),
            fragment=None).geturl()

    def getDefaults(self):
        dependenciesPath = os.path.join(
            self.addonFolder, 'resources/data/dependencies.xml')
        tree = xml.etree.ElementTree.parse(dependenciesPath)

        for platform in tree.iter('platform'):
            platformId = platform.get('id')
            if xbmc.getCondVisibility(platformId):
                browserPath = ''
                browserArgs = ''
                xdotoolPath = ''
                for xdotool in platform.iter('xdotool'):
                    if os.path.exists(xdotool.get('path')):
                        xdotoolPath = xdotool.get('path')
                        break
                for browser in platform.iter('browser'):
                    if os.path.exists(browser.get('path')):
                        browserPath = browser.get('path')
                        browserArgs = browser.get('args')
                        break
                return DetectedDefaults(browserPath, browserArgs, xdotoolPath)
        raise RuntimeError('Platform not supported')

    def marshalBool(self, val):
        BOOL_ENCODING = {False: 'false', True: 'true'}
        return BOOL_ENCODING[bool(val)]

    def unmarshalBool(self, val):
        STRING_ENCODING = {'false': False, 'true': True}
        unmarshalled = STRING_ENCODING.get(val)
        if unmarshalled is None:
            raise ValueError('Invalid Boolean: ' + str(val))
        return unmarshalled

    def generateSettings(self):
        xbmc.log('Generating default addon settings')
        root = xml.etree.ElementTree.Element('settings')
        dependencies = xml.etree.ElementTree.SubElement(
            root, 'category', {'label': '30018'})
        defaults = self.getDefaults()

        xml.etree.ElementTree.SubElement(dependencies, 'setting', {
            'id': 'browserPath',
            'type': 'executable',
            'label': '30019',
            'default': defaults.browserPath})
        xml.etree.ElementTree.SubElement(dependencies, 'setting', {
            'id': 'browserArgs',
            'type': 'text',
            'label': '30020',
            'default': defaults.browserArgs})
        xml.etree.ElementTree.SubElement(dependencies, 'setting', {
            'id': 'xdotoolPath',
            'type': 'executable',
            'label': '30021',
            'default': defaults.xdotoolPath})
        xml.etree.ElementTree.SubElement(dependencies, 'setting', {
            'id': 'linkcastEnabled',
            'type': 'bool',
            'label': '30030',
            'default': self.marshalBool(False)})
        xml.etree.ElementTree.SubElement(dependencies, 'setting', {
            'id': 'linkcastPort',
            'type': 'number',
            'label': '30031',
            'subsetting': self.marshalBool(True),
            'enable': 'eq(-1,true)',
            'default': str(DEFAULT_LINKCAST_PORT)})
        xml.etree.ElementTree.SubElement(dependencies, 'setting', {
            'type': 'lsep',
            'label': '30022',
            'visible': self.marshalBool(not psutil)})
        xml.etree.ElementTree.SubElement(dependencies, 'setting', {
            'type': 'lsep',
            'label': '30023',
            'visible': self.marshalBool(not alsaaudio)})
        xml.etree.ElementTree.SubElement(dependencies, 'setting', {
            'type': 'lsep',
            'label': '30024',
            'visible': self.marshalBool(not pylirc)})

        tree = xml.etree.ElementTree.ElementTree(root)
        settingsPath = os.path.join(self.addonFolder, 'resources/settings.xml')
        tree.write(settingsPath, encoding='UTF-8', xml_declaration=True)

    def reloadLinkcastServer(self):
        linkcastEnabled = self.unmarshalBool(
            self.getSetting('linkcastEnabled'))
        xbmc.log('Linkcast is enabled: ' + str(linkcastEnabled), xbmc.LOGDEBUG)
        with self.settingsChangeLock:
            if linkcastEnabled:
                self.startLinkcastServer()
            else:
                self.stopLinkcastServer()

    def startLinkcastServer(self):
        if self.isShutdown:
            return

        self.stopLinkcastServer()

        linkcastPort = int(self.getSetting('linkcastPort'))
        xbmc.log('Starting linkcast server on port ' + str(linkcastPort))
        try:
            self.linkcastServer = LinkcastServer(self, ('', linkcastPort))
        except IOError as e:
            xbmc.log('Could not start linkcast server: ' + str(e))

        threadStarting = threading.Thread(
            target=self.linkcastServer.serve_forever)
        threadStarting.start()
        self.linkcastServerThread = threadStarting

    def stopLinkcastServer(self):
        if self.linkcastServer is not None:
            xbmc.log('Stopping linkcast server')
            self.linkcastServer.shutdown()
            self.linkcastServer = None
        if self.linkcastServerThread is not None:
            xbmc.log('Joining linkcast server thread', xbmc.LOGDEBUG)
            self.linkcastServerThread.join()
            xbmc.log('Joined linkcast server thread', xbmc.LOGDEBUG)
            self.linkcastServerThread = None

    def shutdownLinkcastServer(self):
        xbmc.log('Shutting down linkcast server', xbmc.LOGDEBUG)
        with self.settingsChangeLock:
            self.stopLinkcastServer()
            self.isShutdown = True


def main():
    service = RemoteControlBrowserService()
    service.clearBrowserLock()
    service.generateSettings()
    monitor = LinkcastMonitor(service)
    service.reloadLinkcastServer()

    monitor.waitForAbort()

    service.shutdownLinkcastServer()


if __name__ == "__main__":
    main()
