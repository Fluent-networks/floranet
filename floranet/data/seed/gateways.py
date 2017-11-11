import ast
import csv
import datetime
import pytz
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.dialects.postgresql import INET
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Gateway(Base):
    __tablename__ = 'gateways'
    id = Column(Integer, primary_key=True, autoincrement=True)
    host = Column(INET, nullable=False, unique=True)
    name = Column(String, nullable=True)
    enabled = Column(Boolean, nullable=False, default=True)
    eui = Column(Integer, nullable=True)
    power = Column(Integer, nullable=False)
    port = Column(Integer, nullable=True)
    created = Column(DateTime(timezone=True), nullable=False)
    updated = Column(DateTime(timezone=True), nullable=False)
    
    @classmethod
    def seed(cls, session):
        gateways = []
        # Read fields from the CSV file
        with open('gateways.csv') as sfile:
            reader = csv.DictReader(sfile)
            for line in reader:
                # Convert data using literal_eval
                g = {}
                for k,v in line.iteritems():
                    g[k] = v
                gateways.append(g)
        # Set timestamps as UTC
        for g in gateways:
            now = datetime.datetime.now(tz=pytz.utc).isoformat()
            g['created'] = now
            g['updated'] = now
        # Insert rows
        session.bulk_insert_mappings(Gateway, gateways)

    @classmethod
    def clear (cls, session):
        gateways = session.query(Gateway).all()
        for g in gateways:      
            session.delete(g)
