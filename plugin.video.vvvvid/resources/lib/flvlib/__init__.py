import os

# python 2.4 does not have os.SEEK_*
try:
    os.SEEK_SET
except AttributeError:
    os.SEEK_SET, os.SEEK_CUR, os.SEEK_END = range(3)

import logging

log = logging.getLogger('flvlib')
log.setLevel(logging.NOTSET)

handler = logging.StreamHandler()
handler.setLevel(logging.NOTSET)

formatter = logging.Formatter("%(levelname)-7s %(name)-20s "
                              "%(message)s (%(pathname)s:%(lineno)d)")
handler.setFormatter(formatter)

log.addHandler(handler)

__version__ = (0, 1, 12)
__versionstr__ = '.'.join([str(n) for n in __version__])
