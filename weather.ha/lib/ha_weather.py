import os
import sys
import urllib

import xbmcgui
import xbmcplugin
import xbmcaddon
import xbmc
from xbmcvfs import translatePath

import requests
import json
import yaml

import time
from datetime import datetime
import iso8601

from xbmc import log as xbmc_log

from .util import *

from time import sleep
from time import sleep

__addon__ = xbmcaddon.Addon()
__addonname__ = __addon__.getAddonInfo('name')
__addonversion__ = __addon__.getAddonInfo('version')
__icon__ = __addon__.getAddonInfo('icon')
__addonid__ = __addon__.getAddonInfo('id')
__cwd__ = __addon__.getAddonInfo('path')

# get settings...
TEMPUNIT                        = xbmc.getRegion('tempunit')
SPEEDUNIT                       = xbmc.getRegion('speedunit')
MAX_REQUEST_RETRIES             = 6
RETRY_DELAY_S                   = 1
default_temperature_unit        = u'°C'
default_pressure_unit           = 'hPa'
default_wind_speed_unit         = 'm/s'
default_precipitation_unit      = 'mm'

ha_key                          = __addon__.getSettingString('ha_key')
ha_server                       = __addon__.getSettingString('ha_server')
ha_weather_url                  = __addon__.getSettingString('ha_weather_url')
ha_weather_url_method           = __addon__.getSettingString('ha_weather_url_method')
ha_weather_url_data             = __addon__.getSettingString('ha_weather_url_data')
ha_weather_daily_url            = __addon__.getSettingString('ha_weather_daily_url')
ha_weather_daily_url_method     = __addon__.getSettingString('ha_weather_daily_url_method')
ha_weather_daily_url_data       = __addon__.getSettingString('ha_weather_daily_url_data')
ha_weather_hourly_url           = __addon__.getSettingString('ha_weather_hourly_url')
ha_weather_hourly_url_method    = __addon__.getSettingString('ha_weather_hourly_url_method')
ha_weather_hourly_url_data      = __addon__.getSettingString('ha_weather_hourly_url_data')
ha_loc_title                    = __addon__.getSettingString('loc_title')
ha_use_loc_title                = __addon__.getSetting('useHALocName')

# ... and fix them if necessary
if ha_server and ha_server.endswith('/'):
    ha_server = ha_server[:-1]
if ha_weather_url and (not ha_weather_url.startswith('/')):
    ha_weather_url = '/' + ha_weather_url
if ha_weather_daily_url and (not ha_weather_daily_url.startswith('/')):
    ha_weather_daily_url = '/' + ha_weather_daily_url
if ha_weather_hourly_url and (not ha_weather_hourly_url.startswith('/')):
    ha_weather_hourly_url = '/' + ha_weather_hourly_url

headers = {'Authorization': 'Bearer ' + ha_key, 'Content-Type': 'application/json'}

WND = None

