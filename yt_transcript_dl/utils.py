"""Utility functions for yt-transcript-dl."""

import re
import sys


def sanitize_filename(title: str, max_length: int = 200) -> str:
    """
    Sanitize a string to be safe for use as a filename.

    Args:
        title: The raw title string
        max_length: Maximum length for the filename (default 200)

    Returns:
        A filesystem-safe string
    """
    if not title:
        return "untitled"

    # Replace problematic characters with safe alternatives
    replacements = {
        '/': '-',
        '\\': '-',
        ':': ' -',
        '*': '',
        '?': '',
        '"': "'",
        '<': '',
        '>': '',
        '|': '-',
        '\n': ' ',
        '\r': '',
        '\t': ' ',
    }

    result = title
    for char, replacement in replacements.items():
        result = result.replace(char, replacement)

    # Remove leading/trailing whitespace and dots
    result = result.strip().strip('.')

    # Collapse multiple spaces/dashes
    result = re.sub(r'\s+', ' ', result)
    result = re.sub(r'-+', '-', result)

    # Truncate if too long (preserve extension space)
    if len(result) > max_length:
        result = result[:max_length].rsplit(' ', 1)[0]

    # Fallback if empty after sanitization
    if not result:
        return "untitled"

    return result


def print_error(message: str) -> None:
    """Print an error message to stderr in red."""
    if sys.stderr.isatty():
        sys.stderr.write(f"\033[0;31mError:\033[0m {message}\n")
    else:
        sys.stderr.write(f"Error: {message}\n")


def print_info(message: str) -> None:
    """Print an info message to stderr in yellow."""
    if sys.stderr.isatty():
        sys.stderr.write(f"\033[1;33m{message}\033[0m\n")
    else:
        sys.stderr.write(f"{message}\n")


def print_success(message: str) -> None:
    """Print a success message to stderr in green."""
    if sys.stderr.isatty():
        sys.stderr.write(f"\033[0;32m{message}\033[0m\n")
    else:
        sys.stderr.write(f"{message}\n")


def format_filename(pattern: str, video_info, sanitize: bool = True) -> str:
    """
    Format a filename using pattern tokens.

    Args:
        pattern: Filename pattern with tokens {title}, {channel}, {date}, {id}
        video_info: VideoInfo object with video metadata
        sanitize: Whether to sanitize the result (default: True)

    Returns:
        Formatted filename string

    Supported tokens:
        {title}   - Video title
        {channel} - Channel name
        {date}    - Upload date (YYYY-MM-DD format)
        {id}      - Video ID
    """
    # Format date if available
    date_str = ""
    if video_info.upload_date:
        raw_date = video_info.upload_date
        if len(raw_date) == 8:
            date_str = f"{raw_date[:4]}-{raw_date[4:6]}-{raw_date[6:]}"
        else:
            date_str = raw_date

    # Build replacements
    replacements = {
        '{title}': video_info.title,
        '{channel}': video_info.channel,
        '{date}': date_str,
        '{id}': video_info.id,
    }

    result = pattern
    for token, value in replacements.items():
        result = result.replace(token, value)

    if sanitize:
        result = sanitize_filename(result)

    return result
