from twisted.internet.defer import inlineCallbacks, returnValue
from flask_restful import fields, marshal

from floranet.models.model import Model

class Reflector(Model):
    """LoRa reflector application server interface
    
    This appserver interface bounces any messages received
    from a device back to that device.
    
    Attributes:
        name (str): Application interface name
        running (bool): Running flag
    """
    
    TABLENAME = 'appif_reflector'
    HASMANY = [{'name': 'appinterfaces', 'class_name': 'AppInterface', 'as': 'interfaces'}]

    def afterInit(self):
        self.started = False
        self.appinterface = None
        
    @inlineCallbacks
    def start(self, netserver):
        """Start the application interface
        
        Args:
            netserver (NetServer): The LoRa network server
        
        Returns True on success, False otherwise
        """
        self.netserver = netserver
        self.started = True
        returnValue(True)
        yield
    
    def stop(self):
        """Stop the application interface"""
        # Reflector does not require any shutdown
        self.started = False
        return
    
    @inlineCallbacks
    def valid(self):
        """Validate a Reflector object.
            
        Returns:
            valid (bool), message(dict): (True, empty) on success,
            (False, error message dict) otherwise.
        """
        returnValue((True, {}))
        yield
        
    def marshal(self):
        """Get REST API marshalled fields as an orderedDict
        
        Returns:
            OrderedDict of fields defined by marshal_fields
        """
        marshal_fields = {
            'type': fields.String(attribute='__class__.__name__'),
            'id': fields.Integer(attribute='appinterface.id'),
            'name': fields.String,
            'started': fields.Boolean
        }
        return marshal(self, marshal_fields)
    
    def netServerReceived(self, device, app, port, appdata):
        """Receive a application message from LoRa network server"""
        # Send the message to the network server
        self.netserver.inboundAppMessage(device.devaddr, appdata)
    
    def datagramReceived(self, data, (host, port)):
        """Receive inbound application server data"""
        pass
        
    