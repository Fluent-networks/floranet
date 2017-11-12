# Change Log

## [0.4.2] - 2017-11-12
- Change bin folder to cmd

## [0.4.1] - 2017-11-12
- Alter .gitignore

## [0.4.0] - 2017-11-11
- Major upgrade to support cloud-based application interfaces - Azure IoT Hub
- Created application properties, enabling efficient transfer of upstream application message data 
- Added the stand-alone command line configuration tool: floracmd
- REST API
- LoRaWAN Overview, Setup Guide, and Reference Network documentation added in the Wiki.

## [0.3.3] - 2017-01-03
### Changed
- Update README
- Revert default.cfg

## [0.3.2] - 2017-01-31
### Added
- Initial support for EU868 MHz band

### Fixed
- Bug fix: If adrenable is set to false, each call to NetServer \_processADRRequests throws a TypeError exception, as no argument is passed to ReturnValue(). NetServer start() method will now not start the LoopingCall if adrenable is false.

## [0.3.1] - 2017-01-03
### Changed
- Update README

## [0.3.0] - 2017-01-02
### Added
- Support for adaptive data rate (ADR) control and ADR MAC commands
- Support for encoding & decoding MAC commands sent in the fopts field in LoRa MAC messages
- Support for MAC command queuing, allows commands to be sent in the downlink message window
- Added database connection test on server startup

## [0.2.3] - 2016-12-05
### Fixed
- Bug fix: we were not resetting device fcntup and fcntdown to zero on a OTA re-join. This caused OTA devices to fail the device frame count check.

## [0.2.2] - 2016-12-05
### Fixed
- Bug fix for device frame count increment.

## [0.2.1] - 2016-12-02
### Changed
- Tidy up test files.
- Minor edits to Readme

## [0.2.0] - 2016-12-01
### Added
- Support for persistent device state using Postgres database.
- Relaxed frame count option to cater for device
resets where the first received fcntup after a reset is 1.
- Change log.

### Changed
- Band configuration loading.
- Server start method to support twistar.
- Tag each device with a gateway address.
- Unit test mocks.

## [0.1.0] - 2016-09-23
### Added
- Initial verison.