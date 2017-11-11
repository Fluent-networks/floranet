from twisted.internet.defer import inlineCallbacks, returnValue

from model import Model
from floranet.appserver.reflector import Reflector
from floranet.lora.bands import LoraBand
from floranet.util import validIPv4Address, validIPv6Address

class Config(Model):
    """NetServer Configuration model
    
    Model representing the netserver configuration.
    
    Attributes:
        name(str): Server name
        listen (str): Interfaces to listen on
        port (int): LoRaWAN port
        webport (int): Web server port
        apitoken (str): REST API authentication token
        freqband (str): Frequency band
        netid (int): Network ID
        duplicateperiod (int): Period (seconds) used to check for duplicate messages
        fcrelaxed (bool): Relaxed frame count mode
        otaastart (int): OTAA range start address
        otaaend (int): OTAA range end address
        macqueuing (bool): Queue downlink MAC commands 
        macqueuelimit (int): Time (seconds) that MAC Commands can remain in the queue
        adrenable (bool): Adapative data rate enable
        adrmargin (int): SNR margin added to the calculation of adaptive data rate steps
        adrcycletime (int): Period (seconds) for ADR control cycle
        adrmessagetime (int): Minimum inter-ADR message time (seconds)
    """
    
    TABLENAME = 'config'
    
    @classmethod
    @inlineCallbacks
    def loadFactoryDefaults(self):
        """Populate NetServer configuration defaults."""
        
        # Server configuration
        c = Config()
        c.defaults()
        
        yield c.save()
        returnValue(c)

    def check(self):
        """Validate the system configuration object.
            
        Returns:
            valid (bool), message(dict): (True, empty) on success,
            (False, error message dict) otherwise.
        """
        messages = {}

        if self.name == '':
            messages['listen'] = 'Invalid name'
            
        if self.listen != '' and not (validIPv4Address(self.listen) or
                validIPv6Address(self.listen)):
            messages['listen'] = 'Invalid IP address'
            
        if self.port < 1 or self.port > 65535:
            messages['port'] = 'Invalid server port'

        if self.webport < 1 or self.webport > 65535:
            messages['webport'] = 'Invalid web port'

        if self.webport < 1 or self.webport > 65535:
            messages['webport'] = 'Invalid web port'
            
        if self.freqband not in LoraBand.BANDS:
            messages['freqband'] = 'Invalid frequency band'
            
        if self.netid < 1 or self.netid > int('0xFFFFFF', 16):
            messages['netid'] = 'Invalid network ID'

        if self.duplicateperiod < 1 or self.duplicateperiod > 60:
            messages['netid'] = 'Invalid duplicate period'
        
        if self.otaastart < 1 or self.otaastart > int('0xFFFFFFFF', 16):
            messages['otaastart'] = 'Invalid OTAA start address'
        elif self.otaaend < 1 or self.otaaend > int('0xFFFFFFFF', 16) \
             or self.otaaend <= self.otaastart:
            messages['otaastart'] = 'Invalid OTAA end address'
        
        if self.macqueuelimit < 60 or self.macqueuelimit > 86400:
            messages['macqueuelimit'] = 'Invalid MAC queueing limit'

        if self.adrmargin < 0.0:
            messages['adrmargin'] = 'Invalid ADR SNR margin'
        
        if self.adrcycletime < 60:
            messages['adrcycletime'] = 'Invalid ADR cycle time'
            
        if self.adrmessagetime < 1:
            messages['adrmessagetime'] = 'Invalid ADR message time'
 
        valid = not any(messages)
        return valid, messages
            
    def defaults(self):
        """Populate server configuration defaults
        
        """
        self.name = 'floranet'
        self.listen = '0.0.0.0'
        self.port = 1700
        self.webport = 8000
        self.apitoken = 'IMxHj@wfNkym@*+V85Rs^G<QXMD~p[eaX3S=_D8f7{z0q{GN'
        self.freqband = 'US915'
        self.netid = int('0x010203', 16)
        self.duplicateperiod = 10
        self.fcrelaxed = True        
        self.otaastart = int('0x06000001', 16)
        self.otaaend = int('0x060FFFFF', 16)
        self.macqueueing = True
        self.macqueuelimit = 120
        self.adrenable = True
        self.adrmargin = 0.0
        self.adrcycletime = 9000
        self.adrmessagetime = 10
    
    def valid(self):
        pass
    
    
    
    
    



