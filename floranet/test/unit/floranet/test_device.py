import os

from twisted.trial import unittest
from mock import patch, MagicMock

from twistar.registry import Registry

from floranet.models.model import Model
from floranet.models.device import Device
from floranet.lora.bands import US915

class DeviceTest(unittest.TestCase):
    
    def setUp(self):
        """Test Setup.
        """
    
    def _test_device(self):
        """Create a test device object"""
        
        # Mock Registry.getConfig()
        with patch.object(Registry, 'getConfig', MagicMock(return_value=None)):
            return Device(
                deveui=int('0x0F0E0E0D00010209', 16),
                devaddr=int('0x06000001', 16),
                appeui=int('0x0A0B0C0D0A0B0C0D', 16),
                nwkskey=int('0xAEB48D4C6E9EA5C48C37E4F132AA8516', 16),
                appskey=int('0x7987A96F267F0A86B739EED480FC2B3C', 16),
                tx_chan=3,
                tx_datr='SF7BW125',
                gw_addr='192.168.1.125',
                snr=None)

    def test_updateSNR(self):
        """Test updating a SNR measure """
        device = self._test_device()
        # Expected - pointer, measure
        expected = [2.0, 4.0]
        
        device.updateSNR(2.0)
        device.updateSNR(4.0)
        result = device.snr

        self.assertEqual(expected, result)
        
        expected = 3.0
        
        for i in range(0,2):
            device.updateSNR(2.0)
            device.updateSNR(4.0)
        result = device.snr_average
        
        self.assertEqual(expected, result)
        
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
        
            
        

        
    