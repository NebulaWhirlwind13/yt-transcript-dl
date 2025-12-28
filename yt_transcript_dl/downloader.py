"""Core download logic using yt-dlp."""

import json
import re
import tempfile
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Generator, List, Optional

import yt_dlp


class URLType(Enum):
    """Types of YouTube URLs."""
    VIDEO = "video"
    CHANNEL = "channel"
    PLAYLIST = "playlist"
    UNKNOWN = "unknown"


@dataclass
class VideoInfo:
    """Container for video metadata."""
    id: str
    title: str
    channel: str
    upload_date: str
    duration: int
    view_count: int
    url: str
    description: str


@dataclass
class TranscriptSegment:
    """A single segment of transcript with timing information."""
    start: float
    end: float
    text: str


@dataclass
class TranscriptResult:
    """Result of a transcript download."""
    video_info: VideoInfo
    transcript: str  # Plain text transcript (for backward compatibility)
    segments: List[TranscriptSegment]  # Structured segments with timing
    language: str
    is_auto_generated: bool


class TranscriptDownloader:
    """Downloads YouTube transcripts using yt-dlp."""

    def __init__(self, lang: str = "en", lang_fallback: Optional[List[str]] = None, require_lang: bool = False):
        """
        Initialize the downloader.

        Args:
            lang: Preferred language code for transcripts (default: en)
            lang_fallback: List of fallback language codes (optional). 'auto' means auto-generated in any language.
            require_lang: If True, fail instead of falling back to other languages (default: False)
        """
        self.lang = lang
        self.lang_fallback = lang_fallback or []
        self.require_lang = require_lang

    def detect_url_type(self, url: str) -> URLType:
        """
        Detect the type of YouTube URL.

        Args:
            url: YouTube URL to analyze

        Returns:
            URLType indicating the type of content
        """
        # Channel patterns
        channel_patterns = [
            r'youtube\.com/@[\w-]+',
            r'youtube\.com/c/[\w-]+',
            r'youtube\.com/channel/[\w-]+',
            r'youtube\.com/user/[\w-]+',
        ]

        # Playlist patterns
        playlist_patterns = [
            r'youtube\.com/playlist\?list=',
            r'[?&]list=[\w-]+',
        ]

        # Check for playlist
        for pattern in playlist_patterns:
            if re.search(pattern, url):
                return URLType.PLAYLIST

        # Check for channel
        for pattern in channel_patterns:
            if re.search(pattern, url):
                return URLType.CHANNEL

        # Check for video
        if re.search(r'watch\?v=|youtu\.be/', url):
            return URLType.VIDEO

        return URLType.UNKNOWN

    def get_video_info(self, url: str) -> VideoInfo:
        """
        Extract video metadata without downloading.

        Args:
            url: YouTube video URL

        Returns:
            VideoInfo object with metadata

        Raises:
            ValueError: If video info cannot be extracted
        """
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                info = ydl.extract_info(url, download=False)
            except Exception as e:
                raise ValueError(f"Failed to extract video info: {e}")

            if info is None:
                raise ValueError("Could not extract video information")

        return VideoInfo(
            id=info.get('id', ''),
            title=info.get('title', 'Unknown Title'),
            channel=info.get('channel', info.get('uploader', 'Unknown Channel')),
            upload_date=info.get('upload_date', ''),
            duration=info.get('duration', 0),
            view_count=info.get('view_count', 0),
            url=url,
            description=info.get('description', ''),
        )

    def get_available_languages(self, url: str) -> dict:
        """
        Get available subtitle languages for a video.

        Args:
            url: YouTube video URL

        Returns:
            Dictionary with 'manual' and 'auto' keys, each containing a list of language codes

        Raises:
            ValueError: If video info cannot be extracted
        """
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                info = ydl.extract_info(url, download=False)
            except Exception as e:
                raise ValueError(f"Failed to extract video info: {e}")

            if info is None:
                raise ValueError("Could not extract video information")

        manual_langs = list(info.get('subtitles', {}).keys())
        auto_langs = list(info.get('automatic_captions', {}).keys())

        return {
            'manual': manual_langs,
            'auto': auto_langs,
        }

    def enumerate_channel_videos(self, url: str) -> Generator[str, None, None]:
        """
        Enumerate all video URLs from a channel.

        Args:
            url: YouTube channel URL

        Yields:
            Individual video URLs from the channel

        Raises:
            ValueError: If channel cannot be accessed
        """
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': True,
            'playlistend': None,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)

                if info is None:
                    raise ValueError("Could not extract channel information")

                # Handle both channel and playlist structures
                entries = info.get('entries', [])
                for entry in entries:
                    if entry and 'id' in entry:
                        video_id = entry['id']
                        yield f"https://www.youtube.com/watch?v={video_id}"

        except Exception as e:
            raise ValueError(f"Failed to enumerate channel videos: {e}")

    def enumerate_playlist_videos(self, url: str) -> Generator[str, None, None]:
        """
        Enumerate all video URLs from a playlist.

        Args:
            url: YouTube playlist URL

        Yields:
            Individual video URLs from the playlist

        Raises:
            ValueError: If playlist cannot be accessed
        """
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': True,
            'playlistend': None,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)

                if info is None:
                    raise ValueError("Could not extract playlist information")

                # Extract entries from playlist
                entries = info.get('entries', [])
                for entry in entries:
                    if entry and 'id' in entry:
                        video_id = entry['id']
                        yield f"https://www.youtube.com/watch?v={video_id}"

        except Exception as e:
            raise ValueError(f"Failed to enumerate playlist videos: {e}")

    def download_transcript(self, url: str) -> TranscriptResult:
        """
        Download transcript for a YouTube video.

        Args:
            url: YouTube video URL

        Returns:
            TranscriptResult with transcript text and metadata

        Raises:
            ValueError: If no transcript is available
        """
        # Get video info first
        video_info = self.get_video_info(url)

        # Try manual subtitles first, then auto-generated
        transcript, segments, lang, is_auto = self._extract_transcript(url)

        return TranscriptResult(
            video_info=video_info,
            transcript=transcript,
            segments=segments,
            language=lang,
            is_auto_generated=is_auto,
        )

    def _extract_transcript(self, url: str) -> tuple[str, List[TranscriptSegment], str, bool]:
        """
        Extract transcript text from video with language fallback support.

        Returns:
            Tuple of (transcript_text, segments, language_code, is_auto_generated)
        """
        # Build the language priority list
        languages_to_try = [self.lang] + self.lang_fallback

        # Track attempted languages for error message
        attempted_langs = []

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            for lang in languages_to_try:
                # Handle 'auto' keyword - try auto-generated in any available language
                if lang == 'auto':
                    subtitle_file, actual_lang = self._download_any_auto_subtitle(url, temp_path)
                    if subtitle_file is not None:
                        transcript, segments = self._parse_subtitle_file(subtitle_file)
                        return transcript, segments, actual_lang, True
                    attempted_langs.append('auto')
                    continue

                # Try manual subtitles first for this language
                subtitle_file = self._download_subtitles(
                    url, temp_path, lang, auto_generated=False
                )

                if subtitle_file is not None:
                    transcript, segments = self._parse_subtitle_file(subtitle_file)
                    return transcript, segments, lang, False

                # Try auto-generated subtitles for this language
                if not self.require_lang or lang == self.lang:
                    subtitle_file = self._download_subtitles(
                        url, temp_path, lang, auto_generated=True
                    )

                    if subtitle_file is not None:
                        transcript, segments = self._parse_subtitle_file(subtitle_file)
                        return transcript, segments, lang, True

                attempted_langs.append(lang)

                # If require_lang is set, only try the primary language
                if self.require_lang:
                    break

            # No subtitles found in any attempted language
            if self.require_lang:
                raise ValueError(
                    f"No subtitles available for language '{self.lang}'. Use --list-langs to see available languages."
                )
            else:
                raise ValueError(
                    f"No subtitles available in any of the attempted languages: {', '.join(attempted_langs)}. "
                    f"Use --list-langs to see available languages."
                )

    def _download_subtitles(
        self,
        url: str,
        output_dir: Path,
        lang: str,
        auto_generated: bool
    ) -> Optional[Path]:
        """
        Download subtitle file to temporary directory.

        Args:
            url: Video URL
            output_dir: Directory to save subtitle file
            lang: Language code to download
            auto_generated: Whether to download auto-generated subtitles

        Returns:
            Path to downloaded subtitle file, or None if unavailable
        """
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'skip_download': True,
            'writesubtitles': not auto_generated,
            'writeautomaticsub': auto_generated,
            'subtitleslangs': [lang],
            'subtitlesformat': 'vtt/srt/best',
            'outtmpl': str(output_dir / '%(id)s.%(ext)s'),
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
        except Exception:
            return None

        # Find the downloaded subtitle file
        for ext in ['vtt', 'srt']:
            for sub_file in output_dir.glob(f'*.{ext}'):
                return sub_file
            # Also check for language-suffixed files
            for sub_file in output_dir.glob(f'*.{lang}.{ext}'):
                return sub_file

        return None

    def _download_any_auto_subtitle(
        self,
        url: str,
        output_dir: Path
    ) -> tuple[Optional[Path], Optional[str]]:
        """
        Download any available auto-generated subtitle.

        Args:
            url: Video URL
            output_dir: Directory to save subtitle file

        Returns:
            Tuple of (subtitle_file_path, language_code) or (None, None) if unavailable
        """
        # Get available auto-generated languages
        try:
            langs_info = self.get_available_languages(url)
            auto_langs = langs_info.get('auto', [])

            if not auto_langs:
                return None, None

            # Try to download the first available auto-generated subtitle
            # Prefer English if available, otherwise use first available
            preferred_order = ['en', 'en-US', 'en-GB'] + auto_langs
            for lang in preferred_order:
                if lang in auto_langs:
                    subtitle_file = self._download_subtitles(
                        url, output_dir, lang, auto_generated=True
                    )
                    if subtitle_file is not None:
                        return subtitle_file, lang

        except Exception:
            pass

        return None, None

    def _parse_subtitle_file(self, subtitle_file: Path) -> tuple[str, List[TranscriptSegment]]:
        """
        Parse subtitle file and extract clean text with timing.

        Args:
            subtitle_file: Path to VTT or SRT file

        Returns:
            Tuple of (clean_transcript_text, segments_with_timing)
        """
        content = subtitle_file.read_text(encoding='utf-8')
        lines = content.split('\n')

        segments = []
        text_lines = []

        i = 0
        while i < len(lines):
            line = lines[i].strip()

            # Skip VTT header lines
            if line.startswith('WEBVTT') or line.startswith('Kind:') or \
               line.startswith('Language:') or line.startswith('NOTE'):
                i += 1
                continue

            # Skip empty lines
            if not line:
                i += 1
                continue

            # Skip SRT sequence numbers
            if line.isdigit():
                i += 1
                continue

            # Check for timestamp line
            if '-->' in line:
                # Parse timing
                timing_match = re.match(
                    r'(\d{2}):(\d{2}):(\d{2})[.,](\d{3})\s*-->\s*(\d{2}):(\d{2}):(\d{2})[.,](\d{3})',
                    line
                )

                if timing_match:
                    # Convert to seconds
                    start_h, start_m, start_s, start_ms = map(int, timing_match.groups()[:4])
                    end_h, end_m, end_s, end_ms = map(int, timing_match.groups()[4:])

                    start_time = start_h * 3600 + start_m * 60 + start_s + start_ms / 1000
                    end_time = end_h * 3600 + end_m * 60 + end_s + end_ms / 1000

                    # Get subtitle text (next non-empty line(s))
                    i += 1
                    subtitle_text_parts = []

                    while i < len(lines):
                        text_line = lines[i].strip()

                        # Stop at empty line or next timestamp
                        if not text_line or '-->' in text_line or text_line.isdigit():
                            break

                        # Clean the text
                        text_line = re.sub(r'<[^>]+>', '', text_line)
                        text_line = text_line.replace('&nbsp;', ' ')
                        text_line = text_line.replace('&amp;', '&')
                        text_line = text_line.replace('&lt;', '<')
                        text_line = text_line.replace('&gt;', '>')
                        text_line = text_line.replace('&quot;', '"')

                        if text_line:
                            subtitle_text_parts.append(text_line)

                        i += 1

                    if subtitle_text_parts:
                        subtitle_text = ' '.join(subtitle_text_parts)
                        segments.append(TranscriptSegment(
                            start=start_time,
                            end=end_time,
                            text=subtitle_text
                        ))
                        text_lines.append(subtitle_text)

                    continue

            i += 1

        # Join all text and clean up whitespace
        text = ' '.join(text_lines)
        text = re.sub(r'\s+', ' ', text)

        return text.strip(), segments
