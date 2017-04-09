import datetime
import json
import time
import urllib2

from resources.data import config


def show_guide():
    items = []

    request = urllib2.Request(config.GUIDE_URL, headers={'User-Agent': 'Kodi'})
    response = urllib2.urlopen(request)
    string_data = response.read()

    data = json.loads(string_data)
    schedule = data['schedule']

    cur_date = None
    for item in schedule:
        startTime = datetime.datetime(
            *time.strptime(item['timeStart'][:19], "%Y-%m-%dT%H:%M:%S")[:6])
        title = item['title']
        type = item['type']

        if cur_date is None:
            cur_date = startTime.date()
        elif (startTime.date() - cur_date).days != 0:
            items.append(startTime.strftime('--- %A, %d. %B ---'))
            cur_date = startTime.date()

        if not type:
            type_string = ''
        else:
            type_name = type[0].upper() + type[1:]
            if type == 'live':
                type_string = '[COLOR FFFF0000][' + type_name + '][/COLOR]'
            elif type == 'premiere':
                type_string = '[COLOR FF0000FF][' + type_name + '][/COLOR]'
            else:
                type_string = type_name

        items.append(startTime.strftime('%H:%M ') + title + ' ' + type_string)

    return items
