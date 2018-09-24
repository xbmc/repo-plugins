import time


class MetadataCreator:

    def __init__(self):
        self._duration = None
        self._plot = None
        self._datetime = None

    @property
    def duration(self):
        return self._duration

    @duration.setter
    def duration(self, value):
        self._duration = value

    @property
    def plot(self):
        return self._plot

    @plot.setter
    def plot(self, value):
        self._plot = value.strip()

    @property
    def datetime(self):
        return self._datetime

    @datetime.setter
    def datetime(self, value):
        self._datetime = value

    def get_video_dictionary(self):
        video_dictionary = dict()

        if self.plot is not None:
            video_dictionary['plot'] = self.plot

        if self.duration is not None:
            video_dictionary['duration'] = self.duration

        if self.datetime is not None:
            video_dictionary['date'] = time.strftime('%d.%m.%Y', self.datetime)
            video_dictionary['shortdate'] = time.strftime('%d/%m', self.datetime)

        return video_dictionary
