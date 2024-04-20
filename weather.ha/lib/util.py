import os
import sys
import socket
import requests
import _strptime
import math
import re
import codecs
import xbmc
import calendar
import time
from datetime import datetime, timedelta
import iso8601

import urllib

import xbmcgui
import xbmcplugin
import xbmcaddon
import xbmcvfs
from xbmc import log as xbmc_log

from math import sqrt

__addon__ = xbmcaddon.Addon()
__addonname__ = __addon__.getAddonInfo('name')
__addonversion__ = __addon__.getAddonInfo('version')
__icon__ = __addon__.getAddonInfo('icon')
__addonid__ = __addon__.getAddonInfo('id')
LANGUAGE = __addon__.getLocalizedString

#WEATHER_WINDOW = xbmcgui.Window(12600)
WEATHER_ICON = xbmcvfs.translatePath('%s.png')
TEMPUNIT   = xbmc.getRegion('tempunit')
DATEFORMAT = xbmc.getRegion('dateshort')
TIMEFORMAT = xbmc.getRegion('meridiem')
SPEEDUNIT = xbmc.getRegion('speedunit')
MAXDAYS = 6

DATEFORMAT = xbmc.getRegion('dateshort')
TIMEFORMAT = xbmc.getRegion('meridiem')

def build_url(base_url, query):
    return base_url + '?' + urllib.urlencode(query)

def show_dialog(message):
    xbmcgui.Dialog().ok(__addonname__, message)


def log(txt, loglevel=xbmc.LOGDEBUG): #https://forum.kodi.tv/showthread.php?tid=196442
    if __addon__.getSetting( "logEnabled" ) == "true":
        message = u'[ HOME ASSISTANT WEATHER ]: %s: %s' % (__addonid__, txt)
        xbmc.log(msg=message, level=loglevel)

def utc_to_local(utc_dt):
    # get integer timestamp to avoid precision lost
    timestamp = calendar.timegm(utc_dt.timetuple())
    local_dt = datetime.fromtimestamp(timestamp)
    assert utc_dt.resolution >= timedelta(microseconds=1)
    return local_dt.replace(microsecond=utc_dt.microsecond)

def parse_date(event_date):
    datetime_obj = iso8601.parse_date(event_date)
    datetime_obj = utc_to_local(datetime_obj)
    dateString = datetime_obj.strftime(xbmc.getRegion('dateshort'))
    return dateString

def parse_time(event_date):
    datetime_obj = iso8601.parse_date(event_date)
    datetime_obj = utc_to_local(datetime_obj)
    timeString = datetime_obj.strftime(xbmc.getRegion('time'))
    return timeString

def parse_dateTime(event_date):
    return parse_date(event_date) + ' ' + parse_time(event_date)

# set weather window property
def set_property(name, value, WINDOW1):
    WINDOW1.setProperty(name, value)

def get_condition_code_by_name(name, is_num=False):
    code_to_name_map = ['tornado',
        'tropical-storm',
        'hurricane',
        'lightning-rainy',
        'lightning',
        'snowy-rainy',
        'mixed-rain-and-sleet',
        'mixed-snow-and-sleet',
        'freezing-drizzle',
        'drizzle',
        'freezing-rain',
        'pouring',
        'rainy',
        'snow-flurries',
        'light-snow-showers',
        'blowing-snow',
        'snowy',
        'hail',
        'sleet',
        'dust',
        'fog',
        'haze',
        'smoky',
        'blustery',
        'windy',
        'cold',
        'cloudy',
        'mostly-cloudy-night',
        'mostly-cloudy-day',
        'partly-cloudy-night',
        'partly-cloudy-day',
        'clear-night',
        'sunny',
        'fair-night',
        'fair-day',
        'mixed-rain-and-hail',
        'hot',
        'isolated-thunderstorms',
        'scattered-thunderstorms',
        'scattered-thunderstorms',
        'scattered-showers',
        'heavy-snow',
        'scattered-snow-showers',
        'heavy-snow',
        'partlycloudy',
        'thundershowers',
        'snow-showers',
        'isolated-thundershowers'
    ]
    try:
        code = code_to_name_map.index(name)
    except ValueError:
        code = -1 if is_num else 'na'
    return str(code)


