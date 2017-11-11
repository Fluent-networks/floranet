import ipaddress

from flask_restful import Resource, reqparse, abort, inputs, fields, marshal
from flask_login import login_required
from twisted.internet.defer import inlineCallbacks, returnValue
from crochet import wait_for, TimeoutError

from floranet.models.config import Config
from floranet.log import log

# Crochet timeout. If the code block does not complete within this time,
# a TimeoutError exception is raised.
from __init__ import TIMEOUT

class RestSystem(Resource):
    """System configuration resource base class.
    
    Attributes:
        restapi (RestApi): Flask Restful API object
        server (NetServer): FloraNet network server object
        fields (dict): Dictionary of attributes to be returned to a REST request
        parser (RequestParser): Flask RESTful request parser
        args (dict): Parsed request argument
    """
        
    def __init__(self, **kwargs):
        self.restapi = kwargs['restapi']
        self.server = kwargs['server']
        self.fields = {
            'name': fields.String,
            'listen': fields.String,
            'port': fields.Integer,
            'webport': fields.Integer,
            'apitoken': fields.String,
            'freqband': fields.String,
            'netid': fields.Integer,
            'duplicateperiod': fields.Integer,
            'fcrelaxed': fields.Boolean,
            'otaastart': fields.Integer,
            'otaaend':  fields.Integer,
            'macqueueing': fields.Boolean,
            'macqueuelimit': fields.Integer,
            'adrenable': fields.Boolean,
            'adrmargin': fields.Float,
            'adrcycletime': fields.Integer,
            'adrmessagetime': fields.Integer,
        }
        self.parser = reqparse.RequestParser(bundle_errors=True)
        self.parser.add_argument('name', type=str)
        self.parser.add_argument('listen', type=str)
        self.parser.add_argument('port', type=int)
        self.parser.add_argument('webport', type=int)
        self.parser.add_argument('apitoken', type=str)
        self.parser.add_argument('freqband', type=str)
        self.parser.add_argument('netid', type=int)
        self.parser.add_argument('duplicateperiod', type=int)
        self.parser.add_argument('fcrelaxed', type=bool)
        self.parser.add_argument('otaastart', type=int)
        self.parser.add_argument('otaaend', type=int)
        self.parser.add_argument('macqueuing', type=bool)
        self.parser.add_argument('macqueuelimit', type=int)
        self.parser.add_argument('adrenable', type=bool)
        self.parser.add_argument('adrmargin', type=float)
        self.parser.add_argument('adrcycletime', type=int)
        self.parser.add_argument('adrmessagetime', type=int)
        self.args = self.parser.parse_args()
                            
    @login_required
    @wait_for(timeout=TIMEOUT)
    @inlineCallbacks
    def get(self):
        """Method to handle system configuration GET requests"""
        try:
            config = yield Config.find(limit=1)
            # Return a 404 if not found.
            if config is None:
                abort(404, message={'error': "Could not get the system configuration"})
            returnValue(marshal(config, self.fields))
            
        except TimeoutError:
            log.error("REST API timeout retrieving application {appeui}",
                      appeui=euiString(appeui))

    @login_required
    @wait_for(timeout=TIMEOUT)
    @inlineCallbacks
    def put(self):
        """Method to handle system configuration PUT requests
        
        Args:
            appeui (int): Application EUI
        """
        try:
            config = yield Config.find(limit=1)
            # Return a 404 if not found.
            if config is None:
                abort(404, message={'error': "Could not get the system configuration"})
            
            # Filter args
            params = {k: v for k, v in self.args.iteritems() if v is not None}
            
            # Set the new attributes
            for a,v in params.items():
                setattr(config, a, v)

            # Validate the configuration
            (valid, message) = config.check()
            if not valid:
                abort(400, message=message)                
            
            # Reload the config
            (success, message) = self.server.reload(config)
            if not success:
                abort(500, message=message)                
            
            yield config.save()
            returnValue(({}, 200))

        except TimeoutError:
            log.error("REST API timeout retrieving application {appeui}",
                      appeui=euiString(appeui))


        except TimeoutError:
            log.error("REST API timeout retrieving application {appeui}",
                      appeui=euiString(appeui))

