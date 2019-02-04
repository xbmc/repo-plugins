'''
Created on Aug 16, 2018

@author: adamico
'''
import sys
import xbmc

from resources.lib import arlo_stream

if __name__ == '__main__':
    xbmc.log("===> KodiPlugin-ArloStream START <===", xbmc.LOGNOTICE)
    arlo_stream.ArloStream(sys.argv).run()
    xbmc.log("===> KodiPlugin-ArloStream END   <===", xbmc.LOGNOTICE)