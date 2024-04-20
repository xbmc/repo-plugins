import sys
from lib import ha_weather
import xbmcgui

WINDOW = xbmcgui.Window(12600)

if (__name__ == '__main__'):
    ha_weather.MAIN(mode=sys.argv[1],w=WINDOW)