# Source: https://github.com/xbmc/repo-scripts/blob/krypton/weather.yahoo/default.py
# convert winddirection in degrees to a string (eg. NNW).
# https://raw.githubusercontent.com/xbmc/xbmc/master/addons/resource.language.en_gb/resources/strings.po
def WIND_DIR(deg):
    deg = int(deg)
    if deg >= 349 or deg <=  11:
        return 71
    elif deg >= 12 and deg <= 33:
        return 72
    elif deg >= 34 and deg <=  56:
        return 73
    elif deg >= 57 and deg <=  78:
        return 74
    elif deg >= 79 and deg <=  101:
        return 75
    elif deg >= 102 and deg <=  123:
        return 76
    elif deg >= 124 and deg <=  146:
        return 77
    elif deg >= 147 and deg <=  168:
        return 78
    elif deg >= 169 and deg <=  191:
        return 79
    elif deg >= 192 and deg <=  213:
        return 80
    elif deg >= 214 and deg <=  236:
        return 81
    elif deg >= 237 and deg <=  258:
        return 82
    elif deg >= 259 and deg <=  281:
        return 83
    elif deg >= 282 and deg <=  303:
        return 84
    elif deg >= 304 and deg <=  326:
        return 85
    elif deg >= 327 and deg <=  348:
        return 86
    return 92


# convert month numbers to short names (01 = jan)
MONTH_NAME_SHORT = { '01' : 51,
                     '02' : 52,
                     '03' : 53,
                     '04' : 54,
                     '05' : 55,
                     '06' : 56,
                     '07' : 57,
                     '08' : 58,
                     '09' : 59,
                     '10' : 60,
                     '11' : 61,
                     '12' : 62 }
# convert month numbers to names (01 = januari)
MONTH_NAME_LONG = { '01' : 21,
                    '02' : 22,
                    '03' : 23,
                    '04' : 24,
                    '05' : 25,
                    '06' : 26,
                    '07' : 27,
                    '08' : 28,
                    '09' : 29,
                    '10' : 30,
                    '11' : 31,
                    '12' : 32 }

# convert day numbers to names (0 = sunday)
WEEK_DAY_LONG = { '0' : 17,
                  '1' : 11,
                  '2' : 12,
                  '3' : 13,
                  '4' : 14,
                  '5' : 15,
                  '6' : 16 }

# convert day numbers to short names (0 = sun)
WEEK_DAY_SHORT = { '0' : 47,
                   '1' : 41,
                   '2' : 42,
                   '3' : 43,
                   '4' : 44,
                   '5' : 45,
                   '6' : 46 }

# Source: https://github.com/xbmc/repo-scripts/blob/krypton/weather.yahoo/default.py
# convert timestamp to localized time and date
# stamp (input value): either datetime (2020-02-28T22:00:00.000Z), timestamp (1582871381) or daynumber (1)
# inpt (input format) either 'datetime', 'timestamp', 'seconds' (after midnight) or 'day'
# outpt (return value) time+date, month+day, weekday, time
# form (output format) either long or short names 
def convert_datetime(stamp, inpt, outpt, form):
    if inpt == 'date':
        timestruct = time.strptime(stamp, "%d.%m.%Y")
    elif inpt == 'datetime':
        timestruct = time.strptime(stamp, "%Y-%m-%dT%H:%M:%S%z")
    elif inpt == 'timestamp':
        timestruct = time.localtime(stamp)
    elif inpt == 'seconds':
        m, s = divmod(stamp, 60)
        h, m = divmod(m, 60)
        hm = "%02d:%02d" % (h, m)
        timestruct = time.strptime(hm, "%H:%M")
    if outpt == 'timedate':
        if DATEFORMAT[1] == 'd' or DATEFORMAT[0] == 'D':
            localdate = time.strftime('%d-%m-%Y', timestruct)
        elif DATEFORMAT[1] == 'm' or DATEFORMAT[0] == 'M':
            localdate = time.strftime('%m-%d-%Y', timestruct)
        else:
            localdate = time.strftime('%Y-%m-%d', timestruct)
        if TIMEFORMAT != '/':
            localtime = time.strftime('%I:%M %p', timestruct)
        else:
            localtime = time.strftime('%H:%M', timestruct)
        label = localtime + '  ' + localdate
    elif outpt == 'monthday':
        month = time.strftime('%m', timestruct)
        day = time.strftime('%d', timestruct)
        if form == 'short':
            if DATEFORMAT[1] == 'd' or DATEFORMAT[0] == 'D':
                label = day + ' ' + xbmc.getLocalizedString(MONTH_NAME_SHORT[month])
            else:
                label = xbmc.getLocalizedString(MONTH_NAME_SHORT[month]) + ' ' + day
        elif form == 'long':
            if DATEFORMAT[1] == 'd' or DATEFORMAT[0] == 'D':
                label = day + ' ' + xbmc.getLocalizedString(MONTH_NAME_LONG[month])
            else:
                label = xbmc.getLocalizedString(MONTH_NAME_LONG[month]) + ' ' + day
    elif outpt == 'weekday':
        if inpt == 'day':
            weekday = str(stamp)
        else:
            weekday = time.strftime('%w', timestruct)
        if form == 'short':
            label = xbmc.getLocalizedString(WEEK_DAY_SHORT[weekday])
        elif form == 'long':
            label =  xbmc.getLocalizedString(WEEK_DAY_LONG[weekday])
    elif outpt == 'time':
        if TIMEFORMAT != '/':
            label = time.strftime('%I:%M %p', timestruct)
        else:
            label = time.strftime('%H:%M', timestruct)
    return label

