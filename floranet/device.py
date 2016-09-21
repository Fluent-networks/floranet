
class Device(object):
    """LoRa device class
    
    Model representing a LoRa device.
    
    Attributes:
        devaddr (int): 32 bit end device address (DevAddr)
        deveui (int): Global end-device ID (IEEE EUI64)
        nwkskey (int): 128 bit network session key (NwkSKey)
        appskey (int): 128 bit application session key (AppSKey)
        rx (dict): RX1 and RX2 window parameters
        remote (tuple): Remote gateway (host, port) tuple
        gateway (Gateway): The gateway to this device
        fcntup (int): Uplink frame  counter received from the device
        fctndown (int): Downlink frame counter sent to to the device
    """
    
    def __init__(self, devaddr=None, deveui=None, appeui=None, nwkskey=None,
                 appskey=None, rx=None, remote=None, gateway=None, fcntup=0,
                 fcntdown=0):
        """Initialize a Device object."""
        self.devaddr = devaddr
        self.deveui = deveui
        self.appeui = appeui
        self.nwkskey = nwkskey
        self.appskey = appskey
        self.rx = rx
        self.remote = remote
        self.gateway = gateway
        self.fcntup = fcntup
        self.fcntdown = fcntdown
    
    def checkFrameCount(self, fcntup, maxfcntgap):
        """Sync fcntup counter with received value
        
        The value received must have incremented compared to current
        counter value and must be less than the gap value specified
        by MAX_FCNT_GAP after considering rollovers. Otherwise,
        too many frames have been lost.
        
        Args:
            fcntup (int): Received fcntup value
            maxfcntgap (int): MAX_FCNT_GAP, band specific
            
        Returns:
            True if fcntup is within the limit, otherwise False.
        
        """
        if fcntup > (self.fcntup + maxfcntgap):
            return False
        elif fcntup < self.fcntup and (65535 - self.fcntup + fcntup) > maxfcntgap:
            return False
        else:
            self.fcntup = fcntup
            return True

    def incFrameCountDown(self):
        self.fcntdown += 1
    