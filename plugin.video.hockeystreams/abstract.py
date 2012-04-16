import datetime

__author__ = 'longman'

class AbstractHockey(object):
    def __init__(self, util):
        assert type(self) != AbstractHockey, "AbstractHockey must not be instantiated directly"
        today = datetime.date.today()
        self.util = util
        self.today = today
        self.archiveDate = self.get_date(today.day, today.month, today.year)

    def get_date(self, day, month, year, sep = '-'):
        archiveMonth = str(month)
        if len(archiveMonth) == 1:
            archiveMonth = '0' + archiveMonth
        archiveDay = str(day)
        if len(archiveDay) == 1:
            archiveDay = '0' + archiveDay
        archiveDate = sep.join([archiveMonth, archiveDay, str(year)])
        return archiveDate

    def YEAR(self, url, mode):
        self.util.addDir(self.util.__settings__.getLocalizedString(40200), url, 6, '', 1)
        for year in range(self.today.year, 2009, -1):
            if year == self.today.year:
                monthsCount = self.today.month
            else:
                monthsCount = 12
            self.util.addDir(str(year), url, mode, '', monthsCount, year)

    def MONTH(self, url, year, mode):
        if year == self.today.year:
            startmonth = self.today.month
        else:
            startmonth = 12
        for month in range(startmonth, 0, -1):
            patsy = datetime.date(int(year), int(month), 1)
            days_in_month = int(patsy.strftime("%d"))
            if month == patsy.month:
                daysCount = self.today.day
            else:
                daysCount = days_in_month
            self.util.addDir(patsy.strftime("%B"), url, mode, '', daysCount, year, month)

    def DAY(self, url, year, month, mode):
        startday = 31
        if year == self.today.year and month == self.today.month:
            startday = self.today.day

        for day in range(startday, 0, -1):
            try:
                patsy = datetime.date(year, month, day)
                self.util.addDir(patsy.strftime("%x"), url, mode, '', 1, year, month, day)
            except ValueError:
                pass # skip day
