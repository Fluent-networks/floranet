from flask_restful import Resource, reqparse, abort, inputs, fields, marshal
from flask_login import login_required
from twisted.internet.defer import inlineCallbacks, returnValue
from crochet import wait_for, TimeoutError

from floranet.models.device import Device
from floranet.util import euiString
from ...log import log

# Crochet timeout. If the code block does not complete within this time,
# a TimeoutError exception is raised.
from __init__ import TIMEOUT

class DeviceResource(Resource):
    """Device Resource base class.
    
    Attributes:
        restapi (RestApi): Flask Restful API object
        server (NetServer): FloraNet network server object
        fields (dict): Dictionary of attributes to be returned to a REST request
        parser (RequestParser): Flask RESTful request parser
        args (dict): Parsed request arguments
    """
    def __init__(self, **kwargs):
        self.restapi = kwargs['restapi']
        self.server = kwargs['server']
        self.fields = {
            'deveui': fields.Integer,
            'name': fields.String,
            'devclass': fields.String,
            'enabled': fields.Boolean,
            'otaa': fields.Boolean,
            'devaddr': fields.Integer,
            'appeui': fields.Integer,
            'appskey': fields.Integer,
            'nwkskey': fields.Integer,
            'tx_datr': fields.String,
            'snr_average': fields.Float,
            'appname': fields.String,
            'latitude': fields.Float,
            'longitude': fields.Float,
            'created': fields.DateTime(dt_format='iso8601'),
            'updated': fields.DateTime(dt_format='iso8601')
        }
        self.parser = reqparse.RequestParser(bundle_errors=True)
        self.parser.add_argument('deveui', type=int)
        self.parser.add_argument('name', type=str)
        self.parser.add_argument('devclass', type=str)
        self.parser.add_argument('enabled', type=inputs.boolean)
        self.parser.add_argument('otaa', type=inputs.boolean)
        self.parser.add_argument('devaddr', type=int)
        self.parser.add_argument('appeui', type=int)
        self.parser.add_argument('nwkskey', type=int)
        self.parser.add_argument('appskey', type=int)
        self.parser.add_argument('appname', type=str)
        self.parser.add_argument('latitude', type=float)
        self.parser.add_argument('longitude', type=float)
        self.args = self.parser.parse_args()
    
class RestDevice(DeviceResource):
    """RestDevice Resource class.
    
    Manages RESTAPI GET, PUT and DELETE transactions for a single device.
    """
    def __init__(self, **kwargs):
        super(RestDevice, self).__init__(**kwargs)

    @login_required
    @wait_for(timeout=TIMEOUT)
    @inlineCallbacks
    def get(self, deveui):
        """Method to handle device GET request
        
        Args:
            deveui (int): Device deveui
        """
        try:
            d = yield Device.find(where=['deveui = ?', deveui], limit=1)
            # Return a 404 if not found.
            if d is None:
               abort(404, message={'error': "Device {} doesn't exist".
                                   format(euiString(deveui))})
            returnValue(marshal(d, self.fields))

        except TimeoutError:
            log.error("REST API timeout for device GET request")

    @login_required
    @wait_for(timeout=TIMEOUT)
    @inlineCallbacks
    def put(self, deveui):
        """Method to handle device PUT requests
        
        Args:
            deveui (int): Device deveui
        """
        try:
            device = yield Device.find(where=['deveui = ?', deveui], limit=1)
            # Return a 404 if not found.
            if device is None:
                abort(404, message={'error': "Device {} doesn't exist".
                                    format(euiString(deveui))})
            
            kwargs = {}
            for a,v in self.args.items():
                if v is not None and v != getattr(device, a):
                    kwargs [a] = v
                    setattr(device, a, v)
            (valid, message) = yield device.valid(self.server)
            if not valid:
                abort(400, message=message)
            
            # Update the device with the new attributes
            if kwargs:
                device.update(**kwargs)
            returnValue(({}, 200))

        except TimeoutError:
            log.error("REST API timeout for device PUT request")

    @login_required
    @wait_for(timeout=TIMEOUT)
    @inlineCallbacks
    def delete(self, deveui):
        """Method to handle device DELETE requests
        
        Args:
            deveui (int): Device deveui
        """
        try:
            d = yield Device.find(where=['deveui = ?', deveui], limit=1)
            # Return a 404 if not found.
            if d is None:
                abort(404, message={'error': "Device {} doesn't exist".
                                    format(euiString(deveui))})
            deleted = yield d.delete()
            returnValue(({}, 200))

        except TimeoutError:
            log.error("REST API timeout for device DELETE request")

class RestDevices(DeviceResource):
    """ RestDevices Resource class.
    
    Manages REST API GET AND POST transactions for reading multiple devices,
    and creating devices.
    """
    def __init__(self, **kwargs):
        super(RestDevices, self).__init__(**kwargs)

    @login_required
    @wait_for(timeout=TIMEOUT)
    @inlineCallbacks
    def get(self):
        """Method to get all devices"""
        try:
            devices = yield Device.all()
            if devices is None:
                returnValue({})
            data = {}
            for i,d in enumerate(devices):
                data[i] = marshal(d, self.fields)
            returnValue(data)
            
        except TimeoutError:
            # Exception returns 500 to client
            log.error("REST API timeout retrieving all devices")

    @login_required
    @wait_for(timeout=TIMEOUT)
    @inlineCallbacks
    def post(self):
        """Method to create a device"""
        deveui = self.args['deveui']
        name = self.args['name']
        devclass = self.args['devclass']
        enabled = self.args['enabled']
        otaa = self.args['otaa']
        devaddr = self.args['devaddr']
        appeui = self.args['appeui']
        nwkskey = self.args['nwkskey']
        appskey = self.args['appskey']
        
        message = {}

        # Check for required args
        required = {'deveui', 'name', 'devclass', 'enabled',
                    'otaa', 'appeui', 'devaddr', 'nwkskey', 'appskey'}
        for r in required:
            if otaa is True:
                if r in {'devaddr', 'nwkskey', 'appskey'}:
                    continue
            if self.args[r] is None:
                message[r] = "Missing the {} parameter.".format(r)
        if message:
            abort(400, message=message)

        # Check this device does not currently exist
        exists = yield Device.exists(where=['deveui = ?', deveui])
        if exists:
            message[r] = "Device {} currently exists.".format(euiString(deveui))
            abort(400, message=message)

        # Set devaddr to None if this is an otaa device
        if otaa:
            devaddr = None
        
        # Create and validate
        device = Device(deveui=deveui, name=name, devclass=devclass,
                        enabled=enabled, otaa=otaa, devaddr=devaddr,
                        appeui=appeui, nwkskey=nwkskey, appskey=appskey,
                        fcntup=0, fcntdown=0, fcnterror=False)
        (valid, message) = yield device.valid(self.server)
        if not valid:
            abort(400, message=message)

        try:
            d = yield device.save()
            if d is None:
                abort(500, message={'error': "Error saving device"})
            location = self.restapi.api.prefix + '/device/' + str(device.deveui)
            returnValue(({}, 201, {'Location': location}))
        except TimeoutError:
            # Exception returns 500 to client
            log.error("REST API timeout for device POST request")



