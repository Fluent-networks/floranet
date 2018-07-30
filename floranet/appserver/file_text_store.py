import os

from twisted.internet.defer import inlineCallbacks, returnValue
from flask_restful import fields, marshal

from floranet.models.model import Model

class FileTextStore(Model):
    """File text storage application server interface
    
    This appserver interface saves data received to a file.
    
    Attributes:
        name (str): Application interface name
        file (str): File name
        running (bool): Running flag
    """
    
    TABLENAME = 'appif_file_text_store'
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
        """Validate a FileTextStore object.
            
        Returns:
            valid (bool), message(dict): (True, empty) on success,
            (False, error message dict) otherwise.
        """
        messages = {}

        # Check the file path
        (path, name) = os.path.split(self.file)
        if path and not os.path.isdir(path):
            messages['file'] = "Directory {} does not exist".format(path)

        valid = not any(messages)
        returnValue((valid, messages))
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
            'file': fields.String,
            'started': fields.Boolean
        }
        return marshal(self, marshal_fields)
    
    def netServerReceived(self, device, app, port, appdata):
        """Receive a application message from LoRa network server"""
        
        # Write data to our file, append and create if it doesn't exist.
        fp = open(self.file, 'a+')
        fp.write(appdata)
        fp.close()
        
    
    def datagramReceived(self, data, (host, port)):
        """Receive inbound application server data"""
        pass
        
    