from twisted.internet.defer import inlineCallbacks, returnValue

from floranet.models.appinterface import AppInterface
from floranet.log import log

class InterfaceManager(object):
    """Manages the server's application interfaces
    
    Attribues:
        interfaces (list): List of interfaces
        netserver (NetServer): The network server
    """
    
    def __init__(self):
        self.interfaces = []
        self.netserver = None
        
    @inlineCallbacks
    def start(self, netserver):
        """Load all application interfaces and start them.
        
        Args:
            netserver (NetServer): The network server
        """
        
        self.netserver = netserver
        
        # Get all concrete application interface objects
        appinterfaces = yield AppInterface.all()
        for appinterface in appinterfaces:
            # Get the interface, set the appinterface
            interface = yield appinterface.interfaces.get()
            if interface:
                interface.appinterface = appinterface
                self.interfaces.append(interface)
        
        # Start the interfaces
        for interface in self.interfaces:
            log.info("Starting application interface id {id}: {name}",
                     id=interface.appinterface.id, name=interface.name)
            interface.start(self.netserver)
            if not interface.started:
                log.error("Could not start application interface "
                        "id {id}", id=interface.appinterface.id)

    def getInterface(self, appinterface_id):
        """Retrieve an interface by application interface id"""
        
        interface = next((i for i in self.interfaces if
                i.appinterface.id == int(appinterface_id)), None)
        return(interface)
    
    def getAllInterfaces(self):
        """Retrieve all interfaces"""
        
        if not self.interfaces:
            return None
        return self.interfaces

    @inlineCallbacks
    def createInterface(self, interface):
        """Add an interface to the interface list"
        
        Args:
            interface: The concrete application interface
            
        Returns:
            Appinterface id on success
        """
        
        # Create the interface and AppInterface
        yield interface.save()
        appinterface = AppInterface()
        yield appinterface.save()
        yield interface.appinterfaces.set([appinterface])
        
        # Add the new interface to the list
        interface.appinterface = appinterface
        self.interfaces.append(interface)
        
        # Start the interface
        interface.start(self.netserver)
        if not interface.started:
                log.error("Could not start application interface "
                        "id {id}", interface.appinterface.id)
        returnValue(appinterface.id)
        yield

    @inlineCallbacks
    def updateInterface(self, interface):
        """Update an existing interface
        
        Args:
            appinterface (AppInterface): The Appinterface object
            interface: The concrete application interface
        """
        
        # Save interface
        yield interface.save()
        interface.appinterface = yield interface.appinterfaces.get()
        
        # Retrieve the current running interface and its index
        (index, current) = next (((i,iface) for i,iface in
                enumerate(self.interfaces) if
                iface.appinterface.id == interface.appinterface.id),
                (None, None))
        
        # Stop and remove the current interface
        if current:
            current.stop()
            del self.interfaces[index]
        
        # Append the new interface and start
        self.interfaces.append(interface)
        interface.start(self.netserver)
        if not interface.started:
                log.error("Could not start application interface "
                        "id {id}", interface.appinterface.id)

    @inlineCallbacks
    def deleteInterface(self, interface):
        """Remove an interface from the interface list
        
        Args:
            interface: The concrete application interface
        """
        
        # Find the interface in the list, and remove
        index = next ((i for i,iface in enumerate(self.interfaces) if
                iface.appinterface.id == interface.appinterface.id), None)
        if index:
            del self.interfaces[index]
        
        # Delete the interface and appinterface records
        exists = interface.exists(where=['id = ?', interface.id])
        if exists:
            appinterface = yield interface.appinterfaces.get()
            yield interface.delete()
            yield appinterface[0].delete()

interfaceManager = InterfaceManager()

