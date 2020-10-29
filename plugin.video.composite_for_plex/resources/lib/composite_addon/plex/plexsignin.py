# -*- coding: utf-8 -*-
"""

    Copyright (C) 2011-2018 PleXBMC (plugin.video.plexbmc) by hippojay (Dave Hawes-Johnson)
    Copyright (C) 2018-2019 Composite (plugin.video.composite_for_plex)

    This file is part of Composite (plugin.video.composite_for_plex)

    SPDX-License-Identifier: GPL-2.0-or-later
    See LICENSES/GPL-2.0-or-later.txt for more information.
"""

import pyxbmct.addonwindow as pyxbmct  # pylint: disable=import-error
from kodi_six import xbmc  # pylint: disable=import-error
from kodi_six import xbmcgui  # pylint: disable=import-error
from kodi_six import xbmcvfs  # pylint: disable=import-error

from ..addon.constants import CONFIG
from ..addon.logger import Logger
from ..addon.strings import i18n

try:
    xbmc.translatePath = xbmcvfs.translatePath
except AttributeError:
    pass

LOG = Logger('plex_signin')
DIALOG = xbmcgui.Dialog()
MEDIA_PATH = xbmc.translatePath(CONFIG['media_path'] + 'dialogs/')


class AlreadyActiveException(Exception):
    pass


# noinspection PyAttributeOutsideInit
class PlexSignin(pyxbmct.AddonFullWindow):  # pylint: disable=too-many-instance-attributes
    def __init__(self, title='', window=None):
        """Class constructor"""
        # Call the base class' constructor.
        super(PlexSignin, self).__init__(title)  # pylint: disable=super-with-arguments
        # Set width, height and the grid parameters
        self.setGeometry(800, 400, 9, 21)
        # Call set controls method
        self.set_controls()
        # Call set navigation method.
        self.set_navigation()
        # Connect Backspace button to close our addon.
        self.connect(pyxbmct.ACTION_NAV_BACK, self.close)
        self.context = None
        self.identifier = None
        self.window = window
        self.data = {}

    def __enter__(self):
        if self.window.getProperty('-'.join([CONFIG['id'], 'dialog_active'])) == 'true':
            raise AlreadyActiveException
        self.window.setProperty('-'.join([CONFIG['id'], 'dialog_active']), 'true')
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.window.clearProperty('-'.join([CONFIG['id'], 'dialog_active']))

    def start(self):
        xbmc.executebuiltin('Dialog.Close(all,true)')
        self.display_pin()
        self.doModal()

    def set_context(self, context):
        self.context = context

    def set_controls(self):
        """Set up UI controls"""
        # Description Text
        self.description = pyxbmct.TextBox()
        self.placeControl(self.description, 1, 3, columnspan=15, rowspan=2)

        # success message
        self.success_message = pyxbmct.Label(i18n('Successfully signed in'), alignment=2)
        self.placeControl(self.success_message, 1, 3, columnspan=15, rowspan=2)

        # tick
        self.tick = pyxbmct.Image(MEDIA_PATH + 'tick.png', aspectRatio=2)
        self.placeControl(self.tick, 3, 9, columnspan=3, rowspan=3)

        # Username label
        self.name_label = pyxbmct.Label(i18n('Username:'), alignment=1)
        self.placeControl(self.name_label, 3, 3, columnspan=4)
        # username entry box
        self.name_field = pyxbmct.Edit('')
        self.placeControl(self.name_field, 3, 7, columnspan=10)
        if CONFIG['kodi_version'] > 17:
            self.name_field.setType(xbmcgui.INPUT_TYPE_TEXT, i18n('Username:'))

        # Password Label
        self.password_label = pyxbmct.Label(i18n('Password:'), alignment=1)
        self.placeControl(self.password_label, 4, 3, columnspan=4)
        # Password entry box
        if CONFIG['kodi_version'] < 18:
            self.password_field = pyxbmct.Edit('', isPassword=True)
        else:
            self.password_field = pyxbmct.Edit('')

        self.placeControl(self.password_field, 4, 7, columnspan=10)
        if CONFIG['kodi_version'] > 17:
            # must be done after control is placed
            self.password_field.setType(xbmcgui.INPUT_TYPE_PASSWORD, i18n('Password:'))

        # Cancel button
        self.cancel_button = pyxbmct.Button(i18n('Cancel'))
        self.placeControl(self.cancel_button, 6, 3, columnspan=5, rowspan=2)
        # Cancel button closes window
        self.connect(self.cancel_button, self.close)

        # Submit button
        self.submit_button = pyxbmct.Button(i18n('Submit'))
        self.placeControl(self.submit_button, 6, 8, columnspan=5, rowspan=2)
        # Submit button to get token

        # Manual button
        self.manual_button = pyxbmct.Button(i18n('Manual'))
        self.placeControl(self.manual_button, 6, 13, columnspan=5, rowspan=2)

        # PIN button
        self.pin_button = pyxbmct.Button(i18n('Use PIN'))
        self.placeControl(self.pin_button, 6, 13, columnspan=5, rowspan=2)

        # PIN button
        self.submit_pin_button = pyxbmct.Button(i18n('Done'))
        self.placeControl(self.submit_pin_button, 6, 8, columnspan=5, rowspan=2)

        # Submit button to get token
        self.connect(self.submit_button, lambda: self.submit())  # pylint: disable=unnecessary-lambda
        self.connect(self.manual_button, lambda: self.display_manual())  # pylint: disable=unnecessary-lambda
        self.connect(self.pin_button, lambda: self.display_pin())  # pylint: disable=unnecessary-lambda
        self.connect(self.submit_pin_button, lambda: self.submit_pin())  # pylint: disable=unnecessary-lambda

        # set up failure message
        self.error_cross = pyxbmct.Image(MEDIA_PATH + 'error.png', aspectRatio=2)
        self.placeControl(self.error_cross, 5, 6)
        self.error_message = pyxbmct.Label(i18n('Unable to sign in'))
        self.placeControl(self.error_message, 5, 7, columnspan=7, rowspan=1)
        self.error_cross.setVisible(False)
        self.error_message.setVisible(False)

        self.digit_one = pyxbmct.Image(MEDIA_PATH + '-.png', aspectRatio=2)
        self.digit_two = pyxbmct.Image(MEDIA_PATH + '-.png', aspectRatio=2)
        self.digit_three = pyxbmct.Image(MEDIA_PATH + '-.png', aspectRatio=2)
        self.digit_four = pyxbmct.Image(MEDIA_PATH + '-.png', aspectRatio=2)

        self.placeControl(self.digit_one, 3, 5, columnspan=2, rowspan=2)
        self.placeControl(self.digit_two, 3, 8, columnspan=2, rowspan=2)
        self.placeControl(self.digit_three, 3, 11, columnspan=2, rowspan=2)
        self.placeControl(self.digit_four, 3, 14, columnspan=2, rowspan=2)

    def display_failure(self, state=True):
        if state:
            self.error_cross.setVisible(True)
            self.error_message.setVisible(True)
        else:
            self.error_cross.setVisible(False)
            self.error_message.setVisible(False)

    def display_pin(self, failure=False):
        if failure:
            self.display_failure()
        else:
            self.display_failure(False)

        self.success_message.setVisible(False)
        self.tick.setVisible(False)
        self.description.setText(i18n('From your computer, go to %s and enter the code below') %
                                 '[B]https://www.plex.tv/link/[/B]')
        self.name_label.setVisible(False)
        self.password_label.setVisible(False)
        self.name_field.setVisible(False)
        self.password_field.setVisible(False)
        self.manual_button.setVisible(True)
        self.submit_button.setVisible(False)
        self.pin_button.setVisible(False)
        self.submit_pin_button.setVisible(True)
        self.cancel_button.setNavigation(self.submit_pin_button, self.manual_button,
                                         self.manual_button, self.submit_pin_button)
        self.submit_pin_button.setNavigation(self.manual_button, self.cancel_button,
                                             self.cancel_button, self.manual_button)
        self.manual_button.setNavigation(self.cancel_button, self.submit_pin_button,
                                         self.submit_pin_button, self.cancel_button)

        self.data = self.context.plex_network.get_signin_pin()

        digits = self.data['code']
        self.identifier = self.data['id']
        self.digit_one.setVisible(True)
        self.digit_two.setVisible(True)
        self.digit_three.setVisible(True)
        self.digit_four.setVisible(True)

        self.digit_one.setImage(MEDIA_PATH + digits[0].lower() + '.png')
        self.digit_two.setImage(MEDIA_PATH + digits[1].lower() + '.png')
        self.digit_three.setImage(MEDIA_PATH + digits[2].lower() + '.png')
        self.digit_four.setImage(MEDIA_PATH + digits[3].lower() + '.png')

        self.setFocus(self.submit_pin_button)

    def display_manual(self, failure=False):
        self.success_message.setVisible(False)
        self.tick.setVisible(False)
        self.description.setText(i18n('Enter your myPlex details below'))
        self.name_label.setVisible(True)
        self.password_label.setVisible(True)
        self.name_field.setVisible(True)
        self.password_field.setVisible(True)
        self.manual_button.setVisible(False)
        self.submit_button.setVisible(True)
        self.pin_button.setVisible(True)
        self.cancel_button.setNavigation(self.password_field, self.name_field,
                                         self.submit_button, self.pin_button)
        self.pin_button.setNavigation(self.password_field, self.name_field,
                                      self.cancel_button, self.submit_button)
        self.submit_button.setNavigation(self.password_field, self.name_field,
                                         self.pin_button, self.cancel_button)
        self.digit_one.setVisible(False)
        self.digit_two.setVisible(False)
        self.digit_three.setVisible(False)
        self.digit_four.setVisible(False)
        self.submit_pin_button.setVisible(False)
        self.setFocus(self.name_field)

        if failure:
            self.display_failure()
        else:
            self.display_failure(False)

    def submit(self):
        token = self.context.plex_network.sign_into_myplex(self.name_field.getText(),
                                                           self.password_field.getText())

        if token is not None:
            self.display_failure(False)

            self.description.setVisible(False)
            self.name_label.setVisible(False)
            self.password_label.setVisible(False)
            self.name_field.setVisible(False)
            self.password_field.setVisible(False)
            self.manual_button.setVisible(False)
            self.cancel_button.setVisible(False)
            self.submit_button.setVisible(False)
            self.pin_button.setVisible(False)

            self.success_message.setVisible(True)
            self.tick.setVisible(True)

            xbmc.sleep(2000)

            LOG.debug(i18n('Successfully signed in'))
            self.close()
        else:
            LOG.debug(i18n('Sign in not successful'))
            self.display_manual(True)

    def submit_pin(self):
        result = self.context.plex_network.check_signin_status(self.identifier)

        if result:
            self.display_failure(False)

            self.description.setVisible(False)
            self.digit_one.setVisible(False)
            self.digit_two.setVisible(False)
            self.digit_three.setVisible(False)
            self.digit_four.setVisible(False)
            self.manual_button.setVisible(False)
            self.cancel_button.setVisible(False)
            self.submit_button.setVisible(False)
            self.pin_button.setVisible(False)
            self.submit_pin_button.setVisible(False)

            self.success_message.setVisible(True)
            self.tick.setVisible(True)

            xbmc.sleep(2000)

            LOG.debug(i18n('Successfully signed in'))
            self.close()
        else:
            LOG.debug(i18n('Sign in not successful'))
            self.display_pin(True)

    def set_navigation(self):
        """Set up keyboard/remote navigation between controls."""
        self.name_field.controlUp(self.submit_button)
        self.name_field.controlDown(self.password_field)
        self.password_field.controlUp(self.name_field)
        self.password_field.controlDown(self.submit_button)
        # Set initial focus.

    def signed_in(self):
        return self.context.plex_network.is_myplex_signedin()


