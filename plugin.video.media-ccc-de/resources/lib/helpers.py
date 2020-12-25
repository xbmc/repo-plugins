# coding: utf-8
from __future__ import print_function, division, absolute_import


def user_preference_sorter(prefer_quality, prefer_format, prefer_dash=False):
    def do_sort(obj):
        prio = 0

        if obj.type == 'dash':
            prio += 50 if prefer_dash else -50

        if obj.format == prefer_format:
            prio += 20

        # Bonus & penalty for exact matches, no score for "obj.hd == None"
        if obj.hd is True and prefer_quality == "hd":
            prio += 20
        elif obj.hd is False and prefer_quality == "sd":
            prio += 20
        elif obj.hd is True and prefer_quality == "sd":
            prio -= 10
        elif obj.hd is False and prefer_quality == "hd":
            prio -= 10

        # Prefer versions with "more" audio tracks
        try:
            translations = len(obj.languages) - 1
            prio += translations
        except AttributeError:
            pass

        # Prefer "native" over "translated" for now (streaming)...
        try:
            if obj.translated:
                prio -= 5
        except AttributeError:
            pass

        return -prio
    return do_sort


def maybe_json(json, attr, default):
    try:
        return json[attr]
    except KeyError:
        return default


def json_date_to_info(json, field, info):
    if field not in json or not json[field] or len(json[field]) < 10:
        return

    try:
        y, m, d = [int(x) for x in json[field][0:10].split('-')]
        info['date'] = "%02d.%02d.%04d" % (d, m, y)
        info['year'] = y
        info['aired'] = "%04d-%02d-%02d" % (y, m, d)
        info['dateadded'] = "%04d-%02d-%02d" % (y, m, d)
    except ValueError:
        return


def calc_aspect(s):
    try:
        aspect = [float(x) for x in s.split(':')]
        if len(aspect) == 2:
            return aspect[0] / aspect[1]
    except ValueError:
        return None
