from flask_restful import Api, Resource

from floranet.web.rest.system import RestSystem
from floranet.web.rest.device import RestDevice, RestDevices
from floranet.web.rest.gateway import RestGateway, RestGateways
from floranet.web.rest.application import RestApplication, RestApplications
from floranet.web.rest.appinterface import RestAppInterface, RestAppInterfaces
from floranet.web.rest.appproperty import RestAppProperty, RestAppPropertys
class RestApi(object):
    """Defines the Floranet REST API.
    
    Attributes:
        api (Api): Flask RESTful API object
        version (float): API version
        server (NetServer): Network server
        
    """
    def __init__(self, app, server):
        
        # NetServer
        self.server = server
        
        # Set the version
        self.version = 1.0

        # Initialise the API
        self.api = Api(app, prefix='/api/v' + str(self.version))
        
        # Setup routing
        self.resources = {
            # System endpoint
            '/system':                      RestSystem,
            # Device endpoints
            '/device/<int:deveui>':         RestDevice,
            '/devices':                     RestDevices,
            # Application endpoints
            '/app/<int:appeui>':            RestApplication,
            '/apps':                        RestApplications,
            # Gateway endpoints
            '/gateway/<host>':              RestGateway,
            '/gateways':                    RestGateways,
            # Application interface endpoints
            '/interface/<appinterface_id>': RestAppInterface,
            '/interfaces':                  RestAppInterfaces,
            # Application property endpoints
            '/property/<int:appeui>':       RestAppProperty,
            '/propertys':                   RestAppPropertys
        }
        
        kwargs = {'restapi': self, 'server': self.server}
        for path,klass in self.resources.iteritems():
            self.api.add_resource(klass, path, resource_class_kwargs=kwargs)

