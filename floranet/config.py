
import os
import ipaddress
import ConfigParser

from application import Application
from log import log

class Option(object):
    """Configuration option
    
    Model for a configuration option of the form
    optionname = optionvalue
    
    Attributes:
        name (str): Name of the option
        type: (str): Option data type
        default: default value
        val: parsed value from configuration file
        len: length - used for hex value length check
    """
    
    def __init__(self, name, type, default=False, val=None, length=0):
        """Initialise a configuration object"""
        self.name = name
        self.type = type
        self.default = default
        self.val = val
        self.len = length

class Configuration(object):
    """FloraNet configuration
    
    Attributes:
        parser (SafeConfigParser): parser object
        cfile (str): configuration file name
        path (str): Path to this module
        app (list): list of configured Application objects
        
    """    
    def __init__(self):
        """Initialise configuration.
        """
        self.parser = ConfigParser.SafeConfigParser()
        self.cfile = None
        self.path = os.path.dirname(os.path.abspath(__file__))
            
        # Applications
        self.apps = []

    def _getOption(self, section, option, obj):
        """Parse options for the section
        
        Args:
            section (str): the section to check
            option (Option): option to parse
            obj: Object to set the attribute of (name) with value
        """
        
        # Check option exists
        if not self.parser.has_option(section, option.name):
            log.error("Could not find option {opt} in {section}",
                           opt=option.name, section=section)
            return False
        
        # Check it can be accessed
        try:
            v = self.parser.get(section, option.name)
        except ConfigParser.Error:
                log.error("Could not parse option {opt} in {section}",
                           opt=option.name, section=section)
                return False
        
        # Set default value if required
        if v == '' and option.default:
            setattr(obj, option.name, option.val)
            return True
        
        # String type. No checks required.
        if option.type == 'str':
            pass

        # Check boolean type
        elif option.type == 'boolean':
            try:
                v = self.parser.getboolean(section, option.name)
            except (ConfigParser.Error, ValueError):
                log.error("Could not parse option {opt} in {section}",
                           opt=option.name, section=section)
                return False
            
        # Check integer type
        elif option.type == 'int':
            try:
                v = int(self.parser.getint(section, option.name))
            except (ConfigParser.Error, ValueError):
                log.error("Could not parse option {opt} in {section}",
                           opt=option.name, section=section)
                return False
            
        # Check address type
        elif option.type == 'address':
            try:
                ipaddress.ip_address(v)
            except (ipaddress.AddressValueError, ValueError):
                log.error("Could not parse option {opt} in {section}: "
                               "invalid address {address}", address=v)
                return False
            
        # Check hex type
        elif option.type == 'hex':
            if len(v) / 2 != option.len + 1:
                log.error("Option {opt} in {section} is incorrect length: "
                               "hex value should be {n} octets",
                               opt=option.name, section=section, n=option.len)
                return False
            try:
                v = int(v, 16)
            except ValueError:
                log.error("Could not parse option {opt} in {section}: " 
                               "invalid hex value {value}", opt=option.name,
                                    section=section, value=v)
                return False
        
        # Check array type
        elif option.type == 'array':
            try:
                v = eval(v)
            except (NameError, SyntaxError, ValueError):
                log.error("Could not parse array {opt} in {section}",
                           opt=option.name, section=section)
                return False
            if not isinstance(v, list):
                log.error("Error parsing array {opt} in {section}",
                           opt=option.name, section=section)
                return False

        setattr(obj, option.name, v)
        return True
    
    
    def _getApplication(self, section, app):
        """Parse an Application in a section"""
        
        app.name = section[12:]
        
        options = [
            Option('appeui', 'hex', default=False, length=8),
            Option('appnonce', 'hex', default=False, length=3),
            Option('appkey', 'hex', default=False, length=16),
            Option('fport', 'int', default=False),
            Option('appserver', 'array', default=False)
            ]
        for option in options:
            if not self._getOption(section, option, app):
                return False
        return True
        
    def parseConfig(self, cfile):
        """Parse a configuration file
        
        Args:
            cfile (str): Configuration file path
        
        Returns:
            Parsed Configuration object on success, False otherwise
        """
        
        self.cfile = cfile
        
        # Check file exists
        if not os.path.exists(self.cfile):
            log.error("Can't find configuration file {cfile}",
                      cfile=self.cfile)
            return False
        elif not os.path.isfile(self.cfile):
            log.error("Can't read configuration file {cfile}",
                      cfile=self.cfile)
            return False
        
        try:
            self.parser.read(self.cfile)
        except ConfigParser.ParsingError:
            log.error("Error parsing configuration file {cfile}",
                      cfile=self.cfile)
            return False
        
        # Get sections
        sections = self.parser.sections()
        
        # Server section
        if 'server' not in sections:
            log.error("Couldn't find server section in configuration")
            return False
        options = [
            Option('listen', 'address', default=True, val=''),
            Option('port', 'int', default=False),
            Option('database', 'array', default=False),
            Option('freqband', 'str', default=False),
            Option('netid', 'hex', default=False, length=3),
            Option('otaastart', 'hex', default=False, length=4),
            Option('otaaend', 'hex', default=False, length=4),
            Option('macqueuing', 'boolean', default=False),
            Option('macqueuelimit', 'int', default=True, val=300),
            Option('adrenable', 'boolean', default=True, val=False),
            Option('adrmargin', 'int', default=True, val=0),
            Option('adrcycletime', 'int', default=True, val=90),
            Option('adrmessagetime', 'int', default=True, val=30),
            Option('duplicateperiod', 'int', default=False),
            Option('fcrelaxed', 'boolean', default=True, val=False),
            Option('gateways', 'array', default=True, val=[]),
            ]
        for option in options:
            if not self._getOption('server', option, self):
                return False
        
        # Application sections
        appsections = filter(lambda s: s.startswith('application.'), sections)
        if not appsections:
            log.error("Couldn't find application section in configuration")
            return False
        for section in appsections:
            app = Application()
            if not self._getApplication(section, app):
                return False
            self.apps.append(app)
            
        return True
        
    