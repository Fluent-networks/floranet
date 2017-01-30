from twistar.dbobject import DBObject
import datetime
import pytz

from twisted.internet.defer import inlineCallbacks

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
        adr_datr (str): Target ADR data rate
        gw_addr (str): The gateway IP address
        fcntup (int): Uplink frame  counter received from the device
        fcntdown (int): Downlink frame counter sent to to the device
        fcnterror (bool): Frame count error flag
        snr_pointer (int): Pointer to the next ADR measure
        snr_average (float): Calculated ADR average SNR
        snr1 (float): SNR reading 1
        snr2 (float): SNR reading 2
        snr3 (float): SNR reading 3
        snr4 (float): SNR reading 4
        snr5 (float): SNR reading 5
        snr6 (float): SNR reading 6
        snr7 (float): SNR reading 7
        snr8 (float): SNR reading 8
        snr9 (float): SNR reading 9
        snr10 (float): SNR reading 10
        snr11 (float): SNR reading 11
        created (str): Timestamp when the device object is created
        updated (str): Timestamp when the device object is updated
    """
    
    TABLENAME = 'devices'
    
    def beforeCreate(self):
        """Twistar method called before a new object is created.
        
         Returns:
            True on success. If False is returned, then the object is
            not saved in the database.
        """
        self.created = datetime.datetime.now(tz=pytz.utc).isoformat()
        return True
    
    def beforeSave(self):
        """Twistar method called before an existing object is saved.
        
        This method is called after beforeCreate when an object is being
        created, and after beforeUpdate when an existing object
        (whose id is not None) is being saved.
        
        Returns:
            True on success. If False is returned, then the object is
            not saved in the database.
        """
        self.updated = datetime.datetime.now(tz=pytz.utc).isoformat()
        return True
    
    @inlineCallbacks
    def update(self, *args, **kwargs):
        """Updates the object with a variable list of attributes
        
        """
        if kwargs is not None:
            yield self.refresh()
            for key, value in kwargs.iteritems():
                if hasattr(self, key):
                    setattr(self, key, value)
            yield self.save()
    
    def resetFrameCount(self):
        """Reset frame count parameters
        
        """
        self.fcntup = 0
        self.fcntdown = 0
        self.fcnterror = False
    
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
        
        if self.snr_pointer is None:
            self.snr_pointer = 1
        
        # Update the current SNR reading
        snr = str('snr' + str(self.snr_pointer))
        setattr(self, snr, lsnr)
        
        # Average SNR readings
        self.averageSNRs()
    
        # Increment/rotate the pointer
        self.snr_pointer = self.snr_pointer % 11 + 1
        
        
    def averageSNRs(self):
        """Calculates the average of the last six SNR readings.
        If we do not have six valid readings, set average to
        None.
        
        Args:
            None
        """
        # Get the last 6 SNR readings
        if self.snr_pointer >= 6:
            measures = range(self.snr_pointer - 5, self.snr_pointer + 1)
        else:
            measures = range(1, self.snr_pointer + 1)
            measures.extend(range(self.snr_pointer + 6, 12))
        snrs = []
        for i in measures:
            attr = 'snr' + str(i)
            snr = getattr(self, attr) if hasattr(self, attr) else None
            snrs.append(snr)
        
        # Calculate the average
        self.snr_average = sum(snrs)/len(snrs) if not None in snrs else None

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
        
        # Target thresholds that the average must exceed. Note range(0,4) refers
        # to the first four (upstream) indices of the band.datarate list. These
        # are DR0, DR1, DR2, DR3
        thresholds = [float(i) * 3.0 + margin for i in range(0,4)]

        # If we have an average SNR less than the lowest threshold, return the lowest DR
        if self.snr_average < thresholds[0]:
            return band.datarate[0]
        
        # Find the index of lowest threshold that the SNR average just exceeds
        i = [n for n,v in enumerate(thresholds) if self.snr_average >= v][-1]
        return band.datarate[i]
    