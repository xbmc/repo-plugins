# -*- coding: utf-8 -*-
""" Kodi Manifest Proxy

This Proxy is used to workaround an Inputstream Adaptive bug. For more info, see:
* https://github.com/add-ons/plugin.video.vtm.go/issues/241
* https://github.com/peak3d/inputstream.adaptive/pull/565
* https://github.com/peak3d/inputstream.adaptive/pull/566
"""

from __future__ import absolute_import, division, unicode_literals

import logging
import re
import threading

import requests

from resources.lib import kodiutils

try:  # Python 3
    from http.server import BaseHTTPRequestHandler
except ImportError:  # Python 2
    from BaseHTTPServer import BaseHTTPRequestHandler

try:  # Python 3
    from socketserver import TCPServer
except ImportError:  # Python 2
    from SocketServer import TCPServer

try:  # Python 3
    from urllib.parse import parse_qs, urlparse
except ImportError:  # Python 2
    from urlparse import parse_qs, urlparse

_LOGGER = logging.getLogger(__name__)


class Proxy(BaseHTTPRequestHandler):
    """ Manifest Proxy to workaround a Inputstream Adaptive bug """
    server_inst = None

    @staticmethod
    def start():
        """ Start the Proxy. """

        def start_proxy():
            """ Start the Proxy. """
            Proxy.server_inst = TCPServer(('127.0.0.1', 0), Proxy)
            port = Proxy.server_inst.socket.getsockname()[1]
            kodiutils.set_setting('manifest_proxy_port', str(port))
            _LOGGER.debug('Listening on port %s', port)

            # Start listening
            Proxy.server_inst.serve_forever()

        thread = threading.Thread(target=start_proxy)
        thread.start()

        return thread

    @staticmethod
    def stop():
        """ Stop the Proxy. """
        if Proxy.server_inst:
            Proxy.server_inst.shutdown()

    def do_GET(self):  # pylint: disable=invalid-name
        """ Handle http get requests, used for manifest. """
        _LOGGER.debug('HTTP GET Request received for %s', self.path)

        if not self.path.startswith('/manifest'):
            self.send_response(404)
            self.end_headers()
            return

        try:
            # Make real request
            params = parse_qs(urlparse(self.path).query)
            url = params.get('path')[0]
            _LOGGER.debug('Proxying to %s', url)
            response = requests.get(url=url)

            # Return response code
            self.send_response(response.status_code)
            self.end_headers()

            if response.status_code == 200:
                self.wfile.write(self.modify_manifest(response.text).encode())
            else:
                self.wfile.write(response.content)

        except Exception as exc:  # pylint: disable=broad-except
            _LOGGER.exception(exc)
            self.send_response(500)
            self.end_headers()

    @staticmethod
    def modify_manifest(manifest):
        """ Modify the manifest so Inputstream Adaptive can handle it. """

        def repl(matchobj):
            """ Modify an AdaptationSet. We will be removing default_KIDs, the BaseURL and prefixing it with the URL's in all SegmentTemplates. """
            adaptationset = matchobj.group(0)

            # Remove default_KIDs because the manifests from VTM GO have non cenc namespaced default_KID attributes in the ContentProtection tags and
            # InputStream Adaptive is picking them up but something is going wrong. More info: https://github.com/xbmc/inputstream.adaptive/issues/667#issuecomment-840849939
            adaptationset = re.sub(r' default_KID=\".*?\"', '', adaptationset)

            # Only process AdaptationSets that use a SegmentTemplate
            if '<SegmentTemplate' in adaptationset:

                # Extract BaseURL
                match = re.search(r'<BaseURL>(.*?)</BaseURL>', adaptationset)
                if match:
                    base_url = match.group(1)

                    # Remove BaseURL
                    adaptationset = re.sub(r'\s*?<BaseURL>.*?</BaseURL>', '', adaptationset)

                    # Prefix BaseURL on initialization=" and media=" tags
                    adaptationset = re.sub(r'(<SegmentTemplate[^>]*?initialization=\")([^\"]*)(\"[^>]*?>)', r'\1' + base_url + r'\2\3', adaptationset)
                    adaptationset = re.sub(r'(<SegmentTemplate[^>]*?media=\")([^\"]*)(\"[^>]*?>)', r'\1' + base_url + r'\2\3', adaptationset)

            return adaptationset

        # Process all AdaptationSets
        output = re.sub(r'<AdaptationSet[^>]*>(.*?)</AdaptationSet>', repl, manifest, flags=re.DOTALL)

        return output
