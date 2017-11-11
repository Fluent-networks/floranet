import struct

from twisted.internet.defer import inlineCallbacks, returnValue

from floranet.models.model import Model

class AppProperty(Model):
    """LoRa application property class
    
    Model representing a application data properties. A data property
    maps the LoRa fport frame payload parameter to a data name, type,
    and length.
    
    Attributes:
        application_id (int): application foreign key
        port (int): application port
        name (str): mapped name for the property
        type (str): the data type
    """
    
    TABLENAME = 'app_properties'
    TYPES = {'char': 'c',
             'signed char': 'b',
             'unsigned char': 'B',
             'bool': '?',
             'short': 'h',
             'unsigned short': 'H',
             'int': 'i',
             'unsigned int': 'H',
             'long': 'l',
             'unsigned long': 'L',
             'long long': 'q',
             'unsigned long long': 'Q',
             'float': 'f',
             'double': 'd',
             'char[]': 's'
             }
    
    @inlineCallbacks
    def valid(self):
        """Validate an application property.
            
        Returns:
            valid (bool), message(dict): (True, empty) on success,
            (False, error message dict) otherwise.
        """
        messages = {}
        
        if self.port < 1 or self.port > 223:
            messages['port'] = "Invalid port number"
            
        if self.type not in self.TYPES:
            messages['type'] = "Unknown data type"
            
        valid = not any(messages)
        returnValue((valid, messages))
        yield

    def value(self, data):
        """Return the value defined by the property from the
        application data
        
        Args:
            data (str): application data
        """
        
        fmt = self.TYPES[self.type]
        try:
            return struct.unpack(fmt, data)[0]
        except struct.error:
            return None
