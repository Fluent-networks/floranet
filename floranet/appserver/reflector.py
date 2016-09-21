"""
   module:: reflector
   :synopsis: Demonstration AppServerInterface

   moduleauthor:: Francis Edwards <frank.edwards@fluentnetworks.com.au>
"""

from twisted.internet import protocol

class AppServerInterface(protocol.DatagramProtocol):
    """LoRa application server interface
    
    This appserver interface bounces any messages received
    from a device back to that device.
    
    """
    
    def __init__(self, netserver):
        """Initialize a Device object.
        
        Args:
            netserver (NetServer): The LoRa network server
        """
        self.netserver = netserver
    
    def netServerReceived(self, devaddr, appdata, confirmed):
        """Receive a application message from LoRa network server"""
        # Send back to the network server
        self.netserver.inboundAppMessage(devaddr, appdata, confirmed)
    
    def datagramReceived(self, data, (host, port)):
        """Receive inbound application server data"""
        pass
        
    