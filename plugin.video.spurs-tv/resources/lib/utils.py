import _strptime
import time
from datetime import date

def date_from_str(date_str, date_format):
    return date(*(time.strptime(date_str, date_format)[0:3]))

def add_item_info(item, title, item_date):
    item['info'] = {'title': title,
                    'date': item_date.strftime("%d.%m.%Y")}
