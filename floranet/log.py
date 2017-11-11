
import os
import sys

from twisted.logger import (Logger, LogLevel, LogLevelFilterPredicate,
                            FilteringLogObserver,
                            textFileLogObserver,
                            globalLogBeginner)

predicate = None

class Log(Logger):
    """Log class
    
    Netserver logging - subclass of twisted.logger.Logger
    """
    
    def __init__(self):
        """Initialize a Log object."""
        super(Log, self).__init__('Floranet')

    def start(self, console, logfile, debug):
        """Configure and start logging based on user preferences
        
        Args:
            console (bool): Console logging enabled
            logfile (str): Logfile path
            debug (bool): Debugging flag
        """
        global predicate
        
        # Set logging level
        level = LogLevel.debug if debug else LogLevel.info
        predicate = LogLevelFilterPredicate(defaultLogLevel=level)
        
        # Log to console option
        if console:
            f = sys.stdout
        
        # Log to file option
        else:
            # Check the file is valid and can be opened in append mode
            if os.path.exists(logfile) and not os.path.isfile(logfile):
                print "Logfile %s is not a valid file. Exiting." % logfile
                return False
            try:
                f = open(logfile, 'a')
            except IOError:
                print "Can't open logfile %s. Exiting." % logfile
                return False
        
        # Set the observer
        observer = textFileLogObserver(f)
        observers = [FilteringLogObserver(observer=observer,
                                          predicates=[predicate])]
        # Begin logging
        globalLogBeginner.beginLoggingTo(observers)
        return True

log = Log()
