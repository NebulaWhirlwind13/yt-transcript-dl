# yt-transcript-dl Examples

## Basic Usage

### Download single video transcript
```bash
yt-transcript-dl https://youtube.com/watch?v=VIDEO_ID
```

### Download with different language
```bash
yt-transcript-dl https://youtube.com/watch?v=VIDEO_ID --lang es
```

### Save to specific directory
```bash
yt-transcript-dl https://youtube.com/watch?v=VIDEO_ID -o ./transcripts
```

## Output Formats

### Download as SRT (subtitle format)
```bash
yt-transcript-dl https://youtube.com/watch?v=VIDEO_ID --format srt
```

### Download as WebVTT
```bash
yt-transcript-dl https://youtube.com/watch?v=VIDEO_ID --format vtt
```

### Download as JSON (with metadata)
```bash
yt-transcript-dl https://youtube.com/watch?v=VIDEO_ID --format json
```

### Download all formats at once
```bash
yt-transcript-dl https://youtube.com/watch?v=VIDEO_ID --format all
```

## Metadata and Descriptions

### Include video metadata in output
```bash
yt-transcript-dl https://youtube.com/watch?v=VIDEO_ID --include-metadata
```

### Save video description to separate file
```bash
yt-transcript-dl https://youtube.com/watch?v=VIDEO_ID --description
```

### Both metadata and description
```bash
yt-transcript-dl https://youtube.com/watch?v=VIDEO_ID -m -d
```

## Batch Processing

### Process multiple URLs from file
```bash
# Create urls.txt with one URL per line
yt-transcript-dl --input-file urls.txt -o ./transcripts
```

### Download entire channel
```bash
yt-transcript-dl https://youtube.com/@channelname -o ./channel-transcripts
```

### Download playlist
```bash
yt-transcript-dl "https://youtube.com/playlist?list=PLxxx" -o ./playlist
```

## Incremental Sync

### First download (creates .sync_state.json)
```bash
yt-transcript-dl https://youtube.com/@channelname -o ./channel
```

### Sync mode (only new videos)
```bash
yt-transcript-dl https://youtube.com/@channelname -o ./channel --sync
```

### Force re-download everything
```bash
yt-transcript-dl https://youtube.com/@channelname -o ./channel --overwrite
```

### Ignore sync state
```bash
yt-transcript-dl https://youtube.com/@channelname -o ./channel --force-full
```

## Filename Patterns

### Use custom filename pattern
```bash
yt-transcript-dl https://youtube.com/watch?v=VIDEO_ID \
  --filename-pattern "{channel}_{date}_{title}"
```

### Available tokens
- `{title}` - Video title
- `{channel}` - Channel name
- `{date}` - Upload date (YYYY-MM-DD)
- `{id}` - Video ID

## Advanced Options

### Retry failed downloads
```bash
yt-transcript-dl https://youtube.com/watch?v=VIDEO_ID --retry 5
```

### Add delay between requests (rate limiting)
```bash
yt-transcript-dl --input-file urls.txt --delay 2
```

### Verbose logging
```bash
yt-transcript-dl https://youtube.com/watch?v=VIDEO_ID --verbose
```

### Save logs to file
```bash
yt-transcript-dl https://youtube.com/watch?v=VIDEO_ID \
  --verbose --log-file transcript.log
```

## Configuration File

### Create sample configuration file
```bash
yt-transcript-dl --init-config ~/.config/yt-transcript-dl/config.toml
```

### Use local configuration
```bash
# Create .yt-transcript-dl.toml in current directory
yt-transcript-dl --init-config .yt-transcript-dl.toml

# Edit the file, then run:
yt-transcript-dl https://youtube.com/watch?v=VIDEO_ID
# (will use config from .yt-transcript-dl.toml)
```

### Ignore configuration files
```bash
yt-transcript-dl https://youtube.com/watch?v=VIDEO_ID --no-config
```

## Complete Examples

### Archive entire channel with all formats
```bash
yt-transcript-dl https://youtube.com/@channelname \
  -o ./archive \
  --format all \
  --include-metadata \
  --description \
  --delay 1 \
  --retry 5 \
  --verbose
```

### Sync channel weekly
```bash
# Week 1 - initial download
yt-transcript-dl https://youtube.com/@channelname -o ./channel

# Week 2 - only new videos
yt-transcript-dl https://youtube.com/@channelname -o ./channel --sync

# Week 3 - only new videos
yt-transcript-dl https://youtube.com/@channelname -o ./channel --sync
```

### Batch process with custom naming
```bash
yt-transcript-dl --input-file urls.txt \
  -o ./batch \
  --filename-pattern "{date}_{channel}_{id}" \
  --format srt \
  --delay 2
```