# Source: https://github.com/xbmc/repo-scripts/blob/krypton/weather.yahoo/default.py
# convert temperature in Fahrenheit or Celcius to other formats
# val: temperature
# inf (input format): 'F' (fahrenheit) or 'C' (celcius)
# outf (force output format): 'C' (celcius)
def convert_temp(val, inf, outf=None):
    if (inf == 'F') or (inf == u'°F'):
        #fahrenheit to celcius
        val = (float(val)-32) * 5/9
    else:
        val = float(val)
    if outf == 'C':
        temp = val
    elif outf == 'F':
        temp = val * 9/5 + 32
    elif TEMPUNIT == u'°F':
        temp = val * 1.8 + 32
    elif TEMPUNIT == u'K':
        temp = val + 273.15
    elif TEMPUNIT == u'°Ré':
        temp = val * 0.8
    elif TEMPUNIT == u'°Ra':
        temp = val * 1.8 + 491.67
    elif TEMPUNIT == u'°Rø':
        temp = val * 0.525 + 7.5
    elif TEMPUNIT == u'°D':
        temp = val / -0.667 + 150
    elif TEMPUNIT == u'°N':
        temp = val * 0.33
    else:
        temp = val
    return str(int(round(temp)))

# Source: https://github.com/xbmc/repo-scripts/blob/krypton/weather.yahoo/default.py
# convert speed in mph or mps to other formats
# val: speed
# inf (input format): 'mph' (miles per hour), 'kmh' (kilometers per hour) or 'mps' (metre per seconds)
# outf (force output format): 'kmh' (kilometre per hour)
def convert_speed(val, inf, outf=None):
    if inf == 'mph':
        val = float(val) / 2.237 # converting mph to mps
    elif inf == 'kmh':
        val = float(val) / 3.6 # converting kmh to mps
    else:
        val = float(val)
    # At this point val should be in mps format. Hope so :)
    if outf == 'kmh':
        speed = val * 3.6
    elif SPEEDUNIT == 'km/h':
        speed = val * 3.6
    elif SPEEDUNIT == 'm/min':
        speed = val * 60.0
    elif SPEEDUNIT == 'ft/h':
        speed = val * 11810.88
    elif SPEEDUNIT == 'ft/min':
        speed = val * 196.84
    elif SPEEDUNIT == 'ft/s':
        speed = val * 3.281
    elif SPEEDUNIT == 'mph':
        speed = val * 2.237
    elif SPEEDUNIT == 'knots':
        speed = val * 1.944
    elif SPEEDUNIT == 'Beaufort':
        speed = float(KPHTOBFT(val* 3.6))
    elif SPEEDUNIT == 'inch/s':
        speed = val * 39.37
    elif SPEEDUNIT == 'yard/s':
        speed = val * 1.094
    elif SPEEDUNIT == 'Furlong/Fortnight':
        speed = val * 6012.886
    else:
        speed = val
    return str(int(round(speed)))

# Source: https://github.com/xbmc/repo-scripts/blob/krypton/weather.yahoo/default.py
# convert windspeed in km/h to beaufort
def KPHTOBFT(spd):
    if (spd < 1.0):
        bft = '0'
    elif (spd >= 1.0) and (spd < 5.6):
        bft = '1'
    elif (spd >= 5.6) and (spd < 12.0):
        bft = '2'
    elif (spd >= 12.0) and (spd < 20.0):
        bft = '3'
    elif (spd >= 20.0) and (spd < 29.0):
        bft = '4'
    elif (spd >= 29.0) and (spd < 39.0):
        bft = '5'
    elif (spd >= 39.0) and (spd < 50.0):
        bft = '6'
    elif (spd >= 50.0) and (spd < 62.0):
        bft = '7'
    elif (spd >= 62.0) and (spd < 75.0):
        bft = '8'
    elif (spd >= 75.0) and (spd < 89.0):
        bft = '9'
    elif (spd >= 89.0) and (spd < 103.0):
        bft = '10'
    elif (spd >= 103.0) and (spd < 118.0):
        bft = '11'
    elif (spd >= 118.0):
        bft = '12'
    else:
        bft = ''
    return bft

