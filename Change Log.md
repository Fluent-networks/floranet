# Change Log

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