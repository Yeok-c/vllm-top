# CHANGELOG.md

# Changelog

## [Unreleased]

## [0.1.0] - 2023-10-01
### Added
- Initial release of the vllm-top package.
- Implemented the VLLM_TOP class for monitoring vLLM metrics.
- Added methods for fetching, displaying, and averaging metrics.
- Created a command-line interface for one-time and continuous monitoring.

## [0.1.1] - 2023-10-15
### Changed
- Improved error handling in the `fetch_metrics` method.
- Enhanced the display format of metrics in the terminal.

## [0.1.2] - 2023-10-30
### Fixed
- Resolved issues with metric parsing for certain edge cases.
- Fixed a bug where the background monitoring thread could crash on network errors.

## [0.1.3] - 2023-11-10
### Added
- Introduced a sparkline chart for visualizing historical data.
- Added cumulative statistics display for prompt and generation tokens.

## [0.1.4] - 2023-11-20
### Changed
- Refactored code for better readability and maintainability.
- Updated dependencies in `requirements.txt` for compatibility.

## [0.1.5] - 2023-12-01
### Fixed
- Fixed a bug in the calculation of average latency metrics.
- Improved performance of the background monitoring thread.