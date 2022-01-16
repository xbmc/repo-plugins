
from xbmc import Monitor
from threading import Thread
from resources.lib.addon.plugin import get_setting
from resources.lib.addon.logger import kodi_log


class ParallelThread():
    def __init__(self, items, func, *args, **kwargs):
        """ ContextManager for running parallel threads alongside another function
        with ParallelThread(items, func, *args, **kwargs) as pt:
            pass
            item_queue = pt.queue
        item_queue[x]  # to get returned items
        """
        mon = Monitor()
        thread_max = get_setting('max_threads', mode='int') or len(items)
        self.queue = [None] * len(items)
        self._pool = [None] * thread_max
        for x, i in enumerate(items):
            n = x
            while n >= thread_max and not mon.abortRequested():  # Hit our thread limit so look for a spare spot in the queue
                for y, j in enumerate(self._pool):
                    if j.is_alive():
                        continue
                    n = y
                    break
                if n >= thread_max:
                    mon.waitForAbort(0.025)
            try:
                self._pool[n] = Thread(target=self._threadwrapper, args=[x, i, func, *args], kwargs=kwargs)
                self._pool[n].start()
            except IndexError:
                kodi_log(f'ParallelThread: INDEX {n} OUT OF RANGE {thread_max}', 1)

    def _threadwrapper(self, x, i, func, *args, **kwargs):
        self.queue[x] = func(i, *args, **kwargs)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        for i in self._pool:
            try:
                i.join()
            except AttributeError:  # is None
                pass
