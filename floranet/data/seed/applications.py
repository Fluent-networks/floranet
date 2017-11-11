import ast
import csv
import datetime
import pytz
from sqlalchemy import Column, Integer, Numeric, String, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Application(Base):
    __tablename__ = 'applications'
    id = Column(Integer, primary_key=True, autoincrement=True)
    appeui = Column(Numeric, nullable=False, unique=True)
    name = Column(String, nullable=False)
    domain = Column(String, nullable=False)
    appkey = Column(Numeric, nullable=False)
    fport = Column(Integer, nullable=False)
    appnonce = Column(Integer, nullable=False)
    appinterface_id = Column(Integer, nullable=True)
    created = Column(DateTime(timezone=True), nullable=False)
    updated = Column(DateTime(timezone=True), nullable=False)

    @classmethod
    def seed(cls, session):
        apps = []
        # Read fields from the CSV file
        with open('applications.csv') as sfile:
            reader = csv.DictReader(sfile)
            for line in reader:
                # Convert data
                a = {}
                for k,v in line.iteritems():
                    if k in {'name', 'domain'}:
                        a[k] = v
                        continue
                    else:
                        a[k] = ast.literal_eval(v) if v else ''
                apps.append(a)
        # Set timestamps as UTC
        for a in apps:
            now = datetime.datetime.now(tz=pytz.utc).isoformat()
            a['created'] = now
            a['updated'] = now
        # Insert rows
        session.bulk_insert_mappings(Application, apps)

    @classmethod
    def clear (cls, session):
        apps = session.query(Application).all()
        for a in apps:      
            session.delete(a)
