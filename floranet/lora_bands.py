
class US915(object):
    """US 902-928 ISM Band
    
    upstream (list): 72 upstream (from device) channels:
                    64 channels (0 to 63) utilizing LoRa 125 kHz BW
                    starting at 902.3 MHz and incrementing
                    linearly by 200 kHz to 914.9 MHz.
                    8 channels (64 to 71) utilizing LoRa 500 kHz BW
                    starting at 903.0 MHz and incrementing linearly
                    by 1.6 MHz to 914.2 MHz. Units of MHz
    downstream (list): 8 channels numbered 0 to 7 utilizing
                    LoRa 500 kHz BW starting at 923.3 MHz and incrementing
                    linearly by 600 kHz to 927.5 MHz. Units of MHz
    datarate (dict): Data rate configuration as per Table 18 of the
                    LoRa specification
    datarate_rev (dict): Reverse lookup for datarate.
    maxpayload (dict): Maximim payload size, indexed by datarate as per
                    Table 20 of the LoRa specification
    rx1dr (dict): Dictonary of lists to lookup the RX1 window data rate by
                    transmit data rate and Rx1DROffset parameters. Lookup by
                    rx1dr[txdatarate][rx1droffset]
    receive_delay (dict): First and second window window receive delays
    join_accept_delay (dict): First and second window join accept delay
                    
    """

    def __init__(self):
        """Initialize a US915 band object."""

        # Upstream channels in MHz
        self.upstream = []
        for i in range(0, 64):
            self.upstream.append((9033 + 2.0 * i)/10)
        for i in range(0, 8):
            self.upstream.append((9030 + 16.0 * (i - 64))/10)
        # Downstream channels in MHz
        self.downstream = []
        for i in range(0, 8):
            self.downstream.append((9233 + 6.0 * i)/10)
        self.datarate = {
            0:  'SF10BW125',
            1:  'SF9BW125',
            2:  'SF8BW125',
            3:  'SF7BW125',
            4:  'SF8BW125',
            8:  'SF12BW500',
            9:  'SF11BW500',
            10: 'SF10BW500',
            11: 'SF9BW500',
            12: 'SF8BW500',
            13: 'SF7BW500'
        }
        self.datarate_rev = {v:k for k, v in self.datarate.items()}
        self.maxpayload = {0:  19,  1:  61,  2:  137,  3:  250,
                           4:  250, 8:  41,  9:  117,  10: 230,
                           11: 230, 12: 230, 13: 230}
        self.rx1dr = {
                    0: [10,  9,   8,   8],
                    1: [11,  10,  9,   8],
                    2: [12,  11,  10,  9],
                    3: [13,  12,  11,  10],
                    4: [13,  13,  12,  11],
                    8: [8,   8,   8,   8],
                    9: [9,   8,   8,   8],
                   10: [10,  9,   8,   8],
                   11: [11,  10,  9,   8],
                   12: [11,  11,  10,  9], 
                   13: [13,  12,  11,  9]  }
        self.rx1droffset = 0
        self.receive_delay = {1: 1, 2: 2}
        self.join_accept_delay = {1: 1, 2: 2}
        self.max_fcnt_gap = 16384
        
    def _rx1receive(self, txch, txdr, rx1droffset):
        """Get first receive window parameters
        
        Args:
            txch (int): Transmit channel
            txdr (str): Transmit data rate 'SFnBWxxx'
            rx1droffset (int): RX1DROffset parameter
            
        Returns:
            A dict of RX1 frequency, datarate string, datarate index
        """
        rx1 = {'freq': None, 'datr': None, 'index': None}
        rx1['freq'] = self.downstream[txch % 8]
        txindex = self.datarate_rev[txdr]
        rx1['index'] = self.rx1dr[txindex][rx1droffset]
        rx1['datr'] = self.datarate[rx1['index']]
        return rx1
    
    def _rx2receive(self):
        """Get second receive window parameters
        
        RX2 (second receive window) settings uses a fixed data
        rate and frequency. Default parameters are 923.3Mhz / DR8
    
        Returns:
            A dict of RX2 frequency, datarate string, datarate index
        """
        rxindex = 8
        return {'freq': 923.3, 'datr': self.datarate[rxindex],
                'index': rxindex}

    def rxparams(self, rxpk, join=False):
        """Get RX1 and RX2 receive window parameters
        
        Args:
            rxpk (Rxpk): The received Rxpk object
            join (bool): Use join timers if true
        
        Retrurns:
            Dict of RX1 and RX2 parameter dicts {freq, datarate, drindex, delay}
        """
        rx1 = self._rx1receive(rxpk.chan, rxpk.datr, self.rx1droffset)
        rx2 = self._rx2receive()
        if join:
            rx1['delay'] = self.join_accept_delay[1]
            rx2['delay'] = self.join_accept_delay[2]
        else:
            rx1['delay'] = self.receive_delay[1]
            rx2['delay'] = self.receive_delay[2]
        return {1: rx1, 2: rx2}
    
class AU915(US915):
    """Australian pseudostandard 915-928 ISM Band
    
    Subclass of US915 band. Same parameters apply, with the exception
    of upstream channels, which are upshifted to start at 915.2 MHz
    (channels 0 to 63) and 915.9 (channels 64 to 71).
    
    """
    def __init__(self):
        super(AU915, self).__init__()
        self.upstream = []
        for i in range(0, 64):
            self.upstream.append((9152 + 2.0 * i)/10)
        for i in range(0, 8):
            self.upstream.append((9159 + 16.0 * i)/10)

    