# Source: https://github.com/xbmc/repo-scripts/blob/krypton/weather.yahoo/default.py
def convert_seconds(sec):
    m, s = divmod(sec, 60)
    h, m = divmod(m, 60)
    hm = "%02d:%02d" % (h, m)
    if TIMEFORMAT != '/':
        timestruct = time.strptime(hm, "%H:%M")
        hm = time.strftime('%I:%M %p', timestruct)
    return hm

# calculate windchill in fahrenheit from temperature in fahrenheit and windspeed in mph
def windchill(temp, speed):
    if temp < 51 and speed > 2:
        windchill = str(int(round(35.74 + 0.6215 * temp - 35.75 * (speed**0.16) + 0.4275 * temp * (speed**0.16))))
    else:
        windchill = temp
    return windchill

# calculate dewpoint celcius from temperature in celcius and humidity
def dewpoint(Tc=0, RH=93, minRH=(0, 0.075)[0]):
    """ Dewpoint from relative humidity and temperature
        If you know the relative humidity and the air temperature,
        and want to calculate the dewpoint, the formulas are as follows.
        
        getDewPoint(tCelsius, humidity)
    """
    Tc = int(Tc)
    RH = int(RH)
    #First, if your air temperature is in degrees Fahrenheit, then you must convert it to degrees Celsius by using the Fahrenheit to Celsius formula.
    # Tc = 5.0 / 9.0 * (Tf - 32.0)
    #The next step is to obtain the saturation vapor pressure(Es) using this formula as before when air temperature is known.
    Es = 6.11 * 10.0**(7.5 * Tc / (237.7 + Tc))
    #The next step is to use the saturation vapor pressure and the relative humidity to compute the actual vapor pressure(E) of the air. This can be done with the following formula.
    #RH=relative humidity of air expressed as a percent. or except minimum(.075) humidity to abort error with math.log.
    RH = RH or minRH #0.075
    E = (RH * Es) / 100
    #Note: math.log() means to take the natural log of the variable in the parentheses
    #Now you are ready to use the following formula to obtain the dewpoint temperature.
    try:
        DewPoint = (-430.22 + 237.7 * math.log(E)) / (-math.log(E) + 19.08)
    except ValueError:
        #math domain error, because RH = 0%
        #return "N/A"
        DewPoint = 0 #minRH
    #Note: Due to the rounding of decimal places, your answer may be slightly different from the above answer, but it should be within two degrees.
    return str(int(round(DewPoint)))

# Source: https://community.openhab.org/t/apparent-temperature/104066/7
# https://www.wpc.ncep.noaa.gov/html/heatindex.shtml
# https://www.weather.gov/ama/heatindex
# https://www.wpc.ncep.noaa.gov/html/heatindex_equation.shtml
def calculateFeelsLike(T, RH):
    # T is expected in formula to be in F. In function - in C.
    T = float(T)
    RH = float(RH)
    T = float(convert_temp(T, 'C', 'F'))
    HI = T
    if (T < 40):
        HI = T
    else:
        HI = -42.379 + 2.04901523*T + 10.14333127*RH - 0.22475541*T*RH - 0.00683783*T*T - 0.05481717*RH*RH + 0.00122874*T*T*RH + 0.00085282*T*RH*RH - 0.00000199*T*T*RH*RH
        if((RH < 13) and (T>=80) and (T<=112)):
            adjust = ((13-RH)/4)  * sqrt(17-abs(T-95)/17)
            HI -= adjust
        elif ((RH>85) and (T>=80) and (T<=87)):
            adjust = ((RH-85)/10) * ((87-T)/5)
            HI += adjust
        elif (T<80):
            HI = 0.5 * (T + 61.0 + ((T-68.0) * 1.2) + (RH * 0.094))
    return float(convert_temp(HI, 'F', None))

def fix_condition_translation_codes(s):
    if s == 'rainy':
        s = 'rain'
    elif s == 'partlycloudy':
        s = 'partly cloudy'
    return s
