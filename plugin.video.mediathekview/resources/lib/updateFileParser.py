# -*- coding: utf-8 -*-
"""
The database updater module

Copyright 2020 codingPF
SPDX-License-Identifier: MIT
"""

# -- Imports ------------------------------------------------
import json
from contextlib import closing
from codecs import open

class UpdateFileParser(object):

    def __init__(self, logger, bufferSize, inputFilename):
        self.logger = logger
        self.bufferSize = bufferSize
        self.filename = inputFilename
        self.buffer = ""
        self.cPosition = 0
        #self.logger.info('UpdateFileParser constructed' )

    def init(self):
        self.filehandle = open(self.filename, 'rb', encoding="utf-8")
        self.buffer = self.filehandle.read(self.bufferSize)
        #self.logger.info('UpdateFileParser init reading ' + str(len(self.buffer)) + ' bytes to buffer' )
    
    def next(self, aWord):
        ##
        if (self.cPosition == -1):
            #self.logger.info("EOF")
            return ""
        index = self.buffer.find(aWord, self.cPosition)
        #print("index " + str(index))
        if (index > -1):
            rtBuffer = self.buffer[self.cPosition:index]
            self.cPosition = (index + len(aWord)) 
            #self.logger.info("Found at " + str(index))
            return rtBuffer
        else:
            nbuffer = self.filehandle.read(self.bufferSize)
            #print("filled new buffer with " + str(len(nbuffer)))
            if (len(nbuffer) == 0):
                rStr = self.buffer[self.cPosition:]
                self.cPosition = -1
                #self.logger.info("no more buffer")
                return rStr
            else:
                self.buffer = self.buffer[self.cPosition:] + nbuffer
                self.cPosition = 0
                #self.logger.info("refill buffer - next iteration")
                return self.next(aWord)        
        return ""
    
    def close(self):
        self.filehandle.close()