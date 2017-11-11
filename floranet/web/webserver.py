from twisted.internet import reactor
from twisted.web.wsgi import WSGIResource
from twisted.web.server import Site
from twisted.internet.defer import inlineCallbacks, returnValue

from flask import Flask
from flask_login import LoginManager, UserMixin
from crochet import no_setup

from floranet.web.rest.restapi import RestApi
from floranet.log import log

no_setup()

class WebServer(object):
    """Webserver class.
        
    Attributes:
        app (Flask): Flask app instance
        site (Site): Twisted web site
        port (Port): Twisted UDP port
        api (RestApi): Rest API instance
        login (LoginManager): Flask login manager
    """
    def __init__(self, server):
        """Initialize the web server.
        
        Args:
            server: NetServer object      
        """
        self.server = server
        self.port = None
        
        # Create Flask app and configure
        self.app = Flask(__name__)
        self.app.config['ERROR_404_HELP'] = False

        # Create REST API instance
        self.restapi = RestApi(self.app, self.server)

        # Create LoginManager instance and configure
        self.login = LoginManager()
        self.login.init_app(self.app)
        self.login.request_loader(self.load_user)
        
    def start(self):
        """Start the Web Server """
        self.site = Site(WSGIResource(reactor, reactor.getThreadPool(), self.app))
        self.port = reactor.listenTCP(self.server.config.webport, self.site)

    @inlineCallbacks
    def restart(self):
        """Restart the web server"""
        yield self.port.stopListening()
        self.port = reactor.listenTCP(self.server.config.webport, self.site)
        
    def load_user(self, request):
        """Flask login request_loader callback.
        
        The expected behavior is to return a User instance if
        the provided credentials are valid, and return None
        otherwise.
        
        Args:
            request (request): Flask request object
            
        Returns:
            User object on success, otherwise None
        """
        # Get the token as Authorisation header or JSON parameter
        token = request.headers.get('Authorization')
        if token is None:
            data = request.get_json()
            if data is None:
                return None
            token = data['token'] if 'token' in data else None

        # Verify the token
        if token is not None:
            if token.encode('utf8') == self.server.config.apitoken:
                return User('api', None)

        return None

class User(UserMixin):
    """Proxy class to return for token verification"""
    
    def __init__(self, username, password):
        self.id = username
        self.password = password

