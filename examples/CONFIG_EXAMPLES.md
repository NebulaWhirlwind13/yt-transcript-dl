# Configuration File Examples

This guide demonstrates how to use `--init-config` to create and manage configuration files for `yt-transcript-dl`.

## Table of Contents

- [Quick Start](#quick-start)
- [Config File Locations](#config-file-locations)
- [Creating Config Files](#creating-config-files)
- [Configuration Options](#configuration-options)
- [Use Cases](#use-cases)
- [Priority System](#priority-system)
- [Examples](#examples)

---

## Quick Start

Create a global configuration file:

```bash
yt-transcript-dl --init-config ~/.config/yt-transcript-dl/config.toml
```

Create a project-specific configuration file:

```bash
cd your-project
yt-transcript-dl --init-config .yt-transcript-dl.toml
```

---

## Config File Locations

Configuration files are checked in this order (first found wins):

1. **Project-specific**: `./.yt-transcript-dl.toml` (current directory)
2. **Global user**: `~/.config/yt-transcript-dl/config.toml`

**Priority**: Project > Global > CLI flags override both

---

## Creating Config Files

### Basic Usage

```bash
# Create config at specified path
yt-transcript-dl --init-config <path>

# Common patterns:
yt-transcript-dl --init-config ~/.config/yt-transcript-dl/config.toml  # Global
yt-transcript-dl --init-config .yt-transcript-dl.toml                  # Project-specific
yt-transcript-dl --init-config ./custom-config.toml                    # Custom location
```

### Default Template

The `--init-config` command creates a TOML file with all available options:

```toml
# yt-transcript-dl configuration file
#
# This file defines default options for yt-transcript-dl.
# CLI flags override these settings when specified.
#
# Configuration file locations (checked in order):
#   1. ./.yt-transcript-dl.toml (project-specific)
#   2. ~/.config/yt-transcript-dl/config.toml (global)

# ============================================================================
# Language Settings
# ============================================================================

# Default language code for transcripts
lang = "en"

# Comma-separated fallback language codes (empty to disable)
# Use "auto" to accept any auto-generated caption
# Example: lang_fallback = "en,es,auto"
lang_fallback = ""

# Fail if preferred language unavailable (true/false)
# When false, falls back to available languages
require_lang = false

# ============================================================================
# Output Settings
# ============================================================================

# Output directory for transcripts (empty for current directory)
# Example: output_dir = "./transcripts"
output_dir = ""

# Output format: txt, srt, vtt, json, or all
format = "txt"

# Filename pattern using tokens: {title}, {channel}, {date}, {id}
# Example: filename_pattern = "{channel}_{date}_{title}"
filename_pattern = ""

# ============================================================================
# Metadata Settings
# ============================================================================

# Include video metadata in output files
include_metadata = false

# Save video description to separate file
description = false

# Embed video description in transcript file (txt/json only)
embed_description = false

# ============================================================================
# Logging Settings
# ============================================================================

# Enable verbose logging
verbose = false

# Log file path (empty to disable file logging)
# Example: log_file = "./download.log"
log_file = ""

# ============================================================================
# Download Behavior
# ============================================================================

# Number of retry attempts for failed downloads
retry = 3

# Delay in seconds between requests
delay = 0.0

# Force re-download of existing files
overwrite = false

# Only download videos newer than last sync
sync = false
```

---

## Configuration Options

All CLI flags can be set in the config file:

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `lang` | string | `"en"` | Language code for transcripts |
| `lang_fallback` | string | `""` | Comma-separated fallback languages |
| `require_lang` | boolean | `false` | Fail if preferred language unavailable |
| `output_dir` | string | `""` | Output directory path |
| `format` | string | `"txt"` | Output format (txt/srt/vtt/json/all) |
| `filename_pattern` | string | `""` | Filename pattern with tokens |
| `include_metadata` | boolean | `false` | Include video metadata |
| `description` | boolean | `false` | Save description to separate file |
| `embed_description` | boolean | `false` | Embed description in transcript |
| `verbose` | boolean | `false` | Enable verbose logging |
| `log_file` | string | `""` | Log file path |
| `retry` | integer | `3` | Number of retry attempts |
| `delay` | float | `0.0` | Delay between requests (seconds) |
| `overwrite` | boolean | `false` | Force re-download existing files |
| `sync` | boolean | `false` | Only download newer videos |

---

## Use Cases

### 1. Personal Global Defaults

**Setup** (one-time):
```bash
yt-transcript-dl --init-config ~/.config/yt-transcript-dl/config.toml
```

**Edit** `~/.config/yt-transcript-dl/config.toml`:
```toml
lang = "en"
output_dir = "~/Downloads/transcripts"
format = "txt"
retry = 3
delay = 0.5
```

**Usage** (works from anywhere):
```bash
# Uses global defaults
yt-transcript-dl https://youtube.com/watch?v=xxxxx

# Saved to ~/Downloads/transcripts/Video_Title.txt
```

---

### 2. Research Project

**Setup**:
```bash
cd ~/research/climate-videos
yt-transcript-dl --init-config .yt-transcript-dl.toml
```

**Edit** `.yt-transcript-dl.toml`:
```toml
lang = "en"
lang_fallback = "auto"
output_dir = "./raw-transcripts"
include_metadata = true
filename_pattern = "{channel}_{date}_{id}"
format = "json"
verbose = true
log_file = "./scraping.log"
```

**Usage**:
```bash
# Download from list of URLs
yt-transcript-dl --input-file video-urls.txt

# All videos saved to ./raw-transcripts/ with metadata
```

---

### 3. Multi-Language Archive

**Project config**:
```toml
lang = "es"
lang_fallback = "en,fr,auto"
output_dir = "./multilingual-archive"
include_metadata = true
description = true
filename_pattern = "{channel}/{lang}_{title}"
format = "all"
sync = true
```

**Batch processing**:
```bash
# First run - downloads all
yt-transcript-dl --input-file channels.txt

# Second run (days later) - only new videos
yt-transcript-dl --input-file channels.txt
# (sync = true skips existing)

# Force re-download everything
yt-transcript-dl --input-file channels.txt --force-full
```

---

### 4. Team Sharing

**Commit to repo**:
```bash
cd your-team-project
yt-transcript-dl --init-config .yt-transcript-dl.toml
# Edit config for team standards
git add .yt-transcript-dl.toml
git commit -m "Add yt-transcript-dl config"
```

**Team members use automatically**:
```bash
git pull
yt-transcript-dl https://youtube.com/watch?v=xxxxx
# Uses team's standardized config
```

---

## Priority System

### Example: Override Global with Project Config

**Global** (`~/.config/yt-transcript-dl/config.toml`):
```toml
lang = "en"
format = "txt"
verbose = false
```

**Project** (`./.yt-transcript-dl.toml`):
```toml
lang = "fr"
format = "json"
verbose = true
```

**From project directory**:
```bash
yt-transcript-dl https://youtube.com/watch?v=xxxxx
# Uses: lang=fr, format=json, verbose=true (project config)
```

**From other directory**:
```bash
yt-transcript-dl https://youtube.com/watch?v=xxxxx
# Uses: lang=en, format=txt, verbose=false (global config)
```

---

### CLI Flags Override Config

**Config** (`.yt-transcript-dl.toml`):
```toml
lang = "en"
format = "txt"
```

**Override with CLI flag**:
```bash
# Override just language
yt-transcript-dl https://youtube.com/watch?v=xxxxx --lang fr
# Uses: lang=fr (CLI), format=txt (config)

# Override multiple options
yt-transcript-dl https://youtube.com/watch?v=xxxxx --lang es --format srt
# Uses: lang=es (CLI), format=srt (CLI)
```

---

### Ignore All Configs

**Force default settings**:
```bash
yt-transcript-dl https://youtube.com/watch?v=xxxxx --no-config
# Ignores all config files, uses CLI defaults
```

---

## Examples

### Example 1: Quick Setup

```bash
# Create global config
yt-transcript-dl --init-config ~/.config/yt-transcript-dl/config.toml

# Edit to set preferences (use your favorite editor)
vim ~/.config/yt-transcript-dl/config.toml

# Now all commands use these defaults
yt-transcript-dl https://youtube.com/watch?v=xxxxx
```

---

### Example 2: Project-Specific Settings

```bash
# Navigate to project
cd ~/projects/youtube-archives/cooking-channel

# Create project config
yt-transcript-dl --init-config .yt-transcript-dl.toml

# Customize for this project
cat > .yt-transcript-dl.toml << 'EOF'
lang = "en"
lang_fallback = "es,auto"
output_dir = "./transcripts"
include_metadata = true
description = true
filename_pattern = "{date}_{title}"
format = "all"
verbose = true
log_file = "./download.log"
retry = 5
delay = 1.0
EOF

# Download with project settings
yt-transcript-dl https://youtube.com/watch?v=xxxxx
# Equivalent to:
# yt-transcript-dl https://youtube.com/watch?v=xxxxx \
#   --lang en --lang-fallback "es,auto" \
#   -o ./transcripts -m -d \
#   -p "{date}_{title}" -f all -v \
#   --log-file ./download.log --retry 5 --delay 1.0
```

---

### Example 3: Different Configs for Different Projects

```bash
# Project A: English tech videos
cd ~/archives/tech
cat > .yt-transcript-dl.toml << 'EOF'
lang = "en"
format = "txt"
output_dir = "./transcripts"
filename_pattern = "{channel}_{title}"
EOF

# Project B: Spanish cooking videos
cd ~/archives/cooking
cat > .yt-transcript-dl.toml << 'EOF'
lang = "es"
lang_fallback = "en,auto"
format = "srt"
output_dir = "./subtitles"
filename_pattern = "{date}_{title}"
description = true
EOF

# Each project uses its own config automatically
```

---

### Example 4: Verbose Output Shows Config Loading

```bash
cd ~/projects/my-project

# Project config exists
yt-transcript-dl https://youtube.com/watch?v=xxxxx
# Output: Loaded configuration from: /path/to/project/.yt-transcript-dl.toml (project-specific)

# From directory without project config
cd /tmp
yt-transcript-dl https://youtube.com/watch?v=xxxxx
# Output: Loaded configuration from: ~/.config/yt-transcript-dl/config.toml (global)

# Disable config loading
yt-transcript-dl https://youtube.com/watch?v=xxxxx --no-config
# Output: (no config loaded message)
```

---

## Tips

1. **Start with defaults**: Use `--init-config` to create a template, then customize
2. **Project isolation**: Use `.yt-transcript-dl.toml` for project-specific settings
3. **Team consistency**: Commit `.yt-transcript-dl.toml` to version control
4. **Override when needed**: CLI flags override config files
5. **Skip configs**: Use `--no-config` to ignore all config files
6. **Check what's loaded**: Config file path is displayed when loaded

---

## Troubleshooting

### Config not loading

```bash
# Check if config file exists
ls -la .yt-transcript-dl.toml
ls -la ~/.config/yt-transcript-dl/config.toml

# Verify config syntax
python3 -c "import tomllib; print(tomllib.load(open('.yt-transcript-dl.toml', 'rb')))"
```

### Test config values

```bash
# Use verbose to see what's loaded
yt-transcript-dl https://youtube.com/watch?v=xxxxx --verbose
```

### Reset to defaults

```bash
# Ignore config files
yt-transcript-dl https://youtube.com/watch?v=xxxxx --no-config

# Or delete config files
trash ~/.config/yt-transcript-dl/config.toml
trash .yt-transcript-dl.toml
```
