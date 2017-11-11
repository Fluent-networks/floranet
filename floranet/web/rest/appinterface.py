import ipaddress

from flask_restful import Resource, reqparse, abort, inputs, fields, marshal
from flask_login import login_required
from twisted.internet.defer import inlineCallbacks, returnValue
from crochet import wait_for, TimeoutError

from floranet.models.appinterface import AppInterface
from floranet.appserver.azure_iot_https import AzureIotHttps
from floranet.appserver.reflector import Reflector
from floranet.imanager import interfaceManager
from floranet.util import euiString, intHexString
from floranet.log import log

# Crochet timeout. If the code block does not complete within this time,
# a TimeoutError exception is raised.
from __init__ import TIMEOUT

class AppInterfaceResource(Resource):
    """Application interface resource base class.
    
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
            'appif': fields.Integer,
            'name': fields.String,
        }
        self.parser = reqparse.RequestParser(bundle_errors=True)
        self.parser.add_argument('type', type=str)
        self.parser.add_argument('name', type=str)
        self.parser.add_argument('protocol', type=str)
        self.parser.add_argument('iothost', type=str)
        self.parser.add_argument('keyname', type=str)
        self.parser.add_argument('keyvalue', type=str)
        self.parser.add_argument('pollinterval', type=int)
        self.args = self.parser.parse_args()    

class RestAppInterface(AppInterfaceResource):
    """RestAppInterface Resource class
    
    Manages REST API GET PUT and DELETE transactions
    for application interfaces.
    
    """
        
    def __init__(self, **kwargs):
        super(RestAppInterface, self).__init__(**kwargs)

    @login_required
    @wait_for(timeout=TIMEOUT)
    @inlineCallbacks
    def get(self, appinterface_id):
        """Method to handle application GET requests
        
        Args:
            appinterface_id (int): Application Interface ID
        """
        try:
            interface = interfaceManager.getInterface(appinterface_id)
            # Return a 404 if not found.
            if interface is None:
                abort(404, message={'error': "Application interface id {} "
                            "doesn't exist.".format(str(appinterface_id))})
            
            # Return the interface's marshalled attributes
            returnValue(interface.marshal())
            yield
            
        except TimeoutError:
            log.error("REST API timeout retrieving application interface "
                      "{id}", id=appinterface_id)

    @login_required
    @wait_for(timeout=TIMEOUT)
    @inlineCallbacks
    def put(self, appinterface_id):
        """Method to handle AppInterface PUT requests
        
        Args:
            appinterface_id (int): Application Interface ID
        """
        try:
            interface = interfaceManager.getInterface(appinterface_id)
            # Return a 404 if not found.
            if interface is None:
                abort(404, message={'error': "Application interface id {} "
                                    "doesn't exist.".format(str(appinterface_id))})

            kwargs = {}
            for a,v in self.args.items():
                if hasattr(interface, a) and v is not None and v != getattr(interface, a):
                    kwargs[a] = v
                    setattr(interface, a, v)
            (valid, message) = yield interface.valid()
            if not valid:
                abort(400, message=message)
            
            # Update the interface via interfaceManager
            if kwargs:
                yield interfaceManager.updateInterface(interface)
            returnValue(({}, 200))
            
        except TimeoutError:
            log.error("REST API timeout retrieving application interface "
                      "{id}", id=appinterface_id)

    @login_required
    @wait_for(timeout=TIMEOUT)
    @inlineCallbacks
    def delete(self, appinterface_id):
        """Method to handle AppInterface DELETE requests
        
        Args:
            appinterface_id (int): Application inetrface id
        """
        
        try:
            # Check that no interfaces exist with this interface_id.
            interface = yield interfaceManager.getInterface(appinterface_id)
            if interface is None:
                abort(404, message={'error': "Interface {} doesn't exist."
                                    .format(str(appinterface_id))})

            # Delete the interface via interfaceManager
            yield interfaceManager.deleteInterface(interface)
            returnValue(({}, 200))

        except TimeoutError:
            log.error("REST API timeout retrieving application interface "
                      "{id}", id=appinterface_id)

class RestAppInterfaces(AppInterfaceResource):
    """RestAppInterfaces Resource class.
    
    Manages REST API GET and POST transactions for reading multiple
    application interfaces and creating interfaces.
    
    """
    def __init__(self, **kwargs):
        super(RestAppInterfaces, self).__init__(**kwargs)
        
    @login_required
    @wait_for(timeout=TIMEOUT)
    @inlineCallbacks
    def get(self):
        """Method to get all application interfaces"""
        try:
            interfaces = interfaceManager.getAllInterfaces()
            if interfaces is None:
                returnValue({})
            marshal_fields = {
                'type': fields.String(attribute='__class__.__name__'),
                'id': fields.Integer(attribute='appinterface.id'),
                'name': fields.String
            }
            data = {}
            for i,interface in enumerate(interfaces):
                data[i] = marshal(interface, marshal_fields)
            returnValue(data)
            yield
            
        except TimeoutError:
            log.error("REST API timeout retrieving application interfaces")


    @login_required
    @wait_for(timeout=TIMEOUT)
    @inlineCallbacks
    def post(self):
        """Method to create an Application Interface"""
        klass = self.args['type']
        name = self.args['name']

        message = {}
        
        try:
            
            if klass == 'azure':        
                protocol = self.args['protocol']
                iothost = self.args['iothost']
                keyname = self.args['keyname']
                keyvalue = self.args['keyvalue']
                poll_interval = self.args['pollinterval']
            
                # Check for required args
                required = {'type', 'name', 'protocol', 'iothost',
                            'keyname', 'keyvalue', 'pollinterval'}
                for r in required:
                    if self.args[r] is None:
                        message[r] = "Missing the {} parameter.".format(r)
                if message:
                    abort(400, message=message)
                
                if protocol != 'https':
                    message = "Unknown protocol type {}.".format(protocol)
                    abort(400, message=message)
                    
                # Check this interface does not currently exist
                exists = yield AzureIotHttps.exists(where=['name = ?', name])
                if exists:
                    message = {'error': "Azure Https Interface {} currently exists"
                               .format(name)}
                    abort(400, message=message)
            
                # Create the interface
                interface = AzureIotHttps(name=name, iothost=iothost, keyname=keyname,
                                  keyvalue=keyvalue, poll_interval=poll_interval)
            
            elif klass == 'reflector':
                
                # Required args
                required = {'type', 'name'}
                for r in required:
                    if self.args[r] is None:
                        message[r] = "Missing the {} parameter.".format(r)
                if message:
                    abort(400, message=message)
                
                # Create the interface
                interface = Reflector(name=name)            
            
            else:
                message = {'error': "Unknown interface type"}
                abort(400, message=message)
            
            (valid, message) = yield interface.valid()
            if not valid:
                abort(400, message=message)

            # Add the new interface
            id = interfaceManager.createInterface(interface)
            location = self.restapi.api.prefix + '/interface/' + str(id)
            returnValue(({}, 201, {'Location': location}))
            
        except TimeoutError:
            # Exception returns 500 to client
            log.error("REST API timeout for application interface POST request")


