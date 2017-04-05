import get_scores
import datetime
import collections

class MlbGamesQueue():
    # The `get` method will be called every `refresh_sec`
    # but we want to return data from `delay_sec` ago.
    def __init__(self, delay_sec, refresh_sec, plugin):
        assert delay_sec % refresh_sec == 0
        assert delay_sec >= refresh_sec

        # _buffer[0] will always contain the element from `delay_sec` ago
        # or the oldest element if not enough elements in the deque yet
        self._buffer = collections.deque(maxlen=(delay_sec / refresh_sec) + 1)
        self._li_csv_path =  plugin.addon.getAddonInfo('path') + "/resources/li.csv"

    def get(self):
        # TODO be weary of timezone issues with datetime.today()
        scores = get_scores.best_games(datetime.datetime.today(), self._li_csv_path)
        self._buffer.append(scores)
        return self._buffer[0]