#===============================================================================
# LICENSE Retrospect-Framework - CC BY-NC-ND
#===============================================================================
# This work is licenced under the Creative Commons
# Attribution-Non-Commercial-No Derivative Works 3.0 Unported License. To view a
# copy of this licence, visit http://creativecommons.org/licenses/by-nc-nd/3.0/
# or send a letter to Creative Commons, 171 Second Street, Suite 300,
# San Francisco, California 94105, USA.
#===============================================================================

import os
import io
import datetime
import threading

# lock object to use.
cacheLock = threading.RLock()


def locked_read_write(origfunc):
    """ Decorator to execute function with a lock to prevent threading issues. """

    def execute_locked(*args, **kwargs):
        """ The method that is called when the Decorator is executed.

        Arguments:
        *args     : List[Object] - A list of arguments that will be used to
                                   substitute parameters in the message.

        Keyword Arguments:
        **kwargs  : Dictionary   - List of additional keyword arguments. Possible
                                   values are: "error = True"

        """

        cacheLock.acquire()
        try:
            return origfunc(*args, **kwargs)
        finally:
            cacheLock.release()

    return execute_locked


class StreamCache(object):
    def __init__(self, cache_path):
        self.cacheHits = 0
        self.cachePath = os.path.join(cache_path, "www")
        if not os.path.isdir(self.cachePath):
            os.makedirs(self.cachePath)

    @locked_read_write
    def set(self, key):
        file_name = os.path.join(self.cachePath, key)
        fp = io.open(file_name, mode="w+b")
        return fp

    @locked_read_write
    def get(self, key):
        file_name = os.path.join(self.cachePath, key)
        with io.open(file_name, mode="rb") as fp:
            return io.BytesIO(fp.read())

    def is_expired(self, key, seconds=3600):
        file_name = os.path.join(self.cachePath, key)
        if not os.path.isfile(file_name):
            return False

        store_time = datetime.datetime.fromtimestamp(os.path.getmtime(file_name))
        valid_until = store_time + datetime.timedelta(seconds=seconds)
        if valid_until < datetime.datetime.now():
            return True

        return False

    def has_cache_key(self, key):
        """ Returns if a key is present (expired or not) in the cache.

        Arguments:
        key     : String  - The key to use to check the cache values

        Returns True or False

        """

        file_name = os.path.join(self.cachePath, key)
        return os.path.isfile(file_name)

    def __str__(self):
        return "Cache store [{0}]".format(self.cachePath)
