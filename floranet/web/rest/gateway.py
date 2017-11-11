import ipaddress

from flask_restful import Resource, reqparse, abort, inputs, fields, marshal
from flask_login import login_required
from twisted.internet.defer import inlineCallbacks, returnValue
from crochet import wait_for, TimeoutError

from floranet.models.gateway import Gateway
from floranet.log import log

# Crochet timeout. If the code block does not complete within this time,
# a TimeoutError exception is raised.
from __init__ import TIMEOUT

class GatewayResource(Resource):
    """Gateway resource base class.
    
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
            'host': fields.String,
            'eui': fields.Integer,
            'name': fields.String,
            'enabled': fields.Boolean,
            'power': fields.Integer,
            'created': fields.DateTime(dt_format='iso8601'),
            'updated': fields.DateTime(dt_format='iso8601')
        }
        self.parser = reqparse.RequestParser(bundle_errors=True)
        self.parser.add_argument('host', type=str)
        self.parser.add_argument('eui', type=int)
        self.parser.add_argument('name', type=str)
        self.parser.add_argument('enabled', type=inputs.boolean)
        self.parser.add_argument('power', type=int)
        self.args = self.parser.parse_args()
            
class RestGateway(GatewayResource):
    """RestGateway Resource class.
    
    Manages RESTAPI GET and PUT transactions for gateways.
    
    """
    def __init__(self, **kwargs):
        super(RestGateway, self).__init__(**kwargs)
        
    @login_required
    @wait_for(timeout=TIMEOUT)
    @inlineCallbacks
    def get(self, host):
        """Method to handle gateway GET requests"""  
        try:
            g = yield Gateway.find(where=['host = ?', host], limit=1)
            # Return a 404 if not found.
            if g is None:
                abort(404, message={'error': "Gateway {} doesn't exist.".format(host)})
            returnValue(marshal(g, self.fields))
            
        except TimeoutError:
            log.error("REST API timeout retrieving gateway {host}",
                      host=host)

    @login_required
    @wait_for(timeout=TIMEOUT)
    @inlineCallbacks
    def put(self, host):
        """Method to handle gateway PUT requests
        
        Args:
            host (str): Gateway host address
        """
        try:
            gateway = yield Gateway.find(where=['host = ?', host], limit=1)
            # Return a 404 if not found.
            if gateway is None:
                abort(404, message={'error': "Gateway {} doesn't exist".format(host)})

            kwargs = {}
            for a,v in self.args.items():
                if v is not None and v != getattr(gateway, a):
                    kwargs[a] = v
                    setattr(gateway, a, v)
            (valid, message) = yield gateway.valid()
            if not valid:
                abort(400, message=message)
            
            # Update the gateway and server with the new attributes
            if kwargs:
                gateway.update(**kwargs)
                self.server.lora.updateGateway(host, gateway)
            returnValue(({}, 200))

        except TimeoutError:
            log.error("REST API timeout retrieving gateway {host}",
                      host=host)

    @login_required
    @wait_for(timeout=TIMEOUT)
    @inlineCallbacks
    def delete(self, host):
        """Method to handle gateway DELETE requests
        
        Args:
            host (str): Gateway host
        """
        try:
            g = yield Gateway.find(where=['host = ?', host], limit=1)
            # Return a 404 if not found.
            if g is None:
                abort(404, message={'error': "Gateway {} doesn't exist.".format(host)})
            deleted = yield g.delete()
            self.server.lora.deleteGateway(g)
            returnValue(({}, 200))

        except TimeoutError:
            log.error("REST API timeout retrieving gateway {host}",
                      host=host)

class RestGateways(GatewayResource):
    """ RestGateways Resource class.
    
    Manages REST API GET and POST transactions for reading multiple gateways,
    and creating gateways.
    
    """
    def __init__(self, **kwargs):
        super(RestGateways, self).__init__(**kwargs)
        
    @login_required
    @wait_for(timeout=TIMEOUT)
    @inlineCallbacks
    def get(self):
        """Method to get all gateways"""
        try:
            gateways = yield Gateway.all()
            if gateways is None:
                returnValue({})
            data = {}
            for i,g in enumerate(gateways):
                data[i] = marshal(g, self.fields)
            returnValue(data)
            
        except TimeoutError:
            # Exception returns 500 to client
            log.error("REST API timeout retrieving all gateways")


    @login_required
    @wait_for(timeout=TIMEOUT)
    @inlineCallbacks
    def post(self):
        """Method to create a gateway"""
        host = self.args['host']
        name = self.args['name']
        eui = self.args['eui']
        enabled = self.args['enabled']
        power = self.args['power']
        
        message = {}
        # Check for required args
        required = {'host', 'name', 'eui', 'enabled', 'power'}
        for r in required:
            if self.args[r] is None:
                message[r] = "Missing the {} parameter.".format(r)
        if message:
            abort(400, message=message)
            
        # Ensure we have a valid address
        try:
            ipaddress.ip_address(host)
        except (ipaddress.AddressValueError, ValueError):
            message = {'error': "Invalid IP address {} ".format(host)}
            abort(400, message=message)
            
        # Ensure we have a valid EUI
        if not isinstance(eui, (int, long)):
            message = {'error': "Invalid gateway EUI {} ".format(eui)}
            abort(400, message=message)

        # Check this gateway does not currently exist
        exists = yield Gateway.exists(where=['host = ?', host])
        if exists:
            message = {'error': "Gateway address {} ".format(host) + \
                                 "currently exists."}
            abort(400, message=message)

        # Check the EUI does not currently exist
        exists = yield Gateway.exists(where=['eui = ?', eui])
        if exists:
            message = {'error': "Gateway EUI {} ".format(eui) + \
                                 "currently exists."}
            abort(400, message=message)

        # Create and validate
        gateway = Gateway(host=host, eui=eui, name=name, enabled=enabled, power=power)
        (valid, message) = gateway.valid()
        if not valid:
            abort(400, message=message)

        try:
            g = yield gateway.save()
            if g is None:
                abort(500, message={'error': "Error saving the gateway."})
            # Add the new gateway to the server.
            self.server.lora.addGateway(g)
            location = self.restapi.api.prefix + '/gateway/' + str(host)
            returnValue(({}, 201, {'Location': location}))
        except TimeoutError:
            # Exception returns 500 to client
            log.error("REST API timeout for gateway POST request")


