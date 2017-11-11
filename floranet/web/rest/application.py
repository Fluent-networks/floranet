import ipaddress

from flask_restful import Resource, reqparse, abort, inputs, fields, marshal
from flask_login import login_required
from twisted.internet.defer import inlineCallbacks, returnValue
from crochet import wait_for, TimeoutError

from floranet.models.application import Application
from floranet.models.device import Device
from floranet.util import euiString, intHexString
from floranet.log import log

# Crochet timeout. If the code block does not complete within this time,
# a TimeoutError exception is raised.
from __init__ import TIMEOUT

class ApplicationResource(Resource):
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
            'appeui': fields.Integer,
            'name': fields.String,
            'domain': fields.String,
            'appnonce': fields.Integer,
            'appkey': fields.Integer,
            'fport': fields.Integer,
            'appinterface_id': fields.Integer,
            'properties': {},
            'created': fields.DateTime(dt_format='iso8601'),
            'updated': fields.DateTime(dt_format='iso8601')
        }
        self.pfields = {
            'port': fields.Integer,
            'name': fields.String,
            'type': fields.String,
            'created': fields.DateTime(dt_format='iso8601'),
            'updated': fields.DateTime(dt_format='iso8601')
        }
        self.parser = reqparse.RequestParser(bundle_errors=True)
        self.parser.add_argument('appeui', type=int)
        self.parser.add_argument('name', type=str)
        self.parser.add_argument('domain', type=str)
        self.parser.add_argument('appnonce', type=int)
        self.parser.add_argument('appkey', type=int)
        self.parser.add_argument('fport', type=int)
        self.parser.add_argument('appinterface_id', type=int)
        self.args = self.parser.parse_args()
    
    @inlineCallbacks
    def getProperties(self, app):
        """Get and marshal the application properties"""
        
        # Get the properties
        props = yield app.properties.get()
        
        # Marshal
        data = {}
        for i,p in enumerate(props):
            data[i] = marshal(p, self.pfields)
            
        returnValue(data)
            
class RestApplication(ApplicationResource):
    """RestApplication Resource class.
    
    Manages RESTAPI GET and PUT transactions for applications.
    
    """
    def __init__(self, **kwargs):
        super(RestApplication, self).__init__(**kwargs)
        
    @login_required
    @wait_for(timeout=TIMEOUT)
    @inlineCallbacks
    def get(self, appeui):
        """Method to handle application GET requests
        
        Args:
            appeui (int): Application EUI
        """
        try:
            a = yield Application.find(where=['appeui = ?', appeui], limit=1)
            # Return a 404 if not found.
            if a is None:
                abort(404, message={'error': "Application {} doesn't exist."
                                    .format(euiString(appeui))})
            
            data = marshal(a, self.fields)
            data['properties'] = yield self.getProperties(a)
            returnValue(data)
            
        except TimeoutError:
            log.error("REST API timeout retrieving application {appeui}",
                      appeui=euiString(appeui))

    @login_required
    @wait_for(timeout=TIMEOUT)
    @inlineCallbacks
    def put(self, appeui):
        """Method to handle application PUT requests
        
        Args:
            appeui (int): Application EUI
        """
        try:
            app = yield Application.find(where=['appeui = ?', appeui], limit=1)
            # Return a 404 if not found.
            if app is None:
                abort(404, message={'error': "Application {} doesn't exist."
                                    .format(euiString(appeui))})
            
            kwargs = {}
            for a,v in self.args.items():
                if v is not None and v != getattr(app, a):
                    kwargs[a] = v
                    setattr(app, a, v)
            (valid, message) = yield app.valid()
            if not valid:
                abort(400, message=message)
            
            # Update the model
            if kwargs:
                app.update(**kwargs)
            returnValue(({}, 200))

        except TimeoutError:
            log.error("REST API timeout retrieving application {appeui}",
                      appeui=euiString(appeui))

    @login_required
    @wait_for(timeout=TIMEOUT)
    @inlineCallbacks
    def delete(self, appeui):
        """Method to handle application DELETE requests
        
        Args:
            appeui (int): Application EUI
        """
        
        try:
            # Check that no devices exist with this AppEUI.
            devices = yield Device.find(where=['appeui = ?', appeui], limit=1)
            if devices is not None:
                abort(400, message={'error': "Cannot delete - devices exist " \
                    "with Application EUI {}".format(euiString(appeui))})
            
            # Return a 404 if not found.            
            app = yield Application.find(where=['appeui = ?', appeui], limit=1)
            if app is None:
                abort(404, message={'error': "Application {} doesn't exist."
                                    .format(euiString(appeui))})
            yield app.delete()
            returnValue(({}, 200))

        except TimeoutError:
            log.error("REST API timeout retrieving application {appeui}",
                      appeui=euiString(appeui))

class RestApplications(ApplicationResource):
    """RestApplications Resource class.
    
    Manages REST API GET and POST transactions for reading multiple
    applications, and creating applications.
    
    """
    def __init__(self, **kwargs):
        super(RestApplications, self).__init__(**kwargs)
        
    @login_required
    @wait_for(timeout=TIMEOUT)
    @inlineCallbacks
    def get(self):
        """Method to get all applications"""
        try:
            apps = yield Application.all()
            if apps is None:
                returnValue({})
            data = {}
            for i,a in enumerate(apps):
                data[i] = marshal(a, self.fields)
                data[i]['properties'] = yield self.getProperties(a)
            returnValue(data)
            
        except TimeoutError:
            log.error("REST API timeout retrieving application {appeui}",
                      appeui=euiString(appeui))


    @login_required
    @wait_for(timeout=TIMEOUT)
    @inlineCallbacks
    def post(self):
        """Method to create an application"""
        appeui = self.args['appeui']
        name = self.args['name']
        domain = self.args['domain']
        appnonce = self.args['appnonce']
        appkey = self.args['appkey']
        fport = self.args['fport']
        appinterface_id = self.args['appinterface_id']
        
        message = {}
        # Check for required args
        required = {'appeui', 'name', 'appnonce', 'appkey', 'fport'}
        for r in required:
            if self.args[r] is None:
                message[r] = "Missing the {} parameter.".format(r)
        if message:
            abort(400, message=message)
            
        # Check this application does not currently exist
        exists = yield Application.exists(where=['appeui = ?', appeui])
        if exists:
            message = {'error': "Application EUI {} currently exists"
                       .format(euiString(appeui))}
            abort(400, message=message)

        # Check the appkey doesn't exist
        exists = yield Application.exists(where=['appkey = ?', appkey])
        if exists:
            message = {'error': "Application key {} currently exists".
                       format(intHexString(appkey,16))}
            abort(400, message=message)

        # Create and validate
        app = Application(appeui=appeui, name=name, domain=domain,
                          appnonce=appnonce, appkey=appkey,
                          fport=fport, appinterface_id=appinterface_id)
        (valid, message) = yield app.valid()
        if not valid:
            abort(400, message=message)

        try:
            a = yield app.save()
            if a is None:
                abort(500, message={'error': "Error saving the application."})
            location = self.restapi.api.prefix + '/app/' + str(appeui)
            returnValue(({}, 201, {'Location': location}))
            
        except TimeoutError:
            # Exception returns 500 to client
            log.error("REST API timeout for application POST request")


