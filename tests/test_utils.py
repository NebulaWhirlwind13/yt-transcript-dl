"""Tests for utility functions."""

import pytest
from yt_transcript_dl.downloader import VideoInfo
from yt_transcript_dl.utils import format_filename, sanitize_filename


class TestSanitizeFilename:
    """Tests for sanitize_filename function."""

    def test_basic_title(self):
        """Test that normal titles pass through."""
        assert sanitize_filename("Hello World") == "Hello World"

    def test_removes_slashes(self):
        """Test that slashes are replaced with dashes."""
        assert sanitize_filename("Hello/World") == "Hello-World"
        assert sanitize_filename("Hello\\World") == "Hello-World"

    def test_removes_special_chars(self):
        """Test that special characters are removed or replaced."""
        assert sanitize_filename("What is this?") == "What is this"
        assert sanitize_filename("Test: Something") == "Test - Something"
        assert sanitize_filename("A*B*C") == "ABC"

    def test_collapses_whitespace(self):
        """Test that multiple spaces become single space."""
        assert sanitize_filename("Hello    World") == "Hello World"

    def test_empty_string(self):
        """Test that empty strings return 'untitled'."""
        assert sanitize_filename("") == "untitled"

    def test_only_special_chars(self):
        """Test that strings with only special chars return 'untitled'."""
        assert sanitize_filename("???") == "untitled"

    def test_truncation(self):
        """Test that long titles are truncated."""
        long_title = "A" * 300
        result = sanitize_filename(long_title)
        assert len(result) <= 200

    def test_strips_dots(self):
        """Test that leading/trailing dots are stripped."""
        assert sanitize_filename(".hidden") == "hidden"
        assert sanitize_filename("file.") == "file"


class TestFormatFilename:
    """Tests for format_filename function."""

    def test_basic_title_token(self):
        """Test that {title} token is replaced."""
        video_info = VideoInfo(
            id="abc123",
            title="My Video Title",
            channel="My Channel",
            upload_date="20240315",
            duration=120,
            view_count=1000,
            url="https://youtube.com/watch?v=abc123",
            description="Test description"
        )
        result = format_filename("{title}", video_info)
        assert result == "My Video Title"

    def test_channel_token(self):
        """Test that {channel} token is replaced."""
        video_info = VideoInfo(
            id="abc123",
            title="My Video Title",
            channel="Tech Channel",
            upload_date="20240315",
            duration=120,
            view_count=1000,
            url="https://youtube.com/watch?v=abc123",
            description="Test description"
        )
        result = format_filename("{channel}", video_info)
        assert result == "Tech Channel"

    def test_date_token_formatting(self):
        """Test that {date} token is formatted correctly."""
        video_info = VideoInfo(
            id="abc123",
            title="My Video Title",
            channel="My Channel",
            upload_date="20240315",
            duration=120,
            view_count=1000,
            url="https://youtube.com/watch?v=abc123",
            description="Test description"
        )
        result = format_filename("{date}", video_info)
        assert result == "2024-03-15"

    def test_id_token(self):
        """Test that {id} token is replaced."""
        video_info = VideoInfo(
            id="xyz789",
            title="My Video Title",
            channel="My Channel",
            upload_date="20240315",
            duration=120,
            view_count=1000,
            url="https://youtube.com/watch?v=xyz789",
            description="Test description"
        )
        result = format_filename("{id}", video_info)
        assert result == "xyz789"

    def test_combined_pattern(self):
        """Test that multiple tokens work together."""
        video_info = VideoInfo(
            id="abc123",
            title="My Video",
            channel="Tech Channel",
            upload_date="20240315",
            duration=120,
            view_count=1000,
            url="https://youtube.com/watch?v=abc123",
            description="Test description"
        )
        result = format_filename("{channel}_{date}_{title}", video_info)
        assert result == "Tech Channel_2024-03-15_My Video"

    def test_sanitization_applied(self):
        """Test that filename sanitization is applied by default."""
        video_info = VideoInfo(
            id="abc123",
            title="Video: Title?",
            channel="Channel/Name",
            upload_date="20240315",
            duration=120,
            view_count=1000,
            url="https://youtube.com/watch?v=abc123",
            description="Test description"
        )
        result = format_filename("{channel}_{title}", video_info)
        # Sanitization should replace problematic characters
        assert "?" not in result
        assert "/" not in result
        assert result == "Channel-Name_Video - Title"

    def test_no_sanitization(self):
        """Test that sanitization can be disabled."""
        video_info = VideoInfo(
            id="abc123",
            title="Video: Title",
            channel="Channel Name",
            upload_date="20240315",
            duration=120,
            view_count=1000,
            url="https://youtube.com/watch?v=abc123",
            description="Test description"
        )
        result = format_filename("{channel}_{title}", video_info, sanitize=False)
        assert ":" in result
        assert result == "Channel Name_Video: Title"

    def test_empty_date(self):
        """Test handling when upload_date is empty."""
        video_info = VideoInfo(
            id="abc123",
            title="My Video",
            channel="My Channel",
            upload_date="",
            duration=120,
            view_count=1000,
            url="https://youtube.com/watch?v=abc123",
            description="Test description"
        )
        result = format_filename("{date}_{title}", video_info)
        assert result == "_My Video"

    def test_malformed_date(self):
        """Test handling of malformed date strings."""
        video_info = VideoInfo(
            id="abc123",
            title="My Video",
            channel="My Channel",
            upload_date="2024",
            duration=120,
            view_count=1000,
            url="https://youtube.com/watch?v=abc123",
            description="Test description"
        )
        result = format_filename("{date}", video_info)
        # Should use raw date if not 8 digits
        assert result == "2024"
