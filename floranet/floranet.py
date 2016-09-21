#!/usr/bin/env python

import argparse

from netserver import NetServer
from config import Configuration
from log import log

def parseCommandLine():
    """Parse command line arguments"""
    
    parser = argparse.ArgumentParser(description='FloraNet network server.')
    parser.add_argument('-f', dest='foreground', action='store_true',
                        help='run in foreground, log to console')
    parser.add_argument('-c', dest='config', action='store',
                        default='default.cfg', metavar='config',
                        help='configuration file (default: default.cfg)')
    parser.add_argument('-l', dest='logfile', action='store',
                        default='/tmp/floranet.log', metavar='logfile',
                        help='log file (default: /tmp/floranet.log)')
    return parser.parse_args()

def main():
    # Parse command line arguments
    args = parseCommandLine()
    
    # Start logging
    log.start(args.foreground, args.logfile)
    log.info("Starting up")
    
    # Read server configuration from config file
    config = Configuration()
    log.info("Reading configuration from {config}", config=args.config)
    if not config.parseConfig(args.config):
        log.error("Exiting")
        exit(1)

    # Create and start the netserver
    server = NetServer(config)
    server.start()

if __name__ == '__main__':
    raise SystemExit(main())





