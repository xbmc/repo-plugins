#     Copyright 2011 Joachim Basmaison, Cyril Leclerc
#
#     This file is part of xbmc-qobuz.
#
#     xbmc-qobuz is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
#
#     xbmc-qobuz is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.   See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with xbmc-qobuz.   If not, see <http://www.gnu.org/licenses/>.

import os
import time
import random
import string
import re
from debug import warn


class FileUtil():

    def __init__(self):
        pass

    def generate_filename(self, size=8, chars=string.ascii_letters + string.digits):
        return ''.join(random.choice(chars) for x in range(size))

    def _write(self, path, flag, data):
        ret = False
        with os.open(path, flag) as fd:
            with os.fdopen(fd, 'wb') as fo:
                fo.write(data)
                # fo.flush()
                # os.fsync(fd)
                ret = True

        return ret

    def _unlink(self, path):
        if not os.path.exists(path):
            return False
        os.unlink(path)
        retry = 3
        ret = False
        while retry > 0:
            if not os.path.exists(path):
                return True
            time.sleep(.250)
            retry -= 1
        return False

    def _safe_unlink(self, path):
        if not os.path.exists(path):
            return True
        basepath = os.path.dirname(path)
        new = self.generate_filename() + '.' + self.generate_filename(3)
        newpath = os.path.join(basepath, new)
        os.rename(path, newpath)
        if not os.path.exists(newpath):
            return False
        return self._unlink(newpath)

    def write(self, path, data):
        if os.path.exists(path):
            return False
        return self._write(path, os.O_WRONLY | os.O_EXCL | os.O_CREAT, data)

    def unlink(self, path):
        return self._safe_unlink(path)

    ''' Find '''
    def find(self, directory, pattern, callback=None, gData=None):
        flist = []
        fok = re.compile(pattern)
        for dirname, dirnames, filenames in os.walk(directory):
            for filename in filenames:
                if fok.match(filename):
                    path = os.path.join(dirname, filename)
                    if callback:
                        try:
                            if not callback(path, gData):
                                return None
                        except Exception as e:
                            warn(self, "Callback raise exception: " + repr(e))
                            return None
                    flist.append(path)
        return flist
