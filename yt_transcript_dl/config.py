"""Configuration file support for yt-transcript-dl."""

import sys
from pathlib import Path
from typing import Any, Dict, Optional

# Python 3.11+ has tomllib built-in
if sys.version_info >= (3, 11):
    import tomllib
else:
    try:
        import tomli as tomllib
    except ImportError:
        tomllib = None  # type: ignore


DEFAULT_CONFIG = """# yt-transcript-dl configuration file
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
"""


def load_config(config_file: Path) -> Dict[str, Any]:
    """
    Load configuration from TOML file.

    Args:
        config_file: Path to TOML configuration file

    Returns:
        Dictionary of configuration values

    Raises:
        ValueError: If TOML library is not available
        Exception: If config file cannot be parsed
    """
    if not config_file.exists():
        return {}

    if tomllib is None:
        raise ValueError(
            "TOML support not available. "
            "For Python <3.11, install tomli: pip install tomli"
        )

    with open(config_file, 'rb') as f:
        return tomllib.load(f)


def find_config_file() -> Optional[Path]:
    """
    Find configuration file in standard locations.

    Checks:
    1. ./.yt-transcript-dl.toml (local directory)
    2. ~/.config/yt-transcript-dl/config.toml (user config)

    Returns:
        Path to config file if found, None otherwise
    """
    # Check local directory
    local_config = Path.cwd() / '.yt-transcript-dl.toml'
    if local_config.exists():
        return local_config

    # Check user config directory
    user_config = Path.home() / '.config' / 'yt-transcript-dl' / 'config.toml'
    if user_config.exists():
        return user_config

    return None


def init_config_file(output_path: Path) -> None:
    """
    Create a sample configuration file.

    Args:
        output_path: Where to create the config file
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(DEFAULT_CONFIG, encoding='utf-8')


def merge_config(config: Dict[str, Any], cli_value: Any, config_key: str, cli_default: Any) -> Any:
    """
    Merge configuration value with CLI argument.

    CLI flag > config file > CLI default

    Args:
        config: Configuration dictionary from file
        cli_value: Value from CLI argument
        config_key: Key to look up in config
        cli_default: Default value from CLI

    Returns:
        Merged value
    """
    # If CLI value is None, prefer config value (None means not provided)
    if cli_value is None:
        return config.get(config_key, cli_default)

    # If CLI value differs from default, use it (user explicitly set it)
    if cli_value != cli_default:
        return cli_value

    # Otherwise use config value if present
    return config.get(config_key, cli_default)
