# -*- coding: utf-8 -*-
import re

def return_duration_as_seconds(string):
    try:
        totalseconds = 0
        hours = re.findall('(\d+)H',string)
        minutes = re.findall('(\d+)M',string)
        seconds = re.findall('(\d+)S',string)
        if hours:
            totalseconds += 3600*int(hours[0])
        if minutes:
            totalseconds += 60*int(minutes[0])
        if seconds:
            totalseconds += int(seconds[0])
        return str(totalseconds)
    except IndexError:
        return '0'
