import os
import json

from twisted.trial import unittest
from mock import patch, MagicMock

# Patch crochet wait_for decorator
patch('crochet.wait_for', lambda **x: lambda f : f).start()
# Patch flask_login login_required decorator
patch('flask_login.login_required', lambda x : x).start()

from flask import Flask
from flask_restful import Api, Resource, reqparse
import werkzeug.exceptions as e

from twisted.internet.defer import inlineCallbacks
from twistar.registry import Registry

from floranet.models.model import Model
from floranet.models.config import Config
from floranet.models.gateway import Gateway

from floranet.netserver import NetServer
from floranet.lora.wan import LoraWAN
from floranet.web.webserver import WebServer

from floranet.web.rest.gateway import RestGateway, RestGateways
import floranet.test.unit.mock_dbobject as mockDBObject

class RestGatewayTest(unittest.TestCase):
    
    @inlineCallbacks
    def setUp(self):
        """Test setup"""
        Registry.getConfig =  MagicMock(return_value=None)
        
        # Get factory default configuration
        with patch.object(Model, 'save', MagicMock()):
            config = yield Config.loadFactoryDefaults()
            
        self.server = NetServer(config)
        self.server.lora = LoraWAN(self.server)
        self.webserver = WebServer(self.server)
        self.restapi = self.webserver.restapi

    def _test_gateway(self):
        """Create a test gateway object.
        
        We must load the object dynamically as it depends on the adbapi
        intialisation.
        """
        
        return Gateway(
            host='192.168.1.125',
            name='gateway',
            eui=36028797019005945,
            enabled=True,
            power=20,
            )
    
    @inlineCallbacks
    def test_get(self):
        """Test get method"""
        
        gateway = self._test_gateway()
        mockDBObject.return_value = gateway
        
        with patch.object(reqparse.RequestParser, 'parse_args'):
            resource = RestGateway(restapi=self.restapi, server=self.server)
            
            # Fail to find a gateway: raises 404 NotFound
            with patch.object(Gateway, 'find', classmethod(mockDBObject.findFail)):
                yield self.assertFailure(resource.get(gateway.host), e.NotFound)
            
            # Find a device success returns a dict of field values
            with patch.object(Gateway, 'find', classmethod(mockDBObject.findSuccess)):
                result = yield resource.get(gateway.host)
                self.assertEqual(gateway.host, result['host'])

    @inlineCallbacks
    def test_put(self):
        """Test put method"""
        
        gateway = self._test_gateway()
        mockDBObject.return_value = gateway
        
        with patch.object(reqparse.RequestParser, 'parse_args'):
            resource = RestGateway(restapi=self.restapi, server=self.server)
            
            # Fail to find the gateway: raises 404 NotFound
            with patch.object(Gateway, 'find', classmethod(mockDBObject.findFail)):
                yield self.assertFailure(resource.put(gateway.host), e.NotFound)

            # Find a device, device fails validity check: raises 400 BadRequest
            with patch.object(Gateway, 'find', classmethod(mockDBObject.findSuccess)):
                gateway.valid = MagicMock(return_value=(False, {}))
                yield self.assertFailure(resource.put(gateway.host), e.BadRequest)
            
                # Pass validity check, returns 200
                expected = ({}, 200)
                gateway.valid = MagicMock(return_value=(True, {}))
                gateway.update = MagicMock()
                result = yield resource.put(gateway.host)
                self.assertEqual(expected, result)

    @inlineCallbacks
    def test_delete(self):
        """Test delete method"""
        
        gateway = self._test_gateway()
        mockDBObject.return_value = gateway
        
        with patch.object(reqparse.RequestParser, 'parse_args'):
            resource = RestGateway(restapi=self.restapi, server=self.server)
            
            # Fail to find a device: raises 404 NotFound
            with patch.object(Gateway, 'find', classmethod(mockDBObject.findFail)):
                yield self.assertFailure(resource.delete(gateway.host), e.NotFound)
            
            # Find a device and delete, returns 200
            with patch.object(Gateway, 'find', classmethod(mockDBObject.findSuccess)):
                expected = ({}, 200)
                gateway.delete = MagicMock()
                self.server.lora.deleteGateway = MagicMock()
                result = yield resource.delete(gateway.host)
                self.assertEqual(expected, result)

