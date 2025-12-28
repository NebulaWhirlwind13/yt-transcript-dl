# yt-transcript-dl

Download YouTube video transcripts in multiple formats using yt-dlp.

## Features

- Multiple output formats: TXT, SRT, VTT, JSON
- Download from videos, channels, and playlists
- Incremental sync with state tracking
- Configuration file support (TOML)
- Batch processing
- Custom filename patterns
- Video metadata inclusion
- Language selection
- Retry logic and rate limiting

## Installation

```bash
pip install yt-transcript-dl
```

Or install from source:

```bash
git clone https://github.com/rk/yt-transcript-dl.git
cd yt-transcript-dl
pip install -e .
```

## Quick Start

### Download a single video transcript
```bash
yt-transcript-dl https://youtube.com/watch?v=VIDEO_ID
```

### Download in SRT format
```bash
yt-transcript-dl https://youtube.com/watch?v=VIDEO_ID --format srt
```

### Download entire channel
```bash
yt-transcript-dl https://youtube.com/@channelname -o ./transcripts
```

## Usage

```
yt-transcript-dl [OPTIONS] [URL]
```

### Output Formats

Use `--format` (or `-f`) to specify output format:

- `txt` - Plain text (default)
- `srt` - SubRip subtitle format
- `vtt` - WebVTT subtitle format
- `json` - JSON with segments and metadata
- `all` - Generate all formats

```bash
# SRT format (for video players)
yt-transcript-dl URL --format srt

# All formats at once
yt-transcript-dl URL --format all
```

### Incremental Sync

Skip already downloaded videos using sync state:

```bash
# First download
yt-transcript-dl https://youtube.com/@channel -o ./channel

# Later: only download new videos
yt-transcript-dl https://youtube.com/@channel -o ./channel --sync
```

Sync options:
- `--sync` - Only download videos newer than last sync
- `--overwrite` - Force re-download existing files
- `--force-full` - Ignore sync state and download all

### Configuration Files

Create a configuration file to set defaults:

```bash
# Generate sample config (global)
yt-transcript-dl --init-config ~/.config/yt-transcript-dl/config.toml

# Or create project-specific config
yt-transcript-dl --init-config .yt-transcript-dl.toml
```

Configuration locations (checked in order):
1. `./.yt-transcript-dl.toml` (project-specific, highest priority)
2. `~/.config/yt-transcript-dl/config.toml` (global user config)

CLI flags override config file settings.

Example config:
```toml
lang = "en"
format = "srt"
output_dir = "./transcripts"
include_metadata = true
embed_description = true
filename_pattern = "{channel}_{date}_{title}"
retry = 5
delay = 1.0
```

See [CONFIG_EXAMPLES.md](examples/CONFIG_EXAMPLES.md) for comprehensive configuration examples and use cases.

Options:
- `--init-config PATH` - Create sample configuration file at specified path
- `--no-config` - Ignore all configuration files

### Options

#### Basic Options
```
  -l, --lang TEXT          Language code for transcript (default: en)
  -o, --output-dir PATH    Output directory (default: current directory)
  -m, --include-metadata   Include video metadata in output file
  -d, --description        Save video description to separate file
  --embed-description      Include video description in transcript file (txt/json only)
  -p, --filename-pattern   Custom filename pattern (tokens: {title}, {channel}, {date}, {id})
```

#### Batch Processing
```
  -i, --input-file PATH    File containing list of URLs (one per line)
```

#### Output Formats
```
  -f, --format [txt|srt|vtt|json|all]
                          Output format (default: txt)
```

#### Sync Options
```
  --overwrite             Force re-download of existing files
  --sync                  Only download videos newer than last sync
  --force-full            Ignore sync state and download all videos
```

#### Advanced Options
```
  -v, --verbose           Enable verbose logging
  --log-file PATH         Save logs to file
  --retry INTEGER         Number of retry attempts for failed downloads (default: 3)
  --delay FLOAT           Delay in seconds between requests (default: 0)
```

#### Configuration
```
  --init-config PATH      Create sample configuration file
  --no-config             Ignore configuration files
```

#### Utility
```
  -V, --version           Show version and exit
  --help                  Show help message and exit
```

## Examples

See [examples/EXAMPLES.md](examples/EXAMPLES.md) for comprehensive examples.

### Basic Examples

```bash
# Download with Spanish subtitles
yt-transcript-dl https://youtube.com/watch?v=xxxxx --lang es

# Save to specific directory with metadata
yt-transcript-dl https://youtube.com/watch?v=xxxxx -o ./transcripts -m

# Download playlist in SRT format
yt-transcript-dl "https://youtube.com/playlist?list=PLxxx" --format srt

# Batch process URLs with custom naming
yt-transcript-dl --input-file urls.txt \
  --filename-pattern "{channel}_{date}_{title}" \
  -o ./batch
```

### Advanced Examples

```bash
# Archive channel with all formats and metadata
yt-transcript-dl https://youtube.com/@channel \
  --format all \
  --include-metadata \
  --description \
  --delay 1 \
  -o ./archive

# Incremental channel sync
yt-transcript-dl https://youtube.com/@channel -o ./channel --sync
```

## Output

### Plain Text (TXT)
Clean transcript text, optionally with metadata header.

### SubRip (SRT)
Standard subtitle format with timing:
```
1
00:00:00,000 --> 00:00:05,000
First subtitle segment

2
00:00:05,000 --> 00:00:10,000
Second subtitle segment
```

### WebVTT (VTT)
Web Video Text Tracks format:
```
WEBVTT

00:00:00.000 --> 00:00:05.000
First subtitle segment

00:00:05.000 --> 00:00:10.000
Second subtitle segment
```

### JSON
Structured format with segments and metadata:
```json
{
  "segments": [
    {
      "start": 0.0,
      "end": 5.0,
      "text": "First subtitle segment"
    }
  ],
  "metadata": {
    "title": "Video Title",
    "channel": "Channel Name",
    "url": "https://youtube.com/watch?v=...",
    "language": "en",
    "is_auto_generated": false
  }
}
```

## Requirements

- Python 3.10+
- yt-dlp
- click
- tomli (Python <3.11 only)

## Troubleshooting

### No subtitles available
Some videos don't have captions. Try:
- Using `--lang auto` for auto-generated subtitles (coming in future release)
- Checking if the video has captions on YouTube

### Rate limiting
If downloading many videos, use `--delay`:
```bash
yt-transcript-dl --input-file urls.txt --delay 2
```

### Failed downloads
Increase retry attempts:
```bash
yt-transcript-dl URL --retry 5
```

Enable verbose logging to see detailed errors:
```bash
yt-transcript-dl URL --verbose
```

## Development

### Running Tests
```bash
pip install -e ".[dev]"
pytest
```

### Project Structure
```
yt_transcript_dl/
├── cli.py           # Command-line interface
├── downloader.py    # Core download logic
├── formatters.py    # Output format handlers
├── sync_state.py    # Incremental sync tracking
├── config.py        # Configuration file support
└── utils.py         # Utility functions
```

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for version history.

## Related Projects

- [yt-dlp](https://github.com/yt-dlp/yt-dlp) - YouTube downloader (used internally)
- [youtube-transcript-api](https://github.com/jdepoix/youtube-transcript-api) - Alternative transcript API
