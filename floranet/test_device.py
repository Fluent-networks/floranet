import psycopg2

from twisted.internet import reactor
from twisted.internet.defer import inlineCallbacks

from twisted.enterprise import adbapi
from twistar.registry import Registry

from device import Device
     
@inlineCallbacks
def addDevice():
     d = Device(deveui=1001, devaddr=2, appeui=2, nwkskey=3, appskey=4,
                fcntup=0, fcntdown=0)
     d.id = 2
     yield d.save()
     active = yield Device.find(where=['deveui = ?', d.deveui], limit=1)
     x = active.deveui


# Connect to the DB
Registry.DBPOOL = adbapi.ConnectionPool('psycopg2', host = "127.0.0.1",
                  user = "postgres", password = "postgres", database = "floranet")
#addDevice()
reactor.callWhenRunning(addDevice)
reactor.run()


