import os
import json

from twisted.trial import unittest
from mock import patch, MagicMock

# Patch crochet wait_for decorator
patch('crochet.wait_for', lambda **x: lambda f : f).start()
# Patch flask_login login_required decorator
patch('flask_login.login_required', lambda x : x).start()

from twisted.internet import defer
from twisted.internet.defer import inlineCallbacks
from flask import Flask
from flask_restful import Api, Resource, reqparse
import werkzeug.exceptions as e
from twistar.registry import Registry

from floranet.models.config import Config
from floranet.models.application import Application
from floranet.models.device import Device
from floranet.netserver import NetServer
from floranet.web.webserver import WebServer

from floranet.web.rest.application import RestApplication, RestApplications
from floranet.test.unit.mock_reactor import reactorCall
import floranet.test.unit.mock_dbobject as mockDBObject

class RestApplicationTest(unittest.TestCase):
    
    def setUp(self):
        # Mock Registry
        Registry.getConfig =  MagicMock(return_value=None)
        
        # Load configuration defaults
        config = Config()
        config.defaults()
        
        self.server = NetServer(config)
        self.server.applications = []
        
        self.webserver = WebServer(self.server)
        self.restapi = self.webserver.restapi

    def _test_application(self):
        """Create a test application object. We must load 
        dynamically as it depends on the adbapi intialisation"""
        
        return Application(
            appeui=int('0x0A0B0C0D0A0B0C0D', 16),
            name='app',
            domain='fluentnetworks.com.au',
            appnonce=int('0xC28AE9',16),
            appkey=int('0x017E151638AEC2A6ABF7258809CF4F3C',16),
            fport=15,
            )
    
    @inlineCallbacks
    def test_get(self):
        """Test get method"""
        
        app = self._test_application()
        mockDBObject.return_value = app
        
        with patch.object(reqparse.RequestParser, 'parse_args'):
            resource = RestApplication(restapi=self.restapi, server=self.server)
            
            # Fail to find a device: raises 404 NotFound
            with patch.object(Application, 'find', classmethod(mockDBObject.findFail)):
                yield self.assertFailure(resource.get(app.appeui), e.NotFound)
            
            # Find a device success returns a dict of field values
            with patch.object(Application, 'find', classmethod(mockDBObject.findSuccess)):
                resource.getProperties = MagicMock()
                result = yield resource.get(app.appeui)
                self.assertEqual(app.appeui, result['appeui'])
                
    @inlineCallbacks
    def test_put(self):
        """Test put method"""
        
        app = self._test_application()
        mockDBObject.return_value = app
        
        with patch.object(reqparse.RequestParser, 'parse_args'):
            resource = RestApplication(restapi=self.restapi, server=self.server)
            
            # Fail to find a device: raises 404 NotFound
            with patch.object(Application, 'find', classmethod(mockDBObject.findFail)):
                yield self.assertFailure(resource.put(app.appeui), e.NotFound)
        
            # Find a device, device fails validity check: raises 400 BadRequest
            with patch.object(Application, 'find', classmethod(mockDBObject.findSuccess)):
                app.valid = MagicMock(return_value=(False, {}))
                yield self.assertFailure(resource.put(app.appeui), e.BadRequest)
            
                # Pass validity check, returns 200
                expected = ({}, 200)
                app.valid = MagicMock(return_value=(True, {}))
                app.update = MagicMock()
                result = yield resource.put(app.appeui)
                self.assertEqual(expected, result)

    @inlineCallbacks
    def test_delete(self):
        """Test delete method"""
        
        app = self._test_application()
        mockDBObject.return_value = app
        
        with patch.object(reqparse.RequestParser, 'parse_args'):
            resource = RestApplication(restapi=self.restapi, server=self.server)
            
            # Device exists with AppEUI: raises 400 error
            with patch.object(Device, 'find', classmethod(mockDBObject.findSuccess)):
                yield self.assertFailure(resource.delete(app.appeui), e.BadRequest)
            
            # Fail to find the application: raises 404 NotFound
            with patch.object(Device, 'find', classmethod(mockDBObject.findFail)), \
                patch.object(Application, 'find', classmethod(mockDBObject.findFail)):
                yield self.assertFailure(resource.delete(app.appeui), e.NotFound)
            
            # Find and delete, returns 200
            with patch.object(Device, 'find', classmethod(mockDBObject.findFail)), \
                patch.object(Application, 'find', classmethod(mockDBObject.findSuccess)):
                expected = ({}, 200)
                app.delete = MagicMock()
                result = yield resource.delete(app.appeui)
                self.assertEqual(expected, result)

