'''
Created on Aug 16, 2018

@author: adamico
'''
import sys

from resources.lib import arlo_stream

if __name__ == '__main__':
    arlo_stream.ArloStream(sys.argv).run()
