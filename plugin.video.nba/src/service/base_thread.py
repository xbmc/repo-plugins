import threading

class BaseThread(threading.Thread):
    """ Convenience class for creating stoppable threads. """

    def __init__(self):
        threading.Thread.__init__(self)
        if hasattr(self, 'daemon'):
            self.daemon = True
        else:
            self.setDaemon(True)
        self._stopped_event = threading.Event()

        if not hasattr(self._stopped_event, 'is_set'):
            self._stopped_event.is_set = self._stopped_event.isSet

    @property
    def stopped_event(self):
        return self._stopped_event

    def should_keep_running(self):
        """Determines whether the thread should continue running."""
        return not self._stopped_event.is_set()

    def on_thread_stop(self):
        """Override this method instead of stop().
        stop() calls this method.
        This method is called immediately after the thread is signaled to stop.
        """
        pass

    def stop(self):
        """Signals the thread to stop."""
        self._stopped_event.set()
        self.on_thread_stop()

    def on_thread_start(self):
        """Override this method instead of start(). start()
        calls this method.
        This method is called right before this thread is started and this
        object's run() method is invoked.
        """
        pass

    def start(self):
        self.on_thread_start()
        threading.Thread.start(self)