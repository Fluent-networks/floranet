import datetime
import pytz
from floranet.util import devaddrString

from twisted.internet.defer import inlineCallbacks, returnValue

from model import Model

class Device(Model):
    """LoRa device class model.
        
    Attributes:
        name (str): Device name
        devclass (str): Device class
        devaddr (int): 32 bit end device address (DevAddr)
        deveui (int): Global end-device ID (IEEE EUI64)
        otaa (bool): Over the air activated flag
        appeui (int): Application unique identifer (AppEUI)
        nwkskey (int): 128 bit network session key (NwkSKey)
        appskey (int): 128 bit application session key (AppSKey)
        tx_chan (int): Transmit channel number
        tx_datr (str): Transmit data rate
        adr (bool): Device ADR control
        adr_datr (str): Target ADR data rate
        gw_addr (str): The gateway IP address
        fcntup (int): Uplink frame  counter received from the device
        fcntdown (int): Downlink frame counter sent to to the device
        fcnterror (bool): Frame count error flag
        snr_average (float): Calculated ADR average SNR
        snr (list): SNR readings array
        devnonce (list): Devnonce values from join requests
        created (str): Timestamp when the device object is created
        updated (str): Timestamp when the device object is updated
    """
    
    TABLENAME = 'devices'
    
    @inlineCallbacks
    def valid(self, server):
        """Validate a device object.
        
        Args:
            server (NetServer): Network server object
            
        Returns:
            valid (bool), message(dict): (True, empty) on success,
            (False, error message dict) otherwise.
        """
        messages = {}
        
        # Check we have a valid class
        if not self.devclass in {'a', 'c'}:
            messages['class'] = "Invalid device class"
        
        # For ABP device, check for unique devaddr and keys, and devaddr
        # validity
        if not self.otaa:
            check = {'devaddr': self.devaddr, 'nwkskey': self.nwkskey,
                     'appskey': self.appskey}
            for attr,v in check.items():
                exists = yield Device.exists(where=[attr + ' = ? AND deveui != ?',
                                                    v, self.deveui])
                if exists:
                    messages[attr] = "Device {} {} ".format(attr, v) + \
                                     "currently exists. Must be unique."

            # Check devaddr is correctly defined within the network range
            if not 'devaddr' in messages:
                if not server.checkDevaddr(self.devaddr):
                    messages['devaddr'] = "Device devaddr " + \
                            "{} ".format(devaddrString(self.devaddr)) + \
                            "is not within the configured network address range"

            # Check devaddr is not within the OTAA range
            if not 'devaddr' in messages:
                if self.devaddr >= server.config.otaastart and \
                 self.devaddr <= server.config.otaaend:
                    messages['devaddr'] = "Device devaddr " \
                            "{} ".format(devaddrString(self.devaddr)) + \
                             "is within configured OTAA address range"

        valid = not any(messages)
        returnValue((valid, messages))
    
    def isClassA(self):
        """Check if device is class A"""
        return self.devclass == 'a'
    
    def isClassB(self):
        """Check if device is class B"""
        return self.devclass == 'b'

    def isClassC(self):
        """Check if device is class C"""
        return self.devclass == 'c'
    
    def checkDevNonce(self, message):
        """Check the devnonce is not being repeated
        
        Args:
            message (JoinRequestMessage): Join request message
            
        Returns True if message is valid, otherwise False
        """
        if self.devnonce is None:
            self.devnonce = []
        
        # If the  devnonce has been seen previously, return False
        if message.devnonce in self.devnonce:
            return False
        # If we have exceeded the history length, pop the oldest devnonce
        if len(self.devnonce) >= 20:
            self.devnonce.pop(0)
        self.devnonce.append(message.devnonce)
        return True
            
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
        # Relxed mode. If fcntup <=1 then set fcntdown to zero
        # and the device fcntup to match.
        if relaxed and fcntup <= 1:
            self.fcntdown = 0
            self.fcntup = fcntup
            self.fcnterror = False
        elif fcntup > (self.fcntup + maxfcntgap):
            self.fcnterror = True
        elif fcntup < self.fcntup and (65535 - self.fcntup + fcntup) > maxfcntgap:
            self.fcnterror = True
        else:
            self.fcntup = fcntup
            self.fcnterror = False
        
        return not self.fcnterror

    def updateSNR(self, lsnr):
        """Update Device SNR measures
        
        Updates the most recent received device SNR measure.
        We keep 11 samples for each device, and use the
        snr_pointer attribute to maintain the current sample
        index.
        
        Args:
            lsnr (float): Latest link SNR measure.
        
        """
        # Check we have a SNR measure
        if lsnr is None:
            return
        
        # Check if this is the first SNR reading
        if self.snr is None:
            self.snr = []
            
        # Update the current SNR reading
        if len(self.snr) == 11:
            self.snr.pop(0)
        self.snr.append(lsnr)
        
        # Update the average SNR, ensure we have at least 6 readings
        if len(self.snr) >= 6:
            self.snr_average = sum(self.snr[-6:])/6.0

    def getADRDatarate(self, band, margin):
        """Determine the optimal datarate that will achieve the
        objective margin in the given band.
        
        We assume each increase in datarate step (e.g. DR0 to DR1) requires
        an additional 3dB in SNR.
        
        Args:
            band (Band): Band in use
            margin (float): Target margin in dB
        
        Returns:
            Optimal datarate as a string on success, otherwise None.
        """
        if not hasattr(self, 'snr_average') or self.snr_average is None:
            return None
        
        # Target thresholds that the average must exceed. Note range(0,4)
        # refers to the first four (upstream) indices of the band.datarate
        # list. These are DR0, DR1, DR2, DR3
        thresholds = [float(i) * 3.0 + margin for i in range(0,4)]

        # If we have an average SNR less than the lowest threshold,
        # return the lowest DR
        if self.snr_average < thresholds[0]:
            return band.datarate[0]
        
        # Find the index of lowest threshold that the SNR average just exceeds
        i = [n for n,v in enumerate(thresholds) if self.snr_average >= v][-1]
        return band.datarate[i]
