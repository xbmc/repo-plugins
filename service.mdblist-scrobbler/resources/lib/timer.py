import threading


class Timer(threading.Thread):
    def __init__(self, interval: int, callback: callable):
        super().__init__()

        self.interval = interval
        self.callback = callback
        self.stop_event = threading.Event()

    def stop(self):
        self.stop_event.set()

    def run(self):
        while not self.stop_event.is_set():
            if self.stop_event.wait(self.interval):
                break

            self.callback()
