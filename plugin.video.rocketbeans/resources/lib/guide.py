# -*- coding: utf-8 -*-
import datetime
import json
import time
import urllib.request
import urllib.error
import urllib.parse

from resources.data import config


def show_guide():
    items = []

    request = urllib.request.Request(
        config.GUIDE_URL, headers={'User-Agent': 'Kodi'})

    response = urllib.request.urlopen(request)
    string_data = response.read()

    data = json.loads(string_data)
    schedule = data['schedule']

    cur_date = None
    for item in schedule:
        is_live_now = False
        startTime = datetime.datetime(
            *time.strptime(item['timeStart'][:19], "%Y-%m-%dT%H:%M:%S")[:6])
        endTime = datetime.datetime(
            *time.strptime(item['timeEnd'][:19], "%Y-%m-%dT%H:%M:%S")[:6])
        title = item['title']
        topic = item['topic']
        video_type = item['type']
        video_id = item['youtube']
        duration = item['length']
        game = item['game']

        # create date seperators
        if cur_date is None:
            cur_date = startTime.date()
        elif (startTime.date() - cur_date).days != 0:
            items.append(
                (startTime.strftime('--- %A, %d. %B ---'), '', '', '', ''))
            cur_date = startTime.date()

        if startTime < datetime.datetime.now() < endTime:
            is_live_now = True

        if not video_type:
            type_string = ''
        else:
            type_name = video_type[0].upper() + video_type[1:]
            if video_type == 'live':
                type_string = '[COLOR FFFF0000][' + type_name + '][/COLOR]'
            elif video_type == 'premiere':
                type_string = '[COLOR FF0000FF][' + type_name + '][/COLOR]'
            else:
                type_string = type_name

        if topic:
            items.append(('%s%s: %s %s' % (startTime.strftime(
                '%H:%M '), title, topic, type_string), video_id, duration, game, is_live_now))
        else:
            items.append(('%s%s %s' % (startTime.strftime(
                '%H:%M '), title, type_string), video_id, duration, game, is_live_now))

    return items
