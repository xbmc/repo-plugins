# -*- coding: utf-8 -*-
"""
    Copyright (C) 2020 Tubed (plugin.video.tubed)

    This file is part of plugin.video.tubed

    SPDX-License-Identifier: GPL-2.0-only
    See LICENSES/GPL-2.0-only.txt for more information.
"""

import os
import time
from urllib.parse import quote
from uuid import uuid4
from xml.etree import ElementTree

import xbmc  # pylint: disable=import-error
import xbmcvfs  # pylint: disable=import-error

from ..constants import ADDONDATA_PATH
from ..lib.logger import Log
from ..lib.url_utils import unquote

LOG = Log('storage', __file__)


class UserStorage:
    __template_root = \
        '''
<users>
    <user current="true">
        <name>Default</name>
        <uuid>%s</uuid>
        <refresh_token></refresh_token>
        <access_token></access_token>
        <token_expiry>-1</token_expiry>
        <history_playlist></history_playlist>
        <watchlater_playlist></watchlater_playlist>
        <avatar></avatar>
    </user>
</users>
        '''

    __template_user = \
        '''
    <user current="false">
        <name>%s</name>
        <uuid>%s</uuid>
        <refresh_token></refresh_token>
        <access_token></access_token>
        <token_expiry>-1</token_expiry>
        <history_playlist></history_playlist>
        <watchlater_playlist></watchlater_playlist>
        <avatar></avatar>
    </user>
        '''

    def __init__(self):

        self.filename = os.path.join(ADDONDATA_PATH, 'users.xml')
        self.lock_filename = os.path.join(ADDONDATA_PATH, 'users.lock')

        self.monitor = xbmc.Monitor()

        self.root = None

        self._users = None
        self._user = None

        self._uuid = str(uuid4().hex)[:8]

        self.init()

    @property
    def users(self):
        if self._users:
            return self._users

        user_elements = self.root.findall('./user')
        payload = []

        for user in user_elements:
            try:
                uuid = user.find('uuid').text
                name = user.find('name').text

                avatar = self._get_elements_text(user, 'avatar')

                refresh_token = self._get_elements_text(user, 'refresh_token')
                access_token = self._get_elements_text(user, 'access_token')
                token_expiry = self._get_elements_text(user, 'token_expiry', -1)

                current = user.attrib.get('current', 'false').lower() == 'true'

                history_playlist = self._get_elements_text(user, 'history_playlist')
                watchlater_playlist = self._get_elements_text(user, 'watchlater_playlist')

                payload.append({
                    'uuid': unquote(uuid),
                    'name': unquote(name),
                    'current': current,
                    'refresh_token': refresh_token,
                    'access_token': access_token,
                    'token_expiry': token_expiry,
                    'history_playlist': history_playlist,
                    'watchlater_playlist': watchlater_playlist,
                    'avatar': avatar,
                })

            except:  # pylint: disable=bare-except
                pass

        self._users = payload
        return payload

    @property
    def username(self):
        return self._current_user_get('name', '')

    @username.setter
    def username(self, value):
        self._current_user_set('name', value)

    @property
    def avatar(self):
        return self._current_user_get('avatar', '')

    @avatar.setter
    def avatar(self, value):
        self._current_user_set('avatar', value)

    @property
    def uuid(self):
        return self._current_user_get('uuid', '')

    @property
    def refresh_token(self):
        return self._current_user_get('refresh_token', '')

    @refresh_token.setter
    def refresh_token(self, value):
        self._current_user_set('refresh_token', value)

    @property
    def access_token(self):
        return self._current_user_get('access_token', '')

    @access_token.setter
    def access_token(self, value):
        self._current_user_set('access_token', value)

    @property
    def history_playlist(self):
        return self._current_user_get('history_playlist', '')

    @history_playlist.setter
    def history_playlist(self, value):
        self._current_user_set('history_playlist', value)

    @property
    def watchlater_playlist(self):
        return self._current_user_get('watchlater_playlist', '')

    @watchlater_playlist.setter
    def watchlater_playlist(self, value):
        self._current_user_set('watchlater_playlist', value)

    @property
    def token_expiry(self):
        return float(self._current_user_get('token_expiry', -1))

    @token_expiry.setter
    def token_expiry(self, value):
        self._current_user_set('token_expiry', str(value))

    @property
    def token_expired(self):
        if not self.access_token:
            return True

        # in this case no expiration date was set
        if self.token_expiry == -1:
            return False

        return self.token_expiry <= int(time.time())

    def change_current(self, user_uuid):
        user = self.root.find('.//user[@current="true"]')

        user_elements = self.root.findall('./user')
        for user_element in user_elements:
            uuid_element = user_element.find('uuid')

            if not hasattr(uuid_element, 'text'):
                continue

            if unquote(uuid_element.text) == user_uuid:
                self._reset()

                user.attrib['current'] = 'false'
                user_element.attrib['current'] = 'true'
                break

    def add(self, name):
        self._reset()

        user_template = self.__template_user % (quote(name), quote(str(uuid4())))
        user_element = ElementTree.fromstring(user_template)
        self.root.append(user_element)

    def remove(self, user_uuid):
        self._reset()

        new_uuid = None
        remove = False
        user_elements = self.root.findall('./user')
        for user_element in user_elements:
            uuid_element = user_element.find('uuid')

            if not hasattr(uuid_element, 'text'):
                continue

            if unquote(uuid_element.text) == user_uuid:
                remove = user_element
            else:
                new_uuid = unquote(uuid_element.text)

            if remove and new_uuid:
                break

        if remove and new_uuid:
            if self.uuid == user_uuid:
                self.change_current(new_uuid)

            self.root.remove(remove)

    def rename(self, user_uuid, new_name):
        self._reset()

        user_elements = self.root.findall('./user')
        for user_element in user_elements:
            uuid_element = user_element.find('uuid')
            name_element = user_element.find('name')

            if not hasattr(uuid_element, 'text') or not hasattr(name_element, 'text'):
                continue

            if uuid_element.text == user_uuid:
                name_element.text = quote(new_name)
                break

    def init(self):
        self._reset()
        try:
            if xbmcvfs.exists(self.filename):
                self.load()
            else:
                self.root = ElementTree.fromstring(self.__template_root % str(uuid4()))
                self.save()
        except FileNotFoundError:
            self.root = ElementTree.fromstring(self.__template_root % str(uuid4()))
            self.save()

    def locked(self):
        return xbmcvfs.exists(self.lock_filename)

    def lock(self):

        timeout = 60.0
        sleep_time = 0.1
        slept_for = 0.0

        while not self.monitor.abortRequested() and slept_for < timeout and self.locked():
            if self.monitor.waitForAbort(sleep_time):
                break

            slept_for += sleep_time

            LOG.debug('[%s] Attemping to aquire lock %s/%s ...' %
                      (self._uuid, str(slept_for), str(timeout)))

        if not self.locked():
            with xbmcvfs.File(self.lock_filename, 'w') as _:
                LOG.debug('[%s] Lock aquired' % self._uuid)

        else:
            LOG.error('[%s] Unable to aquire lock' % self._uuid)

    def unlock(self):
        if self.locked():
            xbmcvfs.delete(self.lock_filename)
            LOG.debug('[%s] Lock released' % self._uuid)

    def load(self):
        self.lock()
        try:
            if self.locked():
                self._reset()
                self.root = ElementTree.parse(self.filename).getroot()

        finally:
            self.unlock()

    def save(self):
        self.lock()
        try:
            if self.locked():
                with open(self.filename, 'wb') as file_handle:
                    file_handle.write(ElementTree.tostring(self.root,
                                                           short_empty_elements=False,
                                                           method='html'))
        finally:
            self.unlock()

    def _current_user_get(self, attrib, default=''):
        if self._user:
            return unquote(self._user.get(attrib, default))

        for user in self.users:
            if user.get('current'):
                self._user = user.copy()
                return unquote(user.get(attrib, default))

        return default

    def _current_user_set(self, attrib, value):
        user = self.root.find('.//user[@current="true"]')
        if not user:
            return

        element = user.find(attrib)
        if not hasattr(element, 'text'):
            element = None

        self._reset()
        if element is None:
            new_element = ElementTree.SubElement(user, attrib)
            new_element.text = quote(value)
        else:
            element.text = quote(value)

    def _reset(self):
        self._users = None
        self._user = None

    @staticmethod
    def _get_elements_text(user, element_name, default=''):
        payload = default

        element = user.find(element_name)
        if hasattr(element, 'text'):
            payload = element.text

        if payload is None:
            payload = default

        return unquote(payload)
