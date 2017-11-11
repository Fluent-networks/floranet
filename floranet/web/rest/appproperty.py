import ipaddress

from flask_restful import Resource, reqparse, abort, inputs, fields, marshal
from flask_login import login_required
from twisted.internet.defer import inlineCallbacks, returnValue
from crochet import wait_for, TimeoutError

from floranet.models.application import Application
from floranet.models.appproperty import AppProperty
from floranet.util import euiString, intHexString
from floranet.log import log

# Crochet timeout. If the code block does not complete within this time,
# a TimeoutError exception is raised.
from __init__ import TIMEOUT

class AppPropertyResource(Resource):
    """Application resource base class.
    
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
            'port': fields.Integer,
            'name': fields.String,
            'type': fields.String,
            'created': fields.DateTime(dt_format='iso8601'),
            'updated': fields.DateTime(dt_format='iso8601')
        }
        self.parser = reqparse.RequestParser(bundle_errors=True)
        self.parser.add_argument('appeui', type=int)
        self.parser.add_argument('port', type=int)
        self.parser.add_argument('name', type=str)
        self.parser.add_argument('type', type=str)
        self.args = self.parser.parse_args()
            
class RestAppProperty(AppPropertyResource):
    """RestAppProperty Resource class.
    
    Manages RESTAPI GET and PUT transactions for applicaiton
    properties.
    
    """
    def __init__(self, **kwargs):
        super(RestAppProperty, self).__init__(**kwargs)
        
    @login_required
    @wait_for(timeout=TIMEOUT)
    @inlineCallbacks
    def get(self, appeui):
        """Method to handle application property GET requests
        
        Args:
            appeui (int): Application EUI
            port (int): Application property port
        """
        try:
            app = yield Application.find(where=['appeui = ?', appeui], limit=1)
            # Return a 404 if not found.
            if app is None:
                abort(404, message={'error': "Application {} doesn't exist."
                                    .format(euiString(appeui))})
            
            port = self.args['port']
            p = yield AppProperty.find(where=['application_id = ? AND port = ?',
                                             app.id, port])
            if p is None:
                 abort(404, message={'error': "Application property doesn't exist."})
            
            data = marshal(p, self.fields)
            returnValue(data)
            
        except TimeoutError:
            log.error("REST API timeout get request for application {appeui} "
                      "property {port}", appeui=euiString(appeui), port=port)

    @login_required
    @wait_for(timeout=TIMEOUT)
    @inlineCallbacks
    def put(self, appeui):
        """Method to handle application property PUT requests
        
        Args:
            appeui (int): Application EUI
        """
        try:
            app = yield Application.find(where=['appeui = ?', appeui], limit=1)
            # Return a 404 if not found.
            if app is None:
                abort(404, message={'error': "Application {} doesn't exist."
                                    .format(euiString(appeui))})
            port = self.args['port']
            
            p = yield AppProperty.find(where=['application_id = ? AND port = ?',
                                             app.id, port], limit=1)
            if p is None:
                 abort(404, message={'error': "Application property doesn't exist."})
            
            kwargs = {}
            for a,v in self.args.items():
                if a not in {'name', 'type', 'port'}:
                    continue
                if v is not None and v != getattr(p, a):
                    kwargs[a] = v
                    setattr(p, a, v)
            (valid, message) = yield p.valid()
            if not valid:
                abort(400, message=message)
            
            # Update the model
            if kwargs:
                p.update(**kwargs)
            returnValue(({}, 200))

        except TimeoutError:
            log.error("REST API timeout put request for application {appeui} "
                      "property {port}", appeui=euiString(appeui), port=port)

    @login_required
    @wait_for(timeout=TIMEOUT)
    @inlineCallbacks
    def delete(self, appeui):
        """Method to handle application property DELETE requests
        
        Args:
            appeui (int): application EUI
        """
        
        try:
            # Return a 404 if the application is not found.            
            app = yield Application.find(where=['appeui = ?', appeui], limit=1)
            if app is None:
                abort(404, message={'error': "Application {} doesn't exist."
                                    .format(euiString(appeui))})
            port = self.args['port']
            
            # Return a 404 if the property is not found. 
            p = yield AppProperty.find(where=['application_id = ? AND port = ?',
                                             app.id, port], limit=1)
            if p is None:
                 abort(404, message={'error': "Application property doesn't exist."})
            
            yield p.delete()
            returnValue(({}, 200))

        except TimeoutError:
            log.error("REST API timeout retrieving application {appeui} "
                      "property {port}", appeui=euiString(appeui), port=port)

class RestAppPropertys(AppPropertyResource):
    """RestAppPropertys Resource class.
    
    Manages REST API GET and POST transactions for reading multiple
    application properties, and creating properties.
    
    """
    def __init__(self, **kwargs):
        super(RestAppPropertys, self).__init__(**kwargs)
        
    @login_required
    @wait_for(timeout=TIMEOUT)
    @inlineCallbacks
    def get(self, appeui):
        """Method to get all app properties"""
        try:
            
            # Return a 404 if the application is not found.            
            app = yield Application.find(where=['appeui = ?', appeui], limit=1)
            if app is None:
                abort(404, message={'error': "Application {} doesn't exist."
                                    .format(euiString(appeui))})
                
            # Get the properties
            properties = yield app.properties.get()
            if properties is None:
                returnValue({})
            
            data = {}
            for i,p in enumerate(properties):
                data[i] = marshal(p, self.fields)
            returnValue(data)
            
        except TimeoutError:
            log.error("REST API timeout retrieving application {appeui} "
                      "properties", appeui=euiString(appeui))


    @login_required
    @wait_for(timeout=TIMEOUT)
    @inlineCallbacks
    def post(self):
        """Method to create an application property"""
        appeui = self.args['appeui']
        port = self.args['port']
        name = self.args['name']
        type = self.args['type']
        
        message = {}
        # Check for required args
        required = {'appeui', 'port', 'name', 'type'}
        for r in required:
            if self.args[r] is None:
                message[r] = "Missing the {} parameter.".format(r)
        if message:
            abort(400, message=message)

        # Return a 404 if the application is not found.            
        app = yield Application.find(where=['appeui = ?', appeui], limit=1)
        if app is None:
            abort(404, message={'error': "Application {} doesn't exist."
                                .format(euiString(appeui))})

        # Check this property does not currently exist
        exists = yield AppProperty.exists(where=['application_id = ? AND port = ?',
                                              app.id, port])
        if exists:
            message = {'error': "Application property for appeui {}, port "
                       "{} exists".format(euiString(appeui), port)}
            abort(400, message=message)

        # Create and validate
        p = AppProperty(application_id=app.id, port=port, name=name, type=type)
        
        (valid, message) = yield p.valid()
        if not valid:
            abort(400, message=message)

        try:
            prop = yield p.save()
            if prop is None:
                abort(500, message={'error': "Error saving the property."})
            location = self.restapi.api.prefix + '/property/' + str(prop.id)
            returnValue(({}, 201, {'Location': location}))
            
        except TimeoutError:
            log.error("REST API timeout post application {appeui} "
                      "property {port}", appeui=euiString(appeui), port=port)