class RestGatewaysTest(unittest.TestCase):
    """Test RestGateways class"""
    
    @inlineCallbacks
    def setUp(self):
        """Test setup"""
        Registry.getConfig =  MagicMock(return_value=None)
        
        # Get factory default configuration
        with patch.object(Model, 'save', MagicMock()):
            config = yield Config.loadFactoryDefaults()
            
        self.server = NetServer(config)
        self.server.lora = LoraWAN(self.server)
        self.webserver = WebServer(self.server)
        self.restapi = self.webserver.restapi

    def _test_gateway(self):
        """Create a test gateway object. We must load the device
        dynamically as it depends on the adbapi intialisation"""
        
        return Gateway(
            host='192.168.1.125',
            name='gateway',
            eui=36028797019005945,
            enabled=True,
            power=20,
            )
    
    @inlineCallbacks
    def test_get(self):
        """Test get method"""
        
        gateway = self._test_gateway()
        mockDBObject.return_value = [gateway, gateway]

        with patch.object(reqparse.RequestParser, 'parse_args'):
            resource = RestGateways(restapi=self.restapi, server=self.server)
            
            # Fail to find any devices: return empty dict
            with patch.object(Gateway, 'all', classmethod(mockDBObject.findFail)):
                expected = {}
                result = yield resource.get()
                self.assertEqual(expected, result)
                
            with patch.object(Gateway, 'all', classmethod(mockDBObject.all)):
                expected = (gateway.host, 2)
                r = yield resource.get()
                result = (r[0]['host'], len(r))
                self.assertEqual(expected, result)


    @inlineCallbacks
    def test_post(self):
        """Test post method"""
        
        gateway = self._test_gateway()
        attrs = ['host', 'name', 'eui', 'enabled', 'power']
        args = {}
        for a in attrs:
            args[a] = getattr(gateway, a)
        
        # Remove a required arg - raises 400 BadRequest
        with patch.object(reqparse.RequestParser, 'parse_args',
                          MagicMock(return_value=args)):
            resource = RestGateways(restapi=self.restapi, server=self.server)
            args['name'] = None
            yield self.assertFailure(resource.post(), e.BadRequest)
            args['name'] = gateway.name

        # Device exists - raises 400 BadRequest
        with patch.object(reqparse.RequestParser, 'parse_args',
                          MagicMock(return_value=args)), \
                patch.object(Gateway, 'exists',
                             MagicMock(return_value=True)):
            resource = RestGateways(restapi=self.restapi, server=self.server)
            yield self.assertFailure(resource.post(), e.BadRequest)
            
        # Invalid device - raises 400 BadRequest
        with patch.object(reqparse.RequestParser, 'parse_args',
                          MagicMock(return_value=args)), \
                patch.object(Gateway, 'exists',
                             MagicMock(return_value=False)), \
                patch.object(Gateway, 'valid',
                             MagicMock(return_value=(False, {}))):
            resource = RestGateways(restapi=self.restapi, server=self.server)
            yield self.assertFailure(resource.post(), e.BadRequest)
            
        # Valid device - returns 201 with location
        with patch.object(reqparse.RequestParser, 'parse_args',
                          MagicMock(return_value=args)), \
                patch.object(Gateway, 'exists', MagicMock(return_value=False)), \
                patch.object(Gateway, 'valid', MagicMock(return_value=(True, {}))), \
                patch.object(Gateway, 'save',  MagicMock(return_value=gateway)):
            expected = ({}, 201, {'Location':
                self.restapi.api.prefix + '/gateway/' + gateway.host})
            resource = RestGateways(restapi=self.restapi, server=self.server)
            self.server.lora.addGateway = MagicMock()
            result = yield resource.post()
            self.assertEqual(expected, result)


        