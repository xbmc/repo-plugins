# -*- coding: utf-8 -*-
# GNU General Public License v2.0 (see COPYING or https://www.gnu.org/licenses/gpl-2.0.txt)
"""This is the actual Up Next API script"""

from __future__ import absolute_import, division, unicode_literals
from datetime import datetime, timedelta
from math import ceil
from xbmc import Monitor, sleep
from xbmcgui import WindowXMLDialog
from statichelper import from_unicode
from utils import addon_path, get_setting_bool, localize, localize_time


class TestPopup(WindowXMLDialog):
    ACTION_PLAYER_STOP = 13
    ACTION_NAV_BACK = 92
    progress_step_size = 0
    current_progress_percent = 100.0
    progress_control = None
    pause = False

    def onInit(self):  # pylint: disable=invalid-name
        self.set_info()
        self.prepare_progress_control()

        if get_setting_bool('stopAfterClose'):
            self.getControl(3013).setLabel(localize(30033))  # Stop
        else:
            self.getControl(3013).setLabel(localize(30034))  # Close

    def set_info(self):
        self.setProperty('clearart', 'https://fanart.tv/fanart/tv/121361/clearart/game-of-thrones-4fa1349588447.png')
        self.setProperty('clearlogo', 'https://fanart.tv/fanart/tv/121361/hdtvlogo/game-of-thrones-504c49ed16f70.png')
        self.setProperty('fanart', 'https://fanart.tv/fanart/tv/121361/showbackground/game-of-thrones-4fd5fa8ed5e1b.jpg')
        self.setProperty('landscape', 'https://fanart.tv/detailpreview/fanart/tv/121361/tvthumb/game-of-thrones-4f78ce73d617c.jpg')
        self.setProperty('poster', 'https://fanart.tv/fanart/tv/121361/tvposter/game-of-thrones-521441fd9b45b.jpg')
        self.setProperty('thumb', 'https://fanart.tv/fanart/tv/121361/showbackground/game-of-thrones-556979e5eda6b.jpg')

        self.setProperty('episode', '4')
        self.setProperty('playcount', '1')
        self.setProperty('plot', 'Lord Baelish arrives at Renly\'s camp just before he faces off against Stannis. '
                                 'Daenerys and her company are welcomed into the city of Qarth. Arya, Gendry, and '
                                 'Hot Pie find themselves imprisoned at Harrenhal.')
        self.setProperty('rating', '8.9')
        self.setProperty('season', '2')
        self.setProperty('seasonepisode', '2x4')
        self.setProperty('title', 'Garden of Bones')
        self.setProperty('tvshowtitle', 'Game of Thrones')
        self.setProperty('year', '2012')
        self.setProperty('runtime', '50')

    def prepare_progress_control(self):
        try:
            self.progress_control = self.getControl(3014)
        except RuntimeError:
            return
        self.progress_control.setPercent(100.0)  # pylint: disable=no-member,useless-suppression

    def update_progress_control(self, timeout, wait):
        if self.progress_control is None:
            return
        self.current_progress_percent -= 100 * wait / timeout
        self.progress_control.setPercent(self.current_progress_percent)  # pylint: disable=no-member,useless-suppression
        self.setProperty('remaining', from_unicode('%02d' % ceil((timeout / 1000) * (self.current_progress_percent / 100))))
        self.setProperty('endtime', from_unicode(localize_time(datetime.now() + timedelta(seconds=50 * 60))))

    def onFocus(self, controlId):  # pylint: disable=invalid-name
        pass

    def doAction(self):  # pylint: disable=invalid-name
        pass

    def closeDialog(self):  # pylint: disable=invalid-name
        self.close()

    def onClick(self, controlId):  # pylint: disable=invalid-name,unused-argument
        self.close()

    def onAction(self, action):  # pylint: disable=invalid-name
        if action == self.ACTION_PLAYER_STOP:
            self.close()
        elif action == self.ACTION_NAV_BACK:
            self.close()


def test_popup(window):
    popup = TestPopup(window, addon_path(), 'default', '1080i')
    popup.show()
    step = 0
    wait = 100
    timeout = 10000
    monitor = Monitor()
    while popup and step < timeout and not monitor.abortRequested():
        if popup.pause:
            continue
        sleep(wait)
        popup.update_progress_control(timeout, wait)
        step += wait


def open_settings():
    from xbmcaddon import Addon
    Addon().openSettings()


def run(argv):
    """Route to API method"""
    if len(argv) == 3 and argv[1] == 'test_window':
        test_popup(argv[2])
    else:
        open_settings()
