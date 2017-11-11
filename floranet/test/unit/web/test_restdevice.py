import os
import json

from twisted.trial import unittest
from mock import patch, MagicMock

# Patch crochet wait_for decorator
patch('crochet.wait_for', lambda **x: lambda f : f).start()
# Patch flask_login login_required decorator
patch('flask_login.login_required', lambda x : x).start()

from twistar.registry import Registry

from flask import Flask
from flask_restful import Api, Resource, reqparse
import werkzeug.exceptions as e

from twisted.internet.defer import inlineCallbacks

from floranet.models.model import Model
from floranet.models.config import Config
from floranet.netserver import NetServer
from floranet.web.webserver import WebServer
from floranet.models.device import Device

from floranet.web.rest.device import RestDevice, RestDevices
import floranet.test.unit.mock_dbobject as mockDBObject

class RestDeviceTest(unittest.TestCase):
    
    @inlineCallbacks
    def setUp(self):
        """Test setup"""
        
        Registry.getConfig =  MagicMock(return_value=None)
        
        # Get factory default configuration
        with patch.object(Model, 'save', MagicMock()):
            config = yield Config.loadFactoryDefaults()
            
        self.server = NetServer(config)
        self.webserver = WebServer(self.server)
        self.restapi = self.webserver.restapi

    def _test_device(self):
        """Create a test device object. We must load the device
        dynamically as it depends on the adbapi intialisation"""
        
        return Device(
            deveui=int('0x0F0E0E0D00010209', 16),
            name='device',
            devclass='c',
            enabled=True,
            otaa=False,
            devaddr=int('0x06000001', 16),
            appeui=int('0x0A0B0C0D0A0B0C0D', 16),
            nwkskey=int('0xAEB48D4C6E9EA5C48C37E4F132AA8516', 16),
            appskey=int('0x7987A96F267F0A86B739EED480FC2B3C', 16),
            tx_chan=3,
            tx_datr='SF7BW125',
            gw_addr='192.168.1.125',
            )
    
    @inlineCallbacks
    def test_get(self):
        """Test get method"""
        
        device = self._test_device()
        mockDBObject.return_value = device
        
        with patch.object(reqparse.RequestParser, 'parse_args'):
            resource = RestDevice(restapi=self.restapi, server=self.server)
            
            # Fail to find a device: raises 404 NotFound
            with patch.object(Device, 'find', classmethod(mockDBObject.findFail)):
                yield self.assertFailure(resource.get(device.deveui), e.NotFound)
            
            # Find a device success returns a dict of field values
            with patch.object(Device, 'find', classmethod(mockDBObject.findSuccess)):
                result = yield resource.get(device.deveui)
                self.assertEqual(device.deveui, result['deveui'])
                
    @inlineCallbacks
    def test_put(self):
        """Test put method"""
        
        device = self._test_device()
        mockDBObject.return_value = device
        
        with patch.object(reqparse.RequestParser, 'parse_args'):
            resource = RestDevice(restapi=self.restapi, server=self.server)
            
            # Fail to find a device: raises 404 NotFound
            with patch.object(Device, 'find', classmethod(mockDBObject.findFail)):
                yield self.assertFailure(resource.put(device.deveui), e.NotFound)
        
            # Find a device, device fails validity check: raises 400 BadRequest
            with patch.object(Device, 'find', classmethod(mockDBObject.findSuccess)):
                device.valid = MagicMock(return_value=(False, {}))
                yield self.assertFailure(resource.put(device.deveui), e.BadRequest)
            
                # Pass validity check, returns 200
                expected = ({}, 200)
                device.valid = MagicMock(return_value=(True, {}))
                device.update = MagicMock()
                result = yield resource.put(device.deveui)
                self.assertEqual(expected, result)

    @inlineCallbacks
    def test_delete(self):
        """Test delete method"""
        
        device = self._test_device()
        mockDBObject.return_value = device
        
        with patch.object(reqparse.RequestParser, 'parse_args'):
            resource = RestDevice(restapi=self.restapi, server=self.server)
            
            # Fail to find a device: raises 404 NotFound
            with patch.object(Device, 'find', classmethod(mockDBObject.findFail)):
                yield self.assertFailure(resource.delete(device.deveui), e.NotFound)
            
            # Find a device adn delete, returns 200
            with patch.object(Device, 'find', classmethod(mockDBObject.findSuccess)):
                expected = ({}, 200)
                device.delete = MagicMock()
                result = yield resource.delete(device.deveui)
                self.assertEqual(expected, result)

