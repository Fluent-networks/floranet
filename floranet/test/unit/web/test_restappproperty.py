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
from twistar.relationships import HasMany

from floranet.models.config import Config
from floranet.models.application import Application
from floranet.models.appproperty import AppProperty
from floranet.database import Database
from floranet.netserver import NetServer
from floranet.web.webserver import WebServer

from floranet.web.rest.appproperty import RestAppProperty, RestAppPropertys
import floranet.test.unit.mock_dbobject as mockDBObject

class RestAppPropertyTest(unittest.TestCase):
    
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
    
    def _test_appproperty(self):
        """Create a test AppProperty object"""
        
        return AppProperty(application_id=1,
                           port=15,
                           name='Temperature',
                           type='float',
                           )
    
    @inlineCallbacks
    def test_get(self):
        """Test get method"""
        
        app = self._test_application()
        prop = self._test_appproperty()
        mockDBObject.return_value = prop
        args = {'port': prop.port }
        
        with patch.object(reqparse.RequestParser, 'parse_args',
                          MagicMock(return_value=args)):
            resource = RestAppProperty(restapi=self.restapi, server=self.server)
            
            # Fail to find the app: raises 404 NotFound
            with patch.object(Application, 'find', classmethod(mockDBObject.findFail)):
                yield self.assertFailure(resource.get(app.appeui), e.NotFound)

            # Fail to find the property: raises 404 NotFound
            with patch.object(Application, 'find', classmethod(mockDBObject.findSuccess)), \
                patch.object(AppProperty, 'find', classmethod(mockDBObject.findFail)):
                yield self.assertFailure(resource.get(app.appeui), e.NotFound)

            # Find a property success returns a dict of field values
            with patch.object(Application, 'find', classmethod(mockDBObject.findSuccess)), \
                patch.object(AppProperty, 'find', classmethod(mockDBObject.findSuccess)):
                result = yield resource.get(app.appeui)
                self.assertEqual(prop.port, result['port'])

    @inlineCallbacks
    def test_put(self):
        """Test put method"""
        
        app = self._test_application()
        prop = self._test_appproperty()
        mockDBObject.return_value = prop
        args = {'port': prop.port}
        
        with patch.object(reqparse.RequestParser, 'parse_args',
                          MagicMock(return_value=args)):
            resource = RestAppProperty(restapi=self.restapi, server=self.server)
            
            # Fail to find the application: raises 404 NotFound
            with patch.object(Application, 'find', classmethod(mockDBObject.findFail)):
                yield self.assertFailure(resource.put(app.appeui), e.NotFound)
        
            # Property fails validity check: raises 400 BadRequest
            with patch.object(Application, 'find', classmethod(mockDBObject.findSuccess)), \
                patch.object(AppProperty, 'find', classmethod(mockDBObject.findSuccess)):
                prop.valid = MagicMock(return_value=(False, {}))
                yield self.assertFailure(resource.put(app.appeui), e.BadRequest)
            
                # Pass validity check, returns 200
                expected = ({}, 200)
                prop.valid = MagicMock(return_value=(True, {}))
                prop.update = MagicMock()
                result = yield resource.put(app.appeui)
                self.assertEqual(expected, result)

    @inlineCallbacks
    def test_delete(self):
        """Test delete method"""
        
        app = self._test_application()
        prop = self._test_appproperty()
        args = {'port': 11}
        
        with patch.object(reqparse.RequestParser, 'parse_args',
                          MagicMock(return_value=args)):
            resource = RestAppProperty(restapi=self.restapi, server=self.server)
            mockDBObject.return_value = prop
            
            # Fail to find the application: raises 404 NotFound
            with patch.object(Application, 'find', classmethod(mockDBObject.findFail)):
                yield self.assertFailure(resource.delete(app.appeui), e.NotFound)
            
            # Find and delete, returns 200
            with patch.object(Application, 'find', classmethod(mockDBObject.findSuccess)), \
                patch.object(AppProperty, 'find', classmethod(mockDBObject.findSuccess)):
                expected = ({}, 200)
                prop.delete = MagicMock()
                result = yield resource.delete(app.appeui)
                self.assertEqual(expected, result)

class RestAppPropertysTest(unittest.TestCase):
    """Test RestAppPropertys class"""
    
    def setUp(self):
        # Mock Registry
        Registry.getConfig =  MagicMock(return_value=None)
        
        # Initialise Database object to create relationships
        db = Database()
        db.register()
        
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
            id=1,
            appeui=int('0x0A0B0C0D0A0B0C0D', 16),
            name='app',
            domain='fluentnetworks.com.au',
            appnonce=int('0xC28AE9',16),
            appkey=int('0x017E151638AEC2A6ABF7258809CF4F3C',16),
            fport=15,
            )

    def _test_appproperty(self):
        """Create a test AppProperty object"""
        
        return AppProperty(id=22,
                           application_id=1,
                           port=15,
                           name='Temperature',
                           type='float',
                           )
    
    @inlineCallbacks
    def test_get(self):
        """Test get method"""
        
        app = self._test_application()
        prop = self._test_appproperty()

        with patch.object(reqparse.RequestParser, 'parse_args'):
            resource = RestAppPropertys(restapi=self.restapi, server=self.server)
            
            # Fail to any properties
            mockDBObject.return_value = app
            with patch.object(Application, 'find', classmethod(mockDBObject.findSuccess)), \
                patch.object(HasMany, 'get', MagicMock(return_value=[])):
                expected = {}
                result = yield resource.get(app.appeui)
                self.assertEqual(expected, result)
                
            with patch.object(Application, 'find', classmethod(mockDBObject.findSuccess)), \
                patch.object(HasMany, 'get', MagicMock(return_value=[prop, prop])):
                expected = (prop.port, 2)
                r = yield resource.get(app.appeui)
                result = (r[0]['port'], len(r))
                self.assertEqual(expected, result)

    @inlineCallbacks
    def test_post(self):
        """Test post method"""
        
        app = self._test_application()
        prop = self._test_appproperty()
        
        args = {'appeui': app.appeui}
        attrs = ['port', 'name', 'type']
        for a in attrs:
            args[a] = getattr(prop, a)
        
        # Remove a required arg - raises 400 BadRequest
        with patch.object(reqparse.RequestParser, 'parse_args',
                          MagicMock(return_value=args)):
            resource = RestAppPropertys(restapi=self.restapi,
                                        server=self.server)
            args['name'] = None
            yield self.assertFailure(resource.post(), e.BadRequest)
            args['name'] = app.name

        # Property exists - raises 400 BadRequest
        mockDBObject.return_value = app
        with patch.object(reqparse.RequestParser, 'parse_args',
                          MagicMock(return_value=args)), \
                patch.object(Application, 'find',
                              classmethod(mockDBObject.findSuccess)), \
                patch.object(AppProperty, 'exists',
                             MagicMock(return_value=True)):
            resource = RestAppPropertys(restapi=self.restapi,
                                        server=self.server)
            yield self.assertFailure(resource.post(), e.BadRequest)
            
        # Invalid property - raises 400 BadRequest
        with patch.object(reqparse.RequestParser, 'parse_args',
                          MagicMock(return_value=args)), \
                patch.object(Application, 'find',
                              classmethod(mockDBObject.findSuccess)), \
                patch.object(AppProperty, 'exists',
                             MagicMock(return_value=False)), \
                patch.object(AppProperty, 'valid',
                             MagicMock(return_value=(False, {}))):
            resource = RestAppPropertys(restapi=self.restapi,
                                        server=self.server)
            yield self.assertFailure(resource.post(), e.BadRequest)

        # Valid post - returns 201 with location
        with patch.object(reqparse.RequestParser, 'parse_args',
                          MagicMock(return_value=args)), \
                patch.object(Application, 'find',
                              classmethod(mockDBObject.findSuccess)), \
                patch.object(AppProperty, 'exists', MagicMock(return_value=None)), \
                patch.object(AppProperty, 'valid', MagicMock(return_value=(True, {}))), \
                patch.object(AppProperty, 'save',  MagicMock(return_value=prop)):
            resource = RestAppPropertys(restapi=self.restapi, server=self.server)
            expected = ({}, 201, {'Location':
                self.restapi.api.prefix + '/property/' + str(prop.id)})
            result = yield resource.post()
            self.assertEqual(expected, result)
