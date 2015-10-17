'''
    qobuz.util.file
    ~~~~~~~~~~~~~~~

    :part_of: xbmc-qobuz
    :copyright: (c) 2012 by Joachim Basmaison, Cyril Leclerc
    :license: GPLv3, see LICENSE for more details.
'''
import os
import re
import tempfile

from debug import warn


def unlink(filename):
    if not os.path.exists(filename):
        return False
    tmpfile = tempfile.mktemp('.dat', 'invalid-', os.path.dirname(filename))
    os.rename(filename, tmpfile)
    return os.unlink(tmpfile)


class RenamedTemporaryFile(object):
    """A temporary file object which will be renamed to the specified
    path on exit.

    From http://stackoverflow.com/
        questions/12003805/threadsafe-and-fault-tolerant-file-writes
    """

    def __init__(self, final_path, **kwargs):
        tmpfile_dir = kwargs.pop('dir', None)

        # Put temporary file in the same directory as the location for the
        # final file so that an atomic move into place can occur.

        if tmpfile_dir is None:
            tmpfile_dir = os.path.dirname(final_path)

        self.tmpfile = tempfile.NamedTemporaryFile(dir=tmpfile_dir,
                                                   delete=False, **kwargs)
        self.final_path = final_path

    def __getattr__(self, attr):
        """Delegate attribute access to the underlying temporary file object.
        """
        return getattr(self.tmpfile, attr)

    def __enter__(self):
        self.tmpfile.__enter__()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self.tmpfile.delete = False
            result = self.tmpfile.__exit__(exc_type, exc_val, exc_tb)
            os.rename(self.tmpfile.name, self.final_path)
        else:
            self.tmpfile.delete = True
            result = self.tmpfile.__exit__(exc_type, exc_val, exc_tb)
            os.unlink(self.tmpfile.name)
        return result


def find(directory, pattern, callback=None, gData=None):
    flist = []
    fok = re.compile(pattern)
    for dirname, _dirnames, filenames in os.walk(directory):
        for filename in filenames:
            if fok.match(filename):
                path = os.path.join(dirname, filename)
                if callback:
                    try:
                        if not callback(path, gData):
                            return None
                    except Exception as e:
                        warn('[find]', 'Callback raise exception: '
                             '' + repr(e))
                        return None
                flist.append(path)
    return flist
