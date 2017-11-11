import os
import json

from twisted.trial import unittest
from mock import patch, MagicMock

# Patch crochet wait_for decorator
patch('crochet.wait_for', lambda **x: lambda f : f).start()
# Patch flask_login login_required decorator
patch('flask_login.login_required', lambda x : x).start()

from twisted.internet.defer import inlineCallbacks
from flask import Flask
from flask_restful import Api, Resource, reqparse
import werkzeug.exceptions as e

from twistar.registry import Registry
from twistar.relationships import HasMany

from floranet.models.model import Model
from floranet.models.config import Config
from floranet.models.appinterface import AppInterface
from floranet.appserver.azure_iot_https import AzureIotHttps
from floranet.database import Database
from floranet.netserver import NetServer
from floranet.imanager import interfaceManager
from floranet.web.webserver import WebServer

from floranet.web.rest.appinterface import RestAppInterface, RestAppInterfaces
import floranet.test.unit.mock_dbobject as mockDBObject

class RestAppInterfaceTest(unittest.TestCase):
    
    @inlineCallbacks
    def setUp(self):
        
        # Twistar requirem
        Registry.getConfig =  MagicMock(return_value=None)
        db = Database()
        db.register()
        
        # Get factory default configuration
        with patch.object(Model, 'save', MagicMock()):
            config = yield Config.loadFactoryDefaults()
            
        self.server = NetServer(config)        
        self.webserver = WebServer(self.server)
        self.restapi = self.webserver.restapi

    def _test_appinterface(self):
        """Create a test application object."""
        
        return AppInterface(
            id=1,
            application_id=1,
            interfaces_type='AzureIotHttps',
            interfaces_id=1,
            )
    
    def _test_azureiothttps(self):
        """Create a test AzureIotHttps object"""
        return AzureIotHttps(
            id=1,
            name='Test Azure',
            iothost='somewhere.azure.microsoft.com',
            keyname='mykey',
            keyvalue='ishd7635klw3084%3',
            started = True,
            poll_interval=25,
        )
    
    @inlineCallbacks
    def test_get(self):
        """Test get method"""
        
        interface = self._test_azureiothttps()
        appif = self._test_appinterface()
        interface.appinterface = appif
        interfaceManager.interfaces = [interface]
        
        with patch.object(reqparse.RequestParser, 'parse_args'):
            resource = RestAppInterface(restapi=self.restapi, server=self.server)
            
            # Fail to find the app interface: raises 404 NotFound
            interfaceManager.getInterface = MagicMock(return_value=None)
            yield self.assertFailure(resource.get(1), e.NotFound)
            
            # Success finding the interface returns a dict of field values
            interfaceManager.getInterface = MagicMock(return_value=interface)
            result = yield resource.get(appif.id)
            self.assertEqual(interface.name, result['name'])

    
    @inlineCallbacks
    def test_put(self):
        """Test put method"""
        
        interface = self._test_azureiothttps()
        appif = self._test_appinterface()
        interface.appinterface = appif
        interfaceManager.interfaces = [interface]
        args = {'name': 'Testing'}
        
        with patch.object(reqparse.RequestParser, 'parse_args',
                          MagicMock(return_value=args)):
            resource = RestAppInterface(restapi=self.restapi, server=self.server)
            
            # Fail to find the app interface: raises 404 NotFound
            interfaceManager.getInterface = MagicMock(return_value=None)
            yield self.assertFailure(resource.put(1), e.NotFound)
            
            # Success updating the interface name
            expected = ({}, 200)
            interfaceManager.getInterface = MagicMock(return_value=interface)
            with patch.object(AzureIotHttps, 'save',
                              MagicMock(return_value=interface)), \
                patch.object(HasMany, 'get', MagicMock(return_value=appif)):
                interface.start = MagicMock()
                interface.stop = MagicMock()
                interface.started = True
                result = yield resource.put(1)
                self.assertEqual(expected, result)
                self.assertEqual(args['name'], interfaceManager.interfaces[0].name)


    @inlineCallbacks
    def test_delete(self):
        """Test delete method"""
        
        interface = self._test_azureiothttps()
        appif = self._test_appinterface()
        interface.appinterface = appif
        interfaceManager.interfaces = [interface]
        
        with patch.object(reqparse.RequestParser, 'parse_args'):
            resource = RestAppInterface(restapi=self.restapi, server=self.server)
            
            # Fail to find the interface: raises 404 NotFound
            interfaceManager.getInterface = MagicMock(return_value=None)
            yield self.assertFailure(resource.delete(1), e.NotFound)
            
            # Find and delete, returns 200
            with patch.object(AzureIotHttps, 'exists', MagicMock(return_value=True)), \
                patch.object(HasMany, 'get', MagicMock(return_value=[appif])), \
                patch.object(AzureIotHttps, 'delete'), \
                patch.object(AppInterface, 'delete'):
                interfaceManager.getInterface = MagicMock(return_value=interface)
                expected = ({}, 200)
                result = yield resource.delete(1)
                self.assertEqual(expected, result)

