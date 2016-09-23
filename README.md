# FloraNet
FloraNet is a LoRaWAN™ Network Server. 

In a LoRaWAN network, the Network Server (NS) is a central element that communicates to end-devices via gateways, which act as transparent bridges between a LoRa™ wireless network and an enterprise IP network.

FloraNet was developed to promote development, prototyping and learning of IoT concepts and technologies. Note that you should not consider FloraNet to be a production-ready system.

FloraNet was built using Python 2.7 and has been tested on Mac OS X and Ubuntu Linux platforms. It currently supports Multitech Conduit gateways and Multitech mDot 915 MHz RF modules (MTDOT-915) as end-devices.

### Features
* Supports Class A and Class C end-devices.
* Supports US 902-928 MHz and AU 915-928 MHz ISM bands. 
* Support for over the air (OTA) activation and activation by personalisation (ABP) join procedures.
* De-duplication of messages delivered from multiple gateways.
* Support for multiple applications and extensible application server interfaces using plugin modules.

### Limitations
* No support for EU863-870, CN779-787 or EU433 frequency bands. 
* No support for Class B end-devices.
* No persistent storage of OTA activations - OTA devices must re-join the network if the server is restarted.
* No support for adaptive data rate (ADR) control.
* No support for MAC commands other than the link check command.

### Prerequisites
* Python 2.7
* CryptoPlus 1.0

Install CryptoPlus:

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

### Configuration
FloraNet is configured using a single text-based file compatible with Python's configuration file parser.

The default configuration file `default.cfg` is located in the `floranet` directory. It contains the following sections:

* `[server]`: defines network parameters, frequency band, OTA and ABP join parameters, and gateways.
* `[application.test]`: defines an application identified by `test`, including the application identifier (AppEUI), secret key (AppKey), and upstream application interface configuration.

Further information on configuration parameters is included in the project wiki.

### Usage

Start FloraNet using the following command-line paramters.


```
floranet.py [-h] [-f] [-c config] [-l logfile]

Arguments:
  -h, --help  show help message and exit
  -f          run in foreground, log to console
  -c config   configuration file (default: default.cfg)
  -l logfile  log file (default: /tmp/floranet.log)
```
