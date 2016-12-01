#!/usr/bin/env python

from setuptools import setup, find_packages

setup(name='floranet',
      version='0.2.0',
      description='LoRa Network Server',
      author='Frank Edwards',
      author_email='frank.edwards@fluentnetworks.com.au',
      url='https://github.com/fluentnetworks/floranet',
      packages=find_packages(exclude=["*.test", "*.test.*"]),
      install_requires = ['twisted>=16.1.1', 'psycopg2>=1.6', 'twistar>=1.6', 'py2-ipaddress>=3.4.1', 'pycrypto>=2.6.1', 'alembic >=0.8.8'],
     )