class RestDevicesTest(unittest.TestCase):
    """Test RestDevices class"""
    
    @inlineCallbacks
    def setUp(self):
        """Test setup"""
        
        Registry.getConfig =  MagicMock(return_value=None)
        
        # Get factory default configuration
        with patch.object(Model, 'save', MagicMock()):
            config = yield Config.loadFactoryDefaults()
            
        self.server = NetServer(config)
        self.webserver = WebServer(self.server)
        self.restapi = self.webserver.restapi

    def _test_device(self):
        """Create a test device object. We must load the device
        dynamically as it depends on the adbapi intialisation"""
        
        return Device(
            deveui=int('0x0F0E0E0D00010209', 16),
            name='device',
            devclass='c',
            enabled=True,
            otaa=False,
            devaddr=int('0x06000001', 16),
            appeui=int('0x0A0B0C0D0A0B0C0D', 16),
            nwkskey=int('0xAEB48D4C6E9EA5C48C37E4F132AA8516', 16),
            appskey=int('0x7987A96F267F0A86B739EED480FC2B3C', 16),
            tx_chan=3,
            tx_datr='SF7BW125',
            gw_addr='192.168.1.125',
            )
    
    @inlineCallbacks
    def test_get(self):
        """Test get method"""
        
        device = self._test_device()
        mockDBObject.return_value = [device, device]

        with patch.object(reqparse.RequestParser, 'parse_args'):
            resource = RestDevices(restapi=self.restapi, server=self.server)
            
            # Fail to find any devices: return empty dict
            with patch.object(Device, 'all', classmethod(mockDBObject.findFail)):
                expected = {}
                result = yield resource.get()
                self.assertEqual(expected, result)
                
            with patch.object(Device, 'all', classmethod(mockDBObject.all)):
                expected = (device.deveui, 2)
                r = yield resource.get()
                result = (r[0]['deveui'], len(r))
                self.assertEqual(expected, result)

    @inlineCallbacks
    def test_post(self):
        """Test post method"""
        
        device = self._test_device()
        attrs = ['deveui', 'name', 'devclass', 'enabled', 'otaa', 'devaddr',
                 'appeui', 'devaddr', 'appeui', 'nwkskey', 'appskey']
        args = {}
        for a in attrs:
            args[a] = getattr(device, a)
        
        # Remove a required arg - raises 400 BadRequest
        with patch.object(reqparse.RequestParser, 'parse_args',
                          MagicMock(return_value=args)):
            resource = RestDevices(restapi=self.restapi, server=self.server)
            args['name'] = None
            yield self.assertFailure(resource.post(), e.BadRequest)
            args['name'] = device.name

        # Device exists - raises 400 BadRequest
        with patch.object(reqparse.RequestParser, 'parse_args',
                          MagicMock(return_value=args)), \
                patch.object(Device, 'exists',
                             MagicMock(return_value=True)):
            resource = RestDevices(restapi=self.restapi, server=self.server)
            yield self.assertFailure(resource.post(), e.BadRequest)
            
        # Invalid device - raises 400 BadRequest
        with patch.object(reqparse.RequestParser, 'parse_args',
                          MagicMock(return_value=args)), \
                patch.object(Device, 'exists',
                             MagicMock(return_value=False)), \
                patch.object(Device, 'valid',
                             MagicMock(return_value=(False, {}))):
            resource = RestDevices(restapi=self.restapi, server=self.server)
            yield self.assertFailure(resource.post(), e.BadRequest)
            
        # Valid device - returns 201 with location
        with patch.object(reqparse.RequestParser, 'parse_args',
                          MagicMock(return_value=args)), \
                patch.object(Device, 'exists', MagicMock(return_value=False)), \
                patch.object(Device, 'valid', MagicMock(return_value=(True, {}))), \
                patch.object(Device, 'save',  MagicMock(return_value=device)):
            resource = RestDevices(restapi=self.restapi, server=self.server)
            expected = ({}, 201, {'Location':
                self.restapi.api.prefix + '/device/' + str(device.deveui)})
            result = yield resource.post()
            self.assertEqual(expected, result)
  
        