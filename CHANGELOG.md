# Changelog

All notable changes to yt-transcript-dl will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Multiple output formats: TXT, SRT, VTT, JSON via `--format` option
- `--format all` to output all formats simultaneously
- Incremental sync with `.sync_state.json` tracking
- `--overwrite` flag to force re-download existing files
- `--sync` mode to only download videos newer than last sync
- `--force-full` flag to ignore sync state
- Configuration file support (TOML format)
- `--init-config` to generate sample configuration file
- `--no-config` to ignore configuration files
- Improved progress reporting with sync state statistics

### Changed
- Downloader now preserves timestamp information from subtitles
- Skip existing files by default (was: always download)
- File existence checks now consider all requested output formats

### Fixed
- Subtitle parsing now correctly handles both VTT and SRT formats with timing

## [0.1.0] - 2024-12-27

### Added
- Initial release
- Download transcripts from YouTube videos, channels, and playlists
- Support for multiple languages via `--lang` option
- Batch processing with `--input-file`
- Custom filename patterns with `--filename-pattern`
- Video metadata inclusion with `--include-metadata`
- Description download with `--description`
- Retry logic with configurable attempts
- Rate limiting with `--delay`
- Verbose logging support
