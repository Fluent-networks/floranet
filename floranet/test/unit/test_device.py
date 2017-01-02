import os

from twisted.trial import unittest

from twisted.enterprise import adbapi
from twistar.registry import Registry

from floranet.config import Configuration
from floranet.device import Device
from floranet.lora_bands import US915

class DeviceTest(unittest.TestCase):
    
    def setUp(self):
        """Test Setup.
        """
        # Get configuration
        self.config = Configuration()
        cfile = os.path.join(self.config.path, 'test', 'unit', 'default.cfg')
        if not self.config.parseConfig(cfile):
            exit(1)
        
        # Set Registry.DBPOOL to a adbapi.ConnectionPool
        (driver, host, user, password, database) = self.config.database
        Registry.DBPOOL = adbapi.ConnectionPool(driver, host=host,
                  user=user, password=password, database=database)
    
    def _test_device(self):
        """Create a test device object. We must load the device
        dynamically as it depends on the adbapi intialisation"""
        
        return Device(
            deveui=int('0x0F0E0E0D00010209', 16),
            devaddr=int('0x06000001', 16),
            appeui=int('0x0A0B0C0D0A0B0C0D', 16),
            nwkskey=int('0xAEB48D4C6E9EA5C48C37E4F132AA8516', 16),
            appskey=int('0x7987A96F267F0A86B739EED480FC2B3C', 16),
            tx_chan=3,
            tx_datr='SF7BW125',
            gw_addr='192.168.1.125')
    
    def test_updateSNR(self):
        """Test updating a SNR measure """
        device = self._test_device()
        # Expected - pointer, measure
        expected = [2, 1.1]
        
        device.snr_pointer = 1
        device.updateSNR(1.1)
        results = [device.snr_pointer, getattr(device, 'snr1')]
        
        self.assertEqual(expected, results)
    
    def test_averageSNRs(self):
        """Test averageSNRs method"""
        
        # Mockup some readings
        snrs = {'snr1': 1.0, 'snr2': 2.0, 'snr3': 3.0, 'snr4': 3.0, 'snr5': 2.0, 'snr6': 1.0,
                'snr7': 2.0, 'snr8': 3.0, 'snr9': 2.0, 'snr10': 1.0, 'snr11': 3.0}
        device = self._test_device()
        for a,v in snrs.iteritems():
            setattr(device, a, v)
        
        expected = [2.0, 2.0, 2.0, None]
        results = []
        
        # Test positions 1, 6 and 11
        pointers = [1, 6, 11]
        for p in pointers:
            device.snr_pointer = p
            device.averageSNRs()
            results.append(device.snr_average)
        
        # Set all values to None
        for a in snrs:
            setattr(device, a, None)
        device.averageSNRs()
        results.append(device.snr_average)
        
        self.assertEqual(expected, results)
        
    def test_getADRDatarate(self):
        """Test getADRDatarate method"""
        device = self._test_device()
        band = US915()
        margin = 0
        
        expected = ['SF10BW125', 'SF9BW125', 'SF8BW125', 'SF7BW125', 'SF7BW125']
        results = []

        for t in range(0,5):
            device.snr_average = t*3 + 0.1 
            result = device.getADRDatarate(band, margin)
            results.append(result)
        
        self.assertEqual(expected, results)
        
            
        

        
    