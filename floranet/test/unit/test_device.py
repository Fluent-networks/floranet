
from twisted.trial import unittest

import floranet.device as device

class deviceTest(unittest.TestCase):
    
    def test_checkFrameCount(self):
        maxfcntgap = 16384
        dev = device.Device(fcntup=1000)
        expected = [True, False, False, True]
        
        result = []
        fcnts = [dev.fcntup, dev.fcntup + maxfcntgap + 1,
                0, 1001]
        for fcnt in fcnts:
            result.append(dev.checkFrameCount(fcnt, maxfcntgap))
        
        self.assertEqual(expected, result)



        
    
