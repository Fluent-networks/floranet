# FloraNet
FloraNet is a LoRaWAN™ Network Server. 

In a LoRaWAN network, the Network Server (NS) is a central element that communicates to end-devices via gateways, which act as transparent bridges between a LoRa™ wireless network and an enterprise IP network.

FloraNet was developed to promote development, prototyping and learning of IoT concepts and technologies. Note that you should not consider FloraNet to be a production-ready system.

FloraNet was built using Python 2.7 and has been tested on Mac OS X and Ubuntu Linux platforms. It currently supports Multitech Conduit gateways and Multitech mDot 915 MHz RF modules (MTDOT-915) as end-devices.

### Features
* Supports Class A and Class C end-devices.
* Supports US 902-928 MHz and AU 915-928 MHz ISM bands. 
* Support for over the air (OTA) activation and activation by personalisation (ABP) join procedures.
* Support for adaptive data rate (ADR) control.
* De-duplication of messages delivered from multiple gateways.
* Support for multiple applications and extensible application server interfaces using plugin modules.

### Limitations
* No support for CN779-787 or EU433 frequency bands. 
* No support for Class B end-devices.
* support for EU863-870 at alpha stage

### Prerequisites
* Python 2.7
* Postgres 9.3+
* CryptoPlus 1.0

Installing CryptoPlus:

```
$ git clone https://github.com/doegox/python-cryptoplus.git
$ cd python-cryptoplus && sudo python setup.py install
```


### Installation

Clone the repository:

```
$ git clone https://github.com/Fluent-networks/floranet.git
```

Run setup.py:

```
$ sudo python setup.py install
```

### Database Configuration
FloraNet uses a Postgres database to create ABP and OTA device information and maintain device state. The database connection assumes that the username/password is **postgres**/**postgres** and the database name is **floranet**. If you wish to alter this setup, edit the following line in the file `data/alembic.ini`:

```
sqlalchemy.url = postgresql://postgres:postgres@127.0.0.1:5432/floranet
```

#### Migration
Run alembic to perform the inital database migration to create the device table.

```
$ cd data
$ alembic upgrade head
```

#### Seeding

You may want to populate the device table with ABP devices. This is accomplished using the `devices.csv` file in the `seed` directory. This file can be used to create ABP devices using by defining the following fields (one line per device):

| Field    | Description| Data Type |
|----------|------------|-----------|
| deveui  | Device EUI | Numeric |
| devaddr | Device address | Integer |
| appeui  | Application EUI | Numeric |
| nwkskey | Network Secret Key | Numeric |
| appskey | Application Secret Key | Numeric |

Note that this file includes three sample devices. To seed the database device table, run the `seeder` script in the `seed` directory.

``` 
$ cd data/seed
$ ./seeder -s
```

To clear the device table, run:

``` 
$ ./seeder -c
```


### Server Configuration

FloraNet uses a text-based file compatible with Python's configuration file parser. The default configuration file `default.cfg` is located in the `floranet` directory. It contains the following sections:

* `[server]`: defines the server network configuration, database connection, frequency band, OTA addressing, gateways and other parameters.
* `[application.test]`: defines an application identified by `test`, including the application identifier (AppEUI), secret key (AppKey), and upstream application interface configuration.


### Usage

Start FloraNet using the following command-line parameters.


```
floranet.py [-h] [-f] [-c config] [-l logfile]

Arguments:
  -h, --help  show help message and exit
  -f          run in foreground, log to console
  -c config   configuration file (default: default.cfg)
  -l logfile  log file (default: /tmp/floranet.log)
```

### Troubleshooting

If you encounter an error "FATAL: password authentication failed for user postgres" at setup, you can change
the password by:
```
>sudo -u postgres psql
postgres=# ALTER USER postgres PASSWORD 'postgres';
postgres=# CREATE DATABASE floranet;
``` 