class RestAppInterfacesTest(unittest.TestCase):
    
    @inlineCallbacks
    def setUp(self):
        
        # Twistar requirem
        Registry.getConfig =  MagicMock(return_value=None)
        db = Database()
        db.register()
        
        # Get factory default configuration
        with patch.object(Model, 'save', MagicMock()):
            config = yield Config.loadFactoryDefaults()
            
        self.server = NetServer(config)        
        self.webserver = WebServer(self.server)
        self.restapi = self.webserver.restapi

    def _test_appinterface(self):
        """Create a test AppInterface object."""
        
        return AppInterface(
            id=1,
            application_id=1,
            interfaces_type='AzureIotHttps',
            interfaces_id=1,
            )
    
    def _test_azureiothttps(self):
        """Create a test AzureIotHttps object"""
        return AzureIotHttps(
            id=1,
            name='Test Azure',
            iothost='somewhere.azure.microsoft.com',
            keyname='mykey',
            keyvalue='ishd7635klw3084%3',
            started = True,
            poll_interval=25,
        )
    
    @inlineCallbacks
    def test_get(self):
        """Test get method"""
        
        interface = self._test_azureiothttps()
        appif = self._test_appinterface()
        interface.appinterface = appif
        interfaceManager.interfaces = [interface]
        
        with patch.object(reqparse.RequestParser, 'parse_args'):
            resource = RestAppInterfaces(restapi=self.restapi, server=self.server)
            
            # Success finding the interface returns a dict of field values
            interfaceManager.getAllInterfaces = MagicMock(return_value=[interface])
            result = yield resource.get()
            self.assertEqual(interface.name, result[0]['name'])


    @inlineCallbacks
    def test_post(self):
        """Test post method"""
        
        appif = self._test_appinterface()    
        interface = self._test_azureiothttps()
        interface.appinterface = appif
        attrs = ['name', 'iothost', 'keyname', 'keyvalue']
        args = {}
        for a in attrs:
            args[a] = getattr(interface, a)
        args['type'] = 'azure'
        args['protocol'] = 'https'
        args['pollinterval'] = getattr(interface, 'poll_interval')
        
        # Remove a required arg - raises 400 BadRequest
        with patch.object(reqparse.RequestParser, 'parse_args',
                          MagicMock(return_value=args)):
            resource = RestAppInterfaces(restapi=self.restapi,
                                        server=self.server)
            args['name'] = None
            yield self.assertFailure(resource.post(), e.BadRequest)
            args['name'] = interface.name

        # Interface exists - raises 400 BadRequest
        with patch.object(reqparse.RequestParser, 'parse_args',
                          MagicMock(return_value=args)), \
                patch.object(AzureIotHttps, 'exists',
                             MagicMock(return_value=True)):
            resource = RestAppInterfaces(restapi=self.restapi,
                                        server=self.server)
            yield self.assertFailure(resource.post(), e.BadRequest)
            
        # Invalid interface - raises 400 BadRequest
        with patch.object(reqparse.RequestParser, 'parse_args',
                          MagicMock(return_value=args)), \
                patch.object(AzureIotHttps, 'exists',
                             MagicMock(return_value=False)), \
                patch.object(AzureIotHttps, 'valid',
                             MagicMock(return_value=(False, {}))):
            resource = RestAppInterfaces(restapi=self.restapi,
                                        server=self.server)
            yield self.assertFailure(resource.post(), e.BadRequest)
            
        # Valid application - returns 201 with location
        with patch.object(reqparse.RequestParser, 'parse_args',
                          MagicMock(return_value=args)), \
                patch.object(AzureIotHttps, 'exists', MagicMock(return_value=None)), \
                patch.object(AzureIotHttps, 'valid', MagicMock(return_value=(True, {}))), \
                patch.object(interfaceManager, 'createInterface', return_value=interface.id):
            resource = RestAppInterfaces(restapi=self.restapi, server=self.server)
            expected = ({}, 201, {'Location':
                self.restapi.api.prefix + '/interface/' + str(appif.id)})
            result = yield resource.post()
            self.assertEqual(expected, result)
