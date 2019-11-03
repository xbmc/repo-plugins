# SPDX-License-Identifier: CC-BY-NC-SA-4.0

import time


class StopWatch(object):
    """ Class for time measurements and performance """
    
    def __init__(self, name, logger):
        """Create an instance of a stopwatch with a certain logger
        
        Arguments:
        name   : string       - ID of the stopwatch.
        logger : Customlogger - Logger to write to.
        
        """
        
        if name is None or name == "" or logger is None:
            raise ValueError("Name or logger not specified")
        
        self.logger = logger
        self.name = name
        
        self.startTime = None
        self.lapTime = None
        self.stopTime = None
        
        self.set()
        return
    
    def stop(self):
        """Stops the stopwatch and prints the time elapsed."""
        
        self.stopTime = time.time()
        seconds_taken = self.stopTime - self.startTime
        
        if self.lapTime:
            delta = self.stopTime - self.lapTime
        else:
            delta = self.stopTime - self.startTime
            
        self.logger.debug("Stopwatch :: Stop (%s): %s, time elapsed: %s ms (+%s ms)",
                          self.name, self.stopTime, seconds_taken * 1000, delta * 1000)
        return
        
    def set(self):
        """Starts the stopwatch and prints the start time."""
        
        self.startTime = time.time()
        self.logger.debug("Stopwatch :: Set (%s): %s", self.name, self.startTime)
        return
        
    def lap(self, value=""):
        """Laps the stopwatch and prints the elapsed time. The stopwatch 
        does not stop.
        
        Keyword Arguments:
        value : string - Label to print with the Lap action.
        
        """
        now = time.time()
        
        if self.lapTime:
            delta = now - self.lapTime
        else:
            delta = now - self.startTime
        
        self.lapTime = now
        seconds_taken = self.lapTime - self.startTime
        self.logger.debug("Stopwatch :: Lap (%s) %s: elapsed since start: %s ms (delta +%s ms)",
                          self.name, value, seconds_taken * 1000, delta * 1000)
           
    def __str__(self):
        """String representation of this class."""
        
        return "Stopwatch: [%s]" % (self.name, )