# noinspection PyAttributeOutsideInit
class PlexManage(pyxbmct.AddonFullWindow):  # pylint: disable=too-many-instance-attributes
    def __init__(self, title='', window=None):
        """Class constructor"""
        # Call the base class' constructor.
        super(PlexManage, self).__init__(title)  # pylint: disable=super-with-arguments
        # Set width, height and the grid parameters
        self.setGeometry(800, 400, 9, 21)
        # Call set controls method
        self.set_controls()
        # Call set navigation method.
        self.set_navigation()
        # Connect Backspace button to close our addon.
        self.connect(pyxbmct.ACTION_NAV_BACK, self.close)
        self.context = None
        self.window = window

    def __enter__(self):
        if self.window.getProperty('-'.join([CONFIG['id'], 'dialog_active'])) == 'true':
            raise AlreadyActiveException
        self.window.setProperty('-'.join([CONFIG['id'], 'dialog_active']), 'true')
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.window.clearProperty('-'.join([CONFIG['id'], 'dialog_active']))

    def start(self):
        xbmc.executebuiltin('Dialog.Close(all,true)')
        self.gather_plex_information()
        self.setFocus(self.cancel_button)
        self.doModal()

    def gather_plex_information(self):
        user = self.context.plex_network.get_myplex_information()

        self.name_field.addLabel(user['username'])
        self.email_field.addLabel(user['email'])
        self.plexpass_field.addLabel(user['plexpass'])
        self.membersince_field.addLabel(user['membersince'])
        if user['thumb']:
            self.thumb.setImage(user['thumb'])

    def set_context(self, context):
        self.context = context

    def set_controls(self):
        """Set up UI controls"""
        # Description Text
        self.description = pyxbmct.TextBox()
        self.placeControl(self.description, 2, 0, columnspan=4)

        # Username label
        self.name_label = pyxbmct.Label('[B]%s[/B]' % i18n('Username:'), alignment=1)
        self.placeControl(self.name_label, 1, 3, columnspan=4)
        # username fade label
        self.name_field = pyxbmct.FadeLabel()
        self.placeControl(self.name_field, 1, 7, columnspan=8)

        # thumb label
        self.thumb = pyxbmct.Image('', aspectRatio=2)
        self.placeControl(self.thumb, 1, 15, rowspan=2, columnspan=2)

        # Email Label
        self.email_label = pyxbmct.Label('[B]%s[/B]' % i18n('Email:'), alignment=1)
        self.placeControl(self.email_label, 2, 3, columnspan=4)
        # Email fade label
        self.email_field = pyxbmct.FadeLabel()
        self.placeControl(self.email_field, 2, 7, columnspan=8)

        # plexpass Label
        self.plexpass_label = pyxbmct.Label('[B]%s[/B]' % i18n('Plex Pass:'), alignment=1)
        self.placeControl(self.plexpass_label, 3, 3, columnspan=4)
        # Password columnspan=4
        self.plexpass_field = pyxbmct.FadeLabel()
        self.placeControl(self.plexpass_field, 3, 7, columnspan=8)

        # Member since Label
        self.membersince_label = pyxbmct.Label('[B]%s[/B]' % i18n('Joined:'), alignment=1)
        self.placeControl(self.membersince_label, 4, 3, columnspan=4)
        # Member since fade label
        self.membersince_field = pyxbmct.FadeLabel()
        self.placeControl(self.membersince_field, 4, 7, columnspan=8)

        # Cancel button
        self.cancel_button = pyxbmct.Button(i18n('Exit'))
        self.placeControl(self.cancel_button, 6, 4, columnspan=4, rowspan=2)
        # Cancel button closes window

        # Switch button
        self.switch_button = pyxbmct.Button(i18n('Switch User'))
        self.placeControl(self.switch_button, 6, 8, columnspan=5, rowspan=2)

        # Signout button
        self.signout_button = pyxbmct.Button(i18n('Sign Out'))
        self.placeControl(self.signout_button, 6, 13, columnspan=4, rowspan=2)

        # Submit button to get token
        self.connect(self.cancel_button, self.close)
        self.connect(self.switch_button, lambda: self.switch())  # pylint: disable=unnecessary-lambda
        self.connect(self.signout_button, lambda: self.signout())  # pylint: disable=unnecessary-lambda

    def switch(self):
        switched = switch_user(self.context, refresh=False)
        if switched:
            self.close()

    def signout(self):
        sign_out(self.context, refresh=False)
        if not self.context.plex_network.is_myplex_signedin():
            self.close()

    def set_navigation(self):
        """Set up keyboard/remote navigation between controls."""
        self.cancel_button.setNavigation(self.switch_button, self.signout_button,
                                         self.signout_button, self.switch_button)
        self.switch_button.setNavigation(self.signout_button, self.cancel_button,
                                         self.cancel_button, self.signout_button)
        self.signout_button.setNavigation(self.cancel_button, self.switch_button,
                                          self.switch_button, self.cancel_button)


def manage_plex(context):
    try:
        with PlexManage(i18n('Manage myPlex'), window=xbmcgui.Window(10000)) as dialog:
            dialog.set_context(context)
            dialog.start()
    except AlreadyActiveException:
        pass
    except AttributeError:
        LOG.debug('Failed to load PlexManage ...')


def sign_in_to_plex(context, refresh=True):
    status = False
    try:
        with PlexSignin(i18n('myPlex Login'), window=xbmcgui.Window(10000)) as dialog:
            dialog.set_context(context)
            dialog.start()
            status = dialog.signed_in()
    except AlreadyActiveException:
        pass
    except AttributeError:
        response = context.plex_network.get_signin_pin()
        message = \
            i18n('From your computer, go to [B]%s[/B] and enter the following code: [B]%s[/B]') % \
            ('https://www.plex.tv/link/', ' '.join(response.get('code', [])))
        DIALOG.ok(i18n('myPlex Login'), message)
        xbmc.sleep(500)
        result = context.plex_network.check_signin_status(response.get('id', ''))
        if result:
            status = True
            LOG.debug('Sign in successful ...')
        else:
            LOG.debug('Sign in failed ...')

        if refresh:
            xbmc.executebuiltin('Container.Refresh')

    return status


def sign_out(context, refresh=True):
    can_signout = True
    if not context.plex_network.is_admin():
        can_signout = False
        _ = DIALOG.ok(i18n('Sign Out'),
                      i18n('To sign out you must be logged in as an admin user. '
                           'Switch user and try again'))
    if can_signout:
        result = DIALOG.yesno(i18n('myPlex'),
                              i18n('You are currently signed into myPlex.'
                                   ' Are you sure you want to sign out?'))
        if result:
            context.plex_network.signout()
            if refresh:
                xbmc.executebuiltin('Container.Refresh')


def switch_user(context, refresh=True):
    user_list = context.plex_network.get_plex_home_users()
    # zero means we are not plexHome'd up
    if user_list is None or len(user_list) == 1:
        LOG.debug('No users listed or only one user, Plex Home not enabled')
        return False

    LOG.debug('found %s users: %s' % (len(user_list), user_list.keys()))

    # Get rid of currently logged in user.
    user_list.pop(context.plex_network.get_myplex_user(), None)

    result = DIALOG.select(i18n('Switch User'), user_list.keys())
    if result == -1:
        LOG.debug('Dialog cancelled')
        return False

    LOG.debug('user [%s] selected' % user_list.keys()[result])
    user = user_list[user_list.keys()[result]]

    pin = None
    if user['protected'] == '1':
        LOG.debug('Protected user [%s], requesting password' % user['title'])
        pin = DIALOG.input(i18n('Enter PIN'), type=xbmcgui.INPUT_NUMERIC,
                           option=xbmcgui.ALPHANUM_HIDE_INPUT)

    success, message = context.plex_network.switch_plex_home_user(user['id'], pin)

    if not success:
        DIALOG.ok(i18n('Switch Failed'), message)
        LOG.debug('Switch User Failed')
        return False

    if refresh:
        xbmc.executebuiltin('Container.Refresh')

    return True
