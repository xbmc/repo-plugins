# -*- coding: utf-8 -*-
"""
    Copyright (C) 2020 Tubed (plugin.video.tubed)

    This file is part of plugin.video.tubed

    SPDX-License-Identifier: GPL-2.0-only
    See LICENSES/GPL-2.0-only.txt for more information.
"""

import xbmc  # pylint: disable=import-error
import xbmcgui  # pylint: disable=import-error

from ..generators.utils import get_thumbnail
from ..lib.memoizer import reset_cache
from ..lib.txt_fmt import bold
from ..lib.txt_fmt import color
from ..storage.users import UserStorage


def invoke(context):  # pylint: disable=too-many-branches,too-many-statements
    users = UserStorage()

    reference = []
    choices = []

    if not users.avatar and users.access_token:
        _payload = context.api.channels('mine', fields='items(snippet(thumbnails))')
        _items = _payload.get('items', [{}])
        _snippet = _items[0].get('snippet', {})
        thumbnail = get_thumbnail(_snippet)
        if thumbnail:
            users.avatar = thumbnail
            users.save()
            users.load()

    for user in users.users:
        reference.append(user)

        name = user['name']
        avatar = user['avatar'] or 'DefaultUser.png'

        if user['uuid'] == users.uuid:
            name = bold(color(name, 'lightgreen'))

        if user.get('access_token'):
            authenticated_message = context.i18n('User is authenticated')
        else:
            authenticated_message = context.i18n('User is not authenticated')

        item = xbmcgui.ListItem(label=name, label2=authenticated_message)
        item.setArt({
            'icon': avatar,
            'thumb': avatar,
        })

        choices.append(item)

    action_count = 3
    action_reference = []
    default_action_thumbnail = 'DefaultProgram.png'

    item = xbmcgui.ListItem(label=bold(context.i18n('New user...')),
                            label2=context.i18n('Create a new user'))
    item.setArt({
        'icon': default_action_thumbnail,
        'thumb': default_action_thumbnail,
    })
    choices.append(item)
    action_reference.append('new')

    item = xbmcgui.ListItem(label=bold(context.i18n('Rename user...')),
                            label2=context.i18n('Rename a current user'))
    item.setArt({
        'icon': default_action_thumbnail,
        'thumb': default_action_thumbnail,
    })
    choices.append(item)
    action_reference.append('rename')

    item = xbmcgui.ListItem(label=bold(context.i18n('Change avatar...')),
                            label2=context.i18n('Change a current user\'s avatar'))
    item.setArt({
        'icon': 'DefaultPicture.png',
        'thumb': 'DefaultPicture.png',
    })
    choices.append(item)
    action_reference.append('avatar')

    if len(reference) > 1:
        action_count += 1
        item = xbmcgui.ListItem(label=bold(context.i18n('Remove user...')),
                                label2=context.i18n('Remove a current user'))
        item.setArt({
            'icon': 'DefaultIconWarning.png',
            'thumb': 'DefaultIconWarning.png',
        })
        choices.append(item)
        action_reference.append('remove')

    result = xbmcgui.Dialog().select(context.i18n('Manage Users'), choices, useDetails=True)
    if result == -1:
        return

    choices = choices[:(len(choices) - action_count)]

    is_user = result <= (len(choices) - 1)
    if is_user:
        choice = reference[result]
        users.change_current(choice['uuid'])
        users.save()

    else:
        choice = action_reference[result - len(reference)]
        if choice == 'new':

            keyboard = xbmc.Keyboard()
            keyboard.setHeading(context.i18n('New Username'))
            keyboard.doModal()

            if keyboard.isConfirmed():
                new_username = keyboard.getText()
                new_username = new_username.strip()

                if not new_username:
                    return

                users.add(new_username)
                users.save()

        elif choice == 'rename':
            result = xbmcgui.Dialog().select(context.i18n('Rename user...'),
                                             choices, useDetails=True)
            if result == -1:
                return

            keyboard = xbmc.Keyboard()
            keyboard.setHeading(context.i18n('New Username'))
            keyboard.doModal()

            if keyboard.isConfirmed():
                new_username = keyboard.getText()
                new_username = new_username.strip()

                if not new_username:
                    return

                choice = reference[result]
                users.rename(choice['uuid'], new_username)
                users.save()

        elif choice == 'avatar':
            result = xbmcgui.Dialog().select(context.i18n('Change avatar...'),
                                             choices, useDetails=True)
            if result == -1:
                return

            file = xbmcgui.Dialog().browseSingle(
                2,
                context.i18n('Choose a new avatar'),
                'local',
                useThumbs=True
            )
            if file:
                users.avatar = file
                users.save()

        elif choice == 'remove':
            result = xbmcgui.Dialog().select(context.i18n('Remove user...'),
                                             choices, useDetails=True)
            if result == -1:
                return

            choice = reference[result]
            users.remove(choice['uuid'])
            users.save()

    reset_cache()
    xbmc.executebuiltin('Container.Refresh')