class RestApplicationsTest(unittest.TestCase):
    """Test RestDevices class"""
    
    def setUp(self):
        # Mock Registry
        Registry.getConfig =  MagicMock(return_value=None)
        
        # Load configuration defaults
        config = Config()
        config.defaults()
        
        self.server = NetServer(config)
        self.webserver = WebServer(self.server)
        self.restapi = self.webserver.restapi

    def _test_application(self):
        """Create a test application object. We must load 
        dynamically as it depends on the adbapi intialisation"""
        
        return Application(
            appeui=int('0x0A0B0C0D0A0B0C0D', 16),
            name='app',
            domain='fluentnetworks.com.au',
            appnonce=int('0xC28AE9',16),
            appkey=int('0x017E151638AEC2A6ABF7258809CF4F3C',16),
            fport=15,
            )
    
    @inlineCallbacks
    def test_get(self):
        """Test get method"""
        
        app = self._test_application()
        mockDBObject.return_value = [app, app]

        with patch.object(reqparse.RequestParser, 'parse_args'):
            resource = RestApplications(restapi=self.restapi, server=self.server)
            
            # Fail to find any devices: return empty dict
            with patch.object(Application, 'all', classmethod(mockDBObject.findFail)):
                expected = {}
                result = yield resource.get()
                self.assertEqual(expected, result)
                
            with patch.object(Application, 'all', classmethod(mockDBObject.all)):
                resource.getProperties = MagicMock()
                expected = (app.appeui, 2)
                r = yield resource.get()
                result = (r[0]['appeui'], len(r))
                self.assertEqual(expected, result)

    @inlineCallbacks
    def test_post(self):
        """Test post method"""
        
        app = self._test_application()
        attrs = ['appeui', 'name', 'domain', 'appnonce', 'appkey', 'fport']
        args = {'appinterface_id': 1}
        for a in attrs:
            args[a] = getattr(app, a)
        
        # Remove a required arg - raises 400 BadRequest
        with patch.object(reqparse.RequestParser, 'parse_args',
                          MagicMock(return_value=args)):
            resource = RestApplications(restapi=self.restapi,
                                        server=self.server)
            args['name'] = None
            yield self.assertFailure(resource.post(), e.BadRequest)
            args['name'] = app.name

        # Application exists - raises 400 BadRequest
        with patch.object(reqparse.RequestParser, 'parse_args',
                          MagicMock(return_value=args)), \
                patch.object(Application, 'exists',
                             MagicMock(return_value=True)):
            resource = RestApplications(restapi=self.restapi,
                                        server=self.server)
            yield self.assertFailure(resource.post(), e.BadRequest)
            
        # Invalid application - raises 400 BadRequest
        with patch.object(reqparse.RequestParser, 'parse_args',
                          MagicMock(return_value=args)), \
                patch.object(Application, 'exists',
                             MagicMock(return_value=False)), \
                patch.object(Application, 'valid',
                             MagicMock(return_value=(False, {}))):
            resource = RestApplications(restapi=self.restapi,
                                        server=self.server)
            yield self.assertFailure(resource.post(), e.BadRequest)
            
        # Valid application - returns 201 with location
        with patch.object(reqparse.RequestParser, 'parse_args',
                          MagicMock(return_value=args)), \
                patch.object(Application, 'exists', MagicMock(return_value=None)), \
                patch.object(Application, 'valid', MagicMock(return_value=(True, {}))), \
                patch.object(Application, 'save',  MagicMock(return_value=app)):
            self.server.addApplication = MagicMock(return_value=True)
            resource = RestApplications(restapi=self.restapi, server=self.server)
            expected = ({}, 201, {'Location':
                self.restapi.api.prefix + '/app/' + str(app.appeui)})
            result = yield resource.post()
            self.assertEqual(expected, result)
  
        