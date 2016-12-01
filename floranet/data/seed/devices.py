import ast
import csv
from sqlalchemy import Column, Integer, Numeric, String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Device(Base):
    __tablename__ = 'devices'
    id = Column(Integer, primary_key=True, autoincrement=True)
    deveui = Column(Numeric, nullable=False, unique=True)
    devaddr = Column(Integer, nullable=False)
    appeui = Column(Numeric, nullable=False)
    nwkskey = Column(Numeric, nullable=False)
    appskey = Column(Numeric, nullable=False)
    tx_chan = Column(Integer, nullable=True, default=1)
    tx_datr = Column(String, nullable=True)
    gw_addr = Column(String, nullable=True)
    fcntup = Column(Integer, nullable=False, default=0)
    fcntdown = Column(Integer, nullable=False, default=0)
    
    @classmethod
    def seed(cls, session):
        devices = []
        with open('devices.csv') as sfile:
            reader = csv.DictReader(sfile)
            for line in reader:
                # Convert data using literal_eval
                d = {}
                for k,v in line.iteritems():
                    d[k] = ast.literal_eval(v) if v else ''
                devices.append(d)
        session.bulk_insert_mappings(Device, devices)

    @classmethod
    def clear (cls, session):
        devices = session.query(Device).all()
        for d in devices:      
            session.delete(d)
    