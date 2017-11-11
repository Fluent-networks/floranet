import os
import json

from twisted.trial import unittest
from mock import patch, MagicMock

from twisted.internet.defer import inlineCallbacks

from flask import Flask, Request
from flask_restful import Api, Resource
from werkzeug.test import EnvironBuilder
from twistar.registry import Registry

from floranet.models.config import Config
from floranet.models.model import Model
from floranet.netserver import NetServer
from floranet.web.webserver import WebServer

class WebServerTest(unittest.TestCase):
    
    @inlineCallbacks
    def setUp(self):
        """Test setup.
        """
        Registry.getConfig =  MagicMock(return_value=None)
        
        # Get factory default configuration
        with patch.object(Model, 'save', MagicMock()):
            config = yield Config.loadFactoryDefaults()
            
        self.server = NetServer(config)
        self.webserver = WebServer(self.server)
    
    def test_load_user(self):
        """Test load_user method"""
        
        # Since request objects are immutable, we create
        # a request object with mutable values
        class TestRequest(object):
            
            def __init__(self, method, path, headers, data):
                self.method = method
                self.path = path
                self.headers = headers
                self.data = data
        
            def get_json(self):
                return self.data
            
        # Test JSON authorization
        request = TestRequest('GET', '',
                              {'content-type': 'application/json'},
                              { 'token': self.server.config.apitoken })
        result = self.webserver.load_user(request)

        self.assertTrue(result is not None)        
        
        # Test JSON authorization failure
        request.data['token'] = ''
        
        result = self.webserver.load_user(request)

        self.assertTrue(result is None)   

        # Test header authorization
        request.headers['Authorization'] = self.server.config.apitoken
        
        result = self.webserver.load_user(request)
        
        self.assertTrue(result is not None)
        
        # Test header authorization failure
        request.headers['Authorization'] = ''
        
        result = self.webserver.load_user(request)

        self.assertTrue(result is None)

        
        

            
        

        
    