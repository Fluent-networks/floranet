from twistar.dbobject import DBObject

class Device(DBObject):
    """LoRa device class
    
    Model representing a LoRa device.
    
    Attributes:
        devaddr (int): 32 bit end device address (DevAddr)
        deveui (int): Global end-device ID (IEEE EUI64)
        nwkskey (int): 128 bit network session key (NwkSKey)
        appskey (int): 128 bit application session key (AppSKey)
        tx_chan (int): Transmit channel number
        tx_datr (str): Transmit data rate
        gw_addr (str): The gateway IP address
        fcntup (int): Uplink frame  counter received from the device
        fcntdown (int): Downlink frame counter sent to to the device
    """
    
    TABLENAME = 'devices'
        
    def checkFrameCount(self, fcntup, maxfcntgap, relaxed):
        """Sync fcntup counter with received value
        
        The value received must have incremented compared to current
        counter value and must be less than the gap value specified
        by MAX_FCNT_GAP after considering rollovers. Otherwise,
        too many frames have been lost.
        
        Args:
            fcntup (int): Received fcntup value
            maxfcntgap (int): MAX_FCNT_GAP, band specific
            relaxed (bool): frame count relaxed flag
            
        Returns:
            True if fcntup is within the limit, otherwise False.
        
        """
        # Relxed mode. If fcntup = 1 then set fcntdown to zero
        # and the device fntup to 1.
        if relaxed and fcntup == 1:
            self.fcntdown = 0
            self.fcntup = 1
            return True
        if fcntup > (self.fcntup + maxfcntgap):
            return False
        elif fcntup < self.fcntup and (65535 - self.fcntup + fcntup) > maxfcntgap:
            return False
        else:
            self.fcntup = fcntup
            return True

    