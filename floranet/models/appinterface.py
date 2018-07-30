from twisted.internet.defer import inlineCallbacks, returnValue
from twistar.registry import Registry

from model import Model

class AppInterface(Model):
    """Application interface class
    
    Abstract model representing the application interface.
    
    Each AppInterface belongs to another concrete interface model using
    a polymorphic relationship.
    
    Attributes:
        interfaces_id (int): Application interface class id
        interfaces_type (str): Application interface class name
    """
    
    TABLENAME = 'appinterfaces'
    BELONGSTO = [{'name': 'interfaces', 'polymorphic': True}]

    @inlineCallbacks
    def apps(self):
        """Flags whether this interface has any associated Applications
        
        """
        apps = yield Application.find(where=['appinterface_id = ?', self.appinterface.id])
        returnValue(apps)

