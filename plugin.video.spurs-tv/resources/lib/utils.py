import _strptime
import time
from datetime import datetime, date

def date_from_str(date_str, date_format):
    try:
        return datetime.strptime(date_str, date_format).date()
    except TypeError:
        return date(*(time.strptime(date_str, date_format)[0:3]))
