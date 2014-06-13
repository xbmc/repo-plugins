import datetime

def sortedDictKeys(adict):
    keys = adict.keys()
    keys.sort()
    return keys

def daterange(start_date, end_date):
    for n in range((end_date - start_date).days + 1):
        yield start_date + datetime.timedelta(n)
