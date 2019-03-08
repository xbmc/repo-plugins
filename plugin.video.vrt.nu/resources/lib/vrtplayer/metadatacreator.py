import time

class MetadataCreator:

    def __init__(self):
        self._duration = None
        self._plot = None
        self._plotoutline = None
        self._datetime = None

    @property
    def title(self):
        return self._title

    @title.setter
    def title(self, value):
        self._title = value

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
    def plotoutline(self):
        return self._plotoutline

    @plotoutline.setter
    def plotoutline(self, value):
        self._plotoutline = value.strip()

    @property
    def datetime(self):
        return self._datetime

    @datetime.setter
    def datetime(self, value):
        self._datetime = value
   
    @property
    def datetime_as_short_date(self):
        return time.strftime('%d/%m', self.datetime)

    def get_video_dictionary(self):
        video_dictionary = dict()

        if self.plot is not None:
            video_dictionary['plot'] = self.plot

        if self.plotoutline is not None:
            video_dictionary['plotoutline'] = self.plotoutline

        if self.duration is not None:
            video_dictionary['duration'] = (self.duration * 60) #minutes to seconds

        if self.datetime is not None:
            video_dictionary['date'] = time.strftime('%d.%m.%Y', self.datetime)
            video_dictionary['shortdate'] = self.datetime_as_short_date
            
        return video_dictionary
