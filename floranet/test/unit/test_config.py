
from twisted.trial import unittest

import ConfigParser
import io
import floranet.config as config

class configTest(unittest.TestCase):
    
    def setUp(self):
        self.cdata = """
[server]
listen = 127.0.0.1
port = 1700
freqband = AU915
netid = 0x010203
abpdevices = [
    [0x06100000, 0x0A0B0C0D0A0B0C0D, 0xAEB48D4C6E9EA5C48C37E4F132AA8516, 0x7987A96F267F0A86B739EED480FC2B3C],
    [0x06100001, 0x0A0B0C0D0A0B0C0D, 0x8D952A0140C298C010F418FF70EFC2B2, 0xF00E22163B9E9260B454BE6C4B26A91C],
    [0x06100002, 0x0A0B0C0D0A0B0C0D, 0x9E583C0B4B64789A81E6A39249D478C8, 0x85B010B651C834D3583B9F907BEF4945]
    ]
"""
        self.config = config.Configuration()
        self.config.parser = ConfigParser.SafeConfigParser()
        self.config.parser.readfp(io.BytesIO(self.cdata))
    
    def test_getOption_pass(self):
        
        abpdevices = eval(
                    """[
                        [0x06100000, 0x0A0B0C0D0A0B0C0D,
                         0xAEB48D4C6E9EA5C48C37E4F132AA8516,
                         0x7987A96F267F0A86B739EED480FC2B3C],
                        [0x06100001, 0x0A0B0C0D0A0B0C0D,
                         0x8D952A0140C298C010F418FF70EFC2B2,
                         0xF00E22163B9E9260B454BE6C4B26A91C],
                        [0x06100002, 0x0A0B0C0D0A0B0C0D,
                         0x9E583C0B4B64789A81E6A39249D478C8,
                         0x85B010B651C834D3583B9F907BEF4945]
                    ]""")
        expected = [('freqband', 'AU915'),
                    ('port', 1700),
                    ('listen', '127.0.0.1'),
                    ('netid', int('0x010203', 16)),
                    ('abpdevices', abpdevices)
                   ]
        
        options = [
            config.Option('freqband', 'str', default=False),
            config.Option('port', 'int', default=False),
            config.Option('listen', 'address', default=True, val=''),
            config.Option('netid', 'hex', default=False, length=3),
            config.Option('abpdevices', 'array', default=True, val=[])
        ]
        result = []
        for option in options:
            self.config._getOption('server', option, self.config)
            result.append((option.name, getattr(self.config, option.name)))
        
        self.assertEqual(expected, result)
        
    def test_getOption_fail(self):
        options = [
            config.Option('freqband', 'int', default=False),
            config.Option('port', 'address', default=False),
            config.Option('netid', 'hex', default=False, length=4),
            config.Option('netid', 'array', default=False),
            config.Option('missing', 'str', default=False)
            ]
        
        expected = [False] * len(options)
        result = []
        for option in options:
            result.append(self.config._getOption('server', option, self.config))
            
        self.assertEqual(expected, result)
                
                
            
        


        
    
