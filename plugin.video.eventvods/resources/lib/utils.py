import re
import requests

def get_page_json(url):
    page_response = requests.get(url)
    return page_response.json()


def time_to_seconds(time_string):
    pattern_time = re.compile("[dhmsDHMS]")
    pattern_units = re.compile("[0-9]+")
    units = re.split(pattern_units, time_string)
    time = re.split(pattern_time, time_string)
    time_dict = dict(list(zip(units[1:], time[:-1])))

    seconds = 0
    for (unit, sec) in list(time_dict.items()):
        if unit.lower() == "d":
            seconds += int(sec)*86400
        elif unit.lower() == "h":
            seconds += int(sec)*3600
        elif unit.lower() == "m":
            seconds += int(sec)*60
        elif unit.lower() == "s":
            seconds += int(sec)

    return seconds


def convert_date_to_kodi_format(date):
    kodi_date = date.split("T")[0]
    kodi_date = ":".join(reversed(kodi_date.split("-")))
    return kodi_date
