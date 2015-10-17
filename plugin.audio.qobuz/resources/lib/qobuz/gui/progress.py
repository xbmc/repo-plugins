'''
    qobuz.gui.progress
    ~~~~~~~~~~~~~~~~~~~

    :part_of: xbmc-qobuz
    :copyright: (c) 2012 by Joachim Basmaison, Cyril Leclerc
    :license: GPLv3, see LICENSE for more details.
'''
import time
import xbmcgui  # @UnresolvedImport
from debug import warn


def pretty_epoch(time):
    """Convert second to human readable format h:m:s
        Parameter:
            time: float, time in sec as returned by time.time()
        Return:
            string, Time formatted %
    """
    hours = (time / 3600)
    minutes = (time / 60) - (hours * 60)
    seconds = time % 60
    return '%02i:%02i:%02i' % (hours, minutes, seconds)


class Progress(xbmcgui.DialogProgress):
    """Displaying xbmc progress dialog
        Parameter:
            is_enable: bool (default: True)
    """

    def __init__(self, is_enable=True):
        self.is_enable = is_enable
        if self.is_enable:
            super(Progress, self).__init__()
        self.line1 = 'Working...'
        self.line2 = ''
        self.line3 = ''
        self.percent = 0
        self.started_on = None

    def create(self, line1, line2='', line3=''):
        """Create our progress dialog
        """
        self.line1 = line1
        self.line2 = line2
        self.line3 = line3
        if not self.is_enable:
            return True
        self.started_on = time.time()
        try:
            return super(Progress, self).create(line1, line2, line3)
        except:
            warn(self, "Cannot create progress bar")
            return False
        return True

    def update(self, percent, line1, line2='', line3=''):
        """Update our progress dialog
            Parameter:
                percent: int, between 0 and 100
                line1: string,
                line2: string,
                line3: string,
        """
        if line1:
            self.line1 = line1
        self.line2 = line2
        self.line3 = line3
        if not self.is_enable:
            return False
        elapsed = pretty_epoch((time.time() - self.started_on))
        try:
            return super(Progress, self).update(percent,
                                                '[%s]%s' % (elapsed, line1),
                                                line2, line3)
        except:
            warn(self, "Cannot update progress bar")
            return False

    def update_line1(self, line):
        """Only updating line1
        """
        if not line or line == self.line1:
            return False
        self.line1 = line
        try:
            return self.update(self.percent, self.line1, self.line2,
                               self.line3)
        except:
            warn(self, "Cannot update line1 progress bar")
            return False

    def iscanceled(self):
        """Return true if our dialog has been canceled by user
        """
        if not self.is_enable:
            return False
        bs = True
        try:
            bs = super(Progress, self).iscanceled()
        except:
            warn(self, 'Cannot cancel progress...')
            return True
        return bs

    def close(self):
        """Close our progress dialog
        """
        if not self.is_enable:
            return True
        try:
            return super(Progress, self).close()
        except:
            warn(self, "Cannot close progress bar")
            return False
