# -*- coding: utf-8 -*-
"""

    Copyright (C) 2011-2018 PleXBMC (plugin.video.plexbmc) by hippojay (Dave Hawes-Johnson)
    Copyright (C) 2018-2020 Composite (plugin.video.composite_for_plex)

    This file is part of Composite (plugin.video.composite_for_plex)

    SPDX-License-Identifier: GPL-2.0-or-later
    See LICENSES/GPL-2.0-or-later.txt for more information.
"""

import json
from copy import deepcopy

from kodi_six import xbmc  # pylint: disable=import-error
from kodi_six import xbmcgui  # pylint: disable=import-error
from six.moves.urllib_parse import urlparse

from ..addon.data_cache import DATA_CACHE
from ..addon.logger import Logger
from ..addon.server_config import ServerConfigStore
from ..addon.strings import i18n
from ..plex import plex

LOG = Logger()
WINDOW = xbmcgui.Window(10000)


def run(context):
    manager = ServerManager(context)
    manager.run()


class ServerManager:

    def __init__(self, context):
        self._dialog = xbmcgui.Dialog()

        self.context = context
        self.context.plex_network = plex.Plex(context.settings, load=True)

        self.servers = list(context.plex_network.get_server_list())
        self.master = context.settings.master_server()

        self.server_configs = ServerConfigStore()

        self.server = None
        self.server_config = None
        self.access_urls = None
        self.test_results = None

    def run(self):
        server_data = self._get_server_data()
        if not server_data.get('labels'):
            self._refresh()
            return

        server_labels = server_data.get('labels', [])
        server_test_results = server_data.get('test_results', [])

        chosen_server = self._dialog.select(i18n('Manage Servers'), server_labels)
        if chosen_server < 0:
            self._refresh()
            return

        self.server = self.servers[chosen_server]
        self.server_config = self.server_configs.get_config(self.server.get_uuid())
        self.access_urls = self.server_configs.access_urls(self.server.get_uuid())
        self.test_results = server_test_results[chosen_server]

        management_choices = self._management_choices()
        management_choice = self._dialog.select(i18n('Manage Servers'), management_choices)
        if management_choice < 0:
            self._refresh()
            return

        self._process_management(management_choice)

        self._refresh()

    def _get_server_data(self):
        display_list = []
        test_results = []
        append_server = display_list.append
        append_test = test_results.append

        for server in self.servers:
            name = server.get_name()
            log_status = server.get_status()
            status_label = i18n(log_status)

            if server.is_secure():
                log_secure = 'SSL'
                secure_label = i18n(log_secure)
            else:
                log_secure = 'Not Secure'
                secure_label = i18n(log_secure)

            device_dump = deepcopy(server.__dict__)
            if self.context.settings.privacy():
                device_dump['token'] = 'XXXXXXXXXX'
                device_dump['plex_identification_header']['X-Plex-Token'] = 'XXXXXXXXXX'
                device_dump['plex_identification_header']['X-Plex-User'] = 'XXXXXXX'

            LOG.debug('Device: %s [%s] [%s]' % (name, log_status, log_secure))
            LOG.debugplus('Full device dump [%s]' % json.dumps(device_dump, indent=4))

            server_label = '%s [%s] [%s]' % (name, status_label, secure_label)
            if name == self.master:
                server_label = '[COLOR=lightgreen]%s[/COLOR]' % server_label

            append_server(server_label)
            append_test(device_dump.get('connection_test_results', []))

        return {
            'labels': display_list,
            'test_results': test_results,
        }

    def _management_choices(self):
        management_choices = []
        append_choice = management_choices.append

        if self.server.get_name() != self.master:
            append_choice(i18n('Set as Master'))

        append_choice(i18n('Connection Test Results'))

        if self.server_configs.ssl_certificate_verification(self.server.get_uuid()):
            append_choice('[COLOR=lightgreen]%s[/COLOR]' % i18n('Certificate Verification'))
        else:
            append_choice('[COLOR=orange]%s[/COLOR]' % i18n('Certificate Verification'))

        append_choice(i18n('Custom access urls'))

        return management_choices

    def _process_management(self, choice):
        if self.server.get_name() == self.master:
            choice += 1  # Choice 0 - 'Set as Master' not available on Master server

        if choice == 0:
            LOG.debug('Setting master server to: %s' % self.server.get_name())
            self.context.settings.set_master_server(self.server.get_name())

        elif choice == 1:
            self._show_connection_test()

        elif choice == 2:
            self._certificate_verification()

        elif choice == 3:
            self._custom_access_urls()

    def _certificate_verification(self):
        self.server_configs.toggle_certificate_verification(self.server.get_uuid())

    def _custom_access_urls(self):
        choices = []
        append_choice = choices.append

        append_choice(i18n('Add custom access url'))
        for url in self.access_urls:
            append_choice(url)

        choice = self._dialog.select(i18n('Custom access urls'), choices)
        if choice < 0:
            self._refresh()
            return

        if choice == 0:
            self._add_custom_access_url()
        else:
            self._modify_custom_access_url(choice - 1)  # shift index to compensate for 'add' choice

    def _add_custom_access_url(self, url_index=None):
        default = ''
        heading = i18n('Add custom access url')

        if url_index is not None:
            default = self.access_urls[url_index]
            heading = i18n('Edit custom access url')

        url = ''
        keyboard = xbmc.Keyboard(default, heading)
        keyboard.setHeading(heading)
        keyboard.doModal()
        if keyboard.isConfirmed():
            url = keyboard.getText()
            url = url.strip()

        is_url = self._validate_url(url)
        if is_url:
            self.server_configs.add_access_url(self.server.get_uuid(), url, url_index)
            self._refresh(clear_cache=True)
            WINDOW.setProperty('plugin.video.composite-refresh.servers', 'true')
            return

    def _modify_custom_access_url(self, url_index):
        choice = self._dialog.yesno(
            i18n('Custom access urls'),
            self.access_urls[url_index],
            nolabel=i18n('Delete'),
            yeslabel=i18n('Edit')
        )

        if choice:
            self._add_custom_access_url(url_index)
        else:
            self.server_configs.delete_access_url(self.server.get_uuid(), url_index)
            self._refresh(clear_cache=True)
            WINDOW.setProperty('plugin.video.composite-refresh.servers', 'true')
            return

    def _show_connection_test(self):
        addresses = []
        append_address = addresses.append
        for address in self.test_results:
            append_address('[COLOR %s]%s://%s/[/COLOR]' %
                           ('lightgreen' if address[3] else 'pink', address[1], address[2]))

        self._dialog.select(i18n('Connection Test Results'), addresses)

    @staticmethod
    def _validate_url(url):
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc, result.path])
        except:  # pylint: disable=bare-except
            return False

    @staticmethod
    def _refresh(clear_cache=False):
        if clear_cache:
            DATA_CACHE.delete_cache(True)
        xbmc.executebuiltin('Container.Refresh')