class MAIN():
    def __init__(self, *args, **kwargs):
        log('Home Assistant Weather started.')
        #self.MONITOR = MyMonitor()
        mode = kwargs['mode']
        global WND
        WND = kwargs['w']
        self.settings_provided = ha_key and ha_server and ha_weather_url and ha_weather_daily_url and ha_weather_hourly_url
        if not self.settings_provided:
            show_dialog(__addon__.getLocalizedString(30010))
            log('Settings for Home Assistant Weather not yet provided. Plugin will not work.')
            #raise Exception((ha_key, ha_server, ha_weather_url, ha_weather_daily_url, ha_weather_hourly_url))
        else:
            #Test connection / get version
            response = self.getRequest('/config')
            if response is not None:
                log('Response from server: ' + str(response.content))
                self.getForecasts()
                #parsedResponse = json.loads(response.text)
            else:
                log('Response from server is NONE!')
                show_dialog('Response from server is NONE!')
                self.clearProps()
        log('Home Assistant Weather init finished.')

    def getRequest(self, api_ext):
        global headers, ha_server
        retry = 0
        r = None
        while retry < MAX_REQUEST_RETRIES:
            try:
                log('Trying to make a get request to ' + ha_server + api_ext)
                r = requests.get(ha_server + api_ext, headers=headers)
                log('GetRequest status code is: ' + str(r.status_code))
                if r.status_code == 401:
                    show_dialog(__addon__.getLocalizedString(30011)) #Error 401: Check your token
                elif r.status_code == 405:
                    show_dialog(__addon__.getLocalizedString(30012)) #Error 405: Method not allowed
                elif r.status_code == 200:
                    return r
            except:
                log('Status code error is: ' + str(r.raise_for_status() if r else 'unknown' ))
            retry += 1
            sleep(RETRY_DELAY_S)
        show_dialog(__addon__.getLocalizedString(30013)) #Unknown error: Check IP address or if server is online

    def postRequest(self, api_ext, payload):
        global headers, ha_server
        retry = 0
        r = None
        while retry < MAX_REQUEST_RETRIES:
            try:
                log('Trying to make a post request to ' + ha_server + api_ext + ' with payload: ' + payload)
                r = requests.post(ha_server + api_ext, headers=headers, data=payload)
                log('GetRequest status code is: ' + str(r.status_code))
                if r.status_code == 401:
                    show_dialog(__addon__.getLocalizedString(30011)) #Error 401: Check your token
                elif r.status_code == 405:
                    show_dialog(__addon__.getLocalizedString(30012)) #Error 405: Method not allowed
                else:
                    return r
            except:
                log('Status code error is: ' + str(r.raise_for_status() if r else 'unknown' ))
            retry += 1
            sleep(RETRY_DELAY_S)
        show_dialog(__addon__.getLocalizedString(30013)) #Unknown error: Check IP address or if server is online

    def getForecasts(self):
        global ha_weather_url, ha_weather_daily_url, ha_server, ha_key
        log('Getting forecasts from Home Assistant server.')
        temperature_unit = default_temperature_unit
        pressure_unit = default_pressure_unit
        wind_speed_unit = default_wind_speed_unit
        precipitation_unit = default_precipitation_unit
        # Current weather
        response = self.getRequest(ha_weather_url)
        if response is not None:
            log('Response (weather) from server: ' + str(response.content))
            try:
                parsedResponse = json.loads(response.text)
            except json.decoder.JSONDecodeError:
                show_dialog(__addon__.getLocalizedString(30014))
                self.clearProps()
                raise Exception('Got incorrect response from Home Assistant Weather server (request was to ' + ha_weather_url + ' with data: ' + ha_weather_url_data + ') and response received: ' + response.text)
            if parsedResponse.get('attributes') is not None:
                forecast = parsedResponse['attributes']
                # HA format
                temperature_unit        = forecast['temperature_unit']
                pressure_unit           = forecast['pressure_unit']
                wind_speed_unit         = forecast['wind_speed_unit']
                precipitation_unit      = forecast['precipitation_unit']
                loc_friendly_name       = forecast['friendly_name']
                forecast_description    = forecast['attribution']
                loc = ha_loc_title
                if ha_use_loc_title == "true":
                    loc = loc_friendly_name
                if not 'state' in parsedResponse:
                    parsedResponse['state'] = 'n/a'
                if not 'last_updated' in parsedResponse:
                    parsedResponse['last_updated'] = 'n/a'
                if not 'temperature' in forecast:
                    forecast['temperature'] = 0
                if not 'wind_speed' in forecast:
                    forecast['wind_speed'] = 0
                if not 'wind_bearing' in forecast:
                    forecast['wind_bearing'] = 0
                if not 'humidity' in forecast:
                    forecast['humidity'] = 0
                if not 'dew_point' in forecast:
                    forecast['dew_point'] = 0
                if not 'pressure' in forecast:
                    forecast['pressure'] = 0
                set_property('Location1'             , loc, WND)
                set_property('Locations'             , '1', WND)
                set_property('ForecastLocation'      , loc, WND)
                set_property('RegionalLocation'      , loc, WND)
                set_property('Updated'               , parsedResponse['last_updated'], WND)
                set_property('Current.Location'      , loc, WND)
                set_property('Current.Condition'     , str(fix_condition_translation_codes(parsedResponse['state'])), WND)
                set_property('Current.Temperature'   , str(convert_temp(forecast['temperature'], temperature_unit,'C')), WND)
                set_property('Current.UVIndex'       , '0', WND)
                set_property('Current.OutlookIcon'   , '%s.png' % get_condition_code_by_name(parsedResponse['state']), WND)
                set_property('Current.FanartCode'    , get_condition_code_by_name(parsedResponse['state']), WND)
                set_property('Current.Wind'          , str(convert_speed(forecast['wind_speed'], wind_speed_unit, 'kmh')), WND)
                set_property('Current.WindDirection' , xbmc.getLocalizedString(WIND_DIR(forecast['wind_bearing'])), WND)
                set_property('Current.Humidity'      , str(forecast['humidity']), WND)
                set_property('Current.DewPoint'      , str(convert_temp(forecast['dew_point'], temperature_unit,'C')), WND)
                set_property('Current.FeelsLike'     , str(calculateFeelsLike(convert_temp(forecast['temperature'], temperature_unit,'C'),forecast['humidity'])), WND)
                set_property('Current.WindChill'     , convert_temp(windchill(int(convert_temp(forecast['temperature'], temperature_unit,'F')), int(convert_speed(forecast['wind_speed'], wind_speed_unit, 'mph'))), 'F') + TEMPUNIT, WND)
                set_property('Current.Pressure'      , str(forecast['pressure']), WND)
                set_property('Current.IsFetched'     , 'true', WND)
                set_property('Forecast.City'         , loc, WND)
                set_property('Forecast.Country'      , loc, WND)
                set_property('Forecast.Latitude'     , '0', WND)
                set_property('Forecast.Longitude'    , '0', WND)
                set_property('Forecast.IsFetched'    , 'true', WND)
                set_property('Forecast.Updated'      , parsedResponse['last_updated'], WND)
                set_property('WeatherProvider'       , 'Home Assistant Weather', WND)
                set_property('WeatherProviderLogo'   , translatePath(os.path.join(__cwd__, 'resources', 'banner.png')), WND)
            else:
                log('The response dict from get_forecast url does not contain forecast key. This is unexpected.')
                show_dialog(__addon__.getLocalizedString(30014))
                self.clearProps()
                return
        else:
            log('Response (weather current) from server is NONE!')
            show_dialog('Response (weather current) from server is NONE!')
            self.clearProps()
            return
        # Daily
        response = self.getRequest(ha_weather_daily_url)
        if response is not None:
            log('Response (weather hourly) from server: ' + str(response.content))
            try:
                parsedResponse = json.loads(response.text)
            except json.decoder.JSONDecodeError:
                show_dialog(__addon__.getLocalizedString(30014))
                self.clearProps()
                raise Exception('Got incorrect response from Home Assistant Weather server (request was to ' + ha_weather_daily_url + ' with data: ' + ha_weather_hourly_url_data + ') and response received: ' + response.text)
            if parsedResponse.get('attributes') is not None:
                forecast = parsedResponse['attributes']
                for i in range (0, forecast['days_num']):
                    count = str(i)
                    set_property('Day'+count+'.Title'                   , convert_datetime(forecast['day'+count+'_date'],'datetime','weekday','long'), WND)
                    set_property('Day'+count+'.FanartCode'              , get_condition_code_by_name(forecast['day'+count+'_condition']), WND)
                    set_property('Day'+count+'.Outlook'                 , str(fix_condition_translation_codes(forecast['day'+count+'_condition'])), WND)
                    set_property('Day'+count+'.OutlookIcon'             , '%s.png' % str(get_condition_code_by_name(forecast['day'+count+'_condition'])), WND)
                    set_property('Day'+count+'.HighTemp'                , str(convert_temp(forecast['day'+count+'_temperature'],     temperature_unit,'C')), WND)
                    set_property('Day'+count+'.LowTemp'                 , str(convert_temp(forecast['day'+count+'_temperature_low'], temperature_unit,'C')), WND)
                    set_property('Daily.'+str(i+1)+'.ShortDay'          , convert_datetime(forecast['day'+count+'_date'], 'datetime', 'weekday',  'short'), WND)
                    set_property('Daily.'+str(i+1)+'.LongDay'           , convert_datetime(forecast['day'+count+'_date'], 'datetime', 'weekday',  'long'),  WND)
                    set_property('Daily.'+str(i+1)+'.ShortDate'         , convert_datetime(forecast['day'+count+'_date'], 'datetime', 'monthday', 'short'), WND)
                    set_property('Daily.'+str(i+1)+'.LongDate'          , convert_datetime(forecast['day'+count+'_date'], 'datetime', 'monthday', 'long'),  WND)
                    set_property('Daily.'+str(i+1)+'.HighTemperature'   , str(forecast['day'+count+'_temperature'])+TEMPUNIT, WND)
                    set_property('Daily.'+str(i+1)+'.LowTemperature'    , str(forecast['day'+count+'_temperature_low'])+TEMPUNIT, WND)
                    set_property('Daily.'+str(i+1)+'.Humidity'          , str(forecast['day'+count+'_humidity'])+'%', WND)
                    set_property('Daily.'+str(i+1)+'.Precipitation'     , str(forecast['day'+count+'_precipitation'])+precipitation_unit, WND)
                    set_property('Daily.'+str(i+1)+'.WindDirection'     , str(xbmc.getLocalizedString(WIND_DIR(forecast['day'+count+'_wind_bearing']))), WND)
                    set_property('Daily.'+str(i+1)+'.WindSpeed'         , str(forecast['day'+count+'_wind_speed']) + SPEEDUNIT, WND)
                    set_property('Daily.'+str(i+1)+'.WindDegree'        , str(forecast['day'+count+'_wind_bearing']) + u'°', WND)
                    set_property('Daily.'+str(i+1)+'.DewPoint'          , convert_temp(dewpoint(int(convert_temp(forecast['day'+count+'_temperature'], temperature_unit,'C')), int(forecast['day'+count+'_humidity'])), 'C',None), WND)
                    set_property('Daily.'+str(i+1)+'.Outlook'           , str(fix_condition_translation_codes(forecast['day'+count+'_condition'])), WND)
                    set_property('Daily.'+str(i+1)+'.OutlookIcon'       , '%s.png' % str(get_condition_code_by_name(forecast['day'+count+'_condition'])), WND)
                    set_property('Daily.'+str(i+1)+'.FanartCode'        , get_condition_code_by_name(forecast['day'+count+'_condition']), WND)
                set_property('Daily.IsFetched', 'true', WND)
            else:
                log('The response dict from get_forecast url does not contain forecast key. This is unexpected.')
                show_dialog(__addon__.getLocalizedString(30014))
                self.clearProps()
                return
        else:
            log('Response (weather daily) from server is NONE!')
            show_dialog('Response (weather daily) from server is NONE')
            self.clearProps()
            return
        # Hourly weather
        response = self.getRequest(ha_weather_hourly_url)
        if response is not None:
            log('Response (weather daily) from server: ' + str(response.content))
            try:
                parsedResponse = json.loads(response.text)
            except json.decoder.JSONDecodeError:
                show_dialog(__addon__.getLocalizedString(30014))
                self.clearProps()
                raise Exception('Got incorrect response from Home Assistant Weather server (request was to ' + ha_weather_daily_url + ' with data: ' + ha_weather_daily_url_data + ') and response received: ' + response.text)
            if parsedResponse.get('attributes') is not None:
                forecast = parsedResponse['attributes']
                for i in range (0, forecast['hours_num']):
                    count = str(i)
                    set_property('Hourly.'+str(i+1)+'.Time', convert_datetime(forecast['hour'+count+'_date'], 'datetime', 'time', None), WND)
                    set_property('Hourly.'+str(i+1)+'.ShortDate', convert_datetime(forecast['hour'+count+'_date'], 'datetime', 'monthday', 'short'), WND)
                    set_property('Hourly.'+str(i+1)+'.LongDate', convert_datetime(forecast['hour'+count+'_date'], 'datetime', 'monthday', 'long'), WND)
                    set_property('Hourly.'+str(i+1)+'.Temperature' , str(forecast['hour'+count+'_temperature'])+TEMPUNIT, WND)
                    set_property('Hourly.'+str(i+1)+'.Humidity', str(forecast['hour'+count+'_humidity'])+'%', WND)
                    set_property('Hourly.'+str(i+1)+'.Precipitation', str(forecast['hour'+count+'_precipitation'])+precipitation_unit, WND)
                    set_property('Hourly.'+str(i+1)+'.WindDirection', str(xbmc.getLocalizedString(WIND_DIR(forecast['hour'+count+'_wind_bearing']))), WND)
                    set_property('Hourly.'+str(i+1)+'.WindSpeed', str(forecast['hour'+count+'_wind_speed']) + SPEEDUNIT, WND)
                    set_property('Hourly.'+str(i+1)+'.WindDegree', str(forecast['hour'+count+'_wind_bearing']) + u'°', WND)
                    set_property('Hourly.'+str(i+1)+'.DewPoint', convert_temp(dewpoint(convert_temp(forecast['hour'+count+'_temperature'], temperature_unit,'C'),forecast['hour'+count+'_humidity']),'C',None), WND)
                    set_property('Hourly.'+str(i+1)+'.Outlook', str(fix_condition_translation_codes(forecast['hour'+count+'_condition'])), WND)
                    set_property('Hourly.'+str(i+1)+'.OutlookIcon', '%s.png' % str(get_condition_code_by_name(forecast['hour'+count+'_condition'])), WND)
                    set_property('Hourly.'+str(i+1)+'.FanartCode', get_condition_code_by_name(forecast['hour'+count+'_condition']), WND)
                set_property('Hourly.IsFetched', 'true', WND)
            else:
                log('The response dict from get_forecast url does not contain forecast key. This is unexpected.')
                show_dialog(__addon__.getLocalizedString(30014))
                self.clearProps()
                return
        else:
            log('Response (weather daily) from server is NONE!')
            show_dialog('Response (weather daily) from server is NONE')
            self.clearProps()
            return

    def clearProps(self):
        set_property('Current.Condition'     , 'N/A', WND)
        set_property('Current.Temperature'   , '0', WND)
        set_property('Current.Wind'          , '0', WND)
        set_property('Current.WindDirection' , 'N/A', WND)
        set_property('Current.Humidity'      , '0', WND)
        set_property('Current.FeelsLike'     , '0', WND)
        set_property('Current.UVIndex'       , '0', WND)
        set_property('Current.DewPoint'      , '0', WND)
        set_property('Current.OutlookIcon'   , 'na.png', WND)
        set_property('Current.FanartCode'    , 'na', WND)
        for count in range (0, MAXDAYS):
            set_property('Day%i.Title'       % count, 'N/A', WND)
            set_property('Day%i.HighTemp'    % count, '0', WND)
            set_property('Day%i.LowTemp'     % count, '0', WND)
            set_property('Day%i.Outlook'     % count, 'N/A', WND)
            set_property('Day%i.OutlookIcon' % count, 'na.png', WND)
            set_property('Day%i.FanartCode'  % count, 'na', WND)


class MyMonitor(xbmc.Monitor):
    def __init__(self, *args, **kwargs):
        xbmc.Monitor.__init__(self)
