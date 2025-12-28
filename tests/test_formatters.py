"""Tests for formatters module."""

import json

import pytest

from yt_transcript_dl.downloader import TranscriptSegment, VideoInfo
from yt_transcript_dl.formatters import (
    format_json,
    format_srt,
    format_time_srt,
    format_time_vtt,
    format_txt,
    format_vtt,
    get_file_extension,
    get_formatter,
)


@pytest.fixture
def sample_segments():
    """Create sample transcript segments."""
    return [
        TranscriptSegment(start=0.0, end=5.0, text="Hello world"),
        TranscriptSegment(start=5.0, end=10.5, text="This is a test"),
        TranscriptSegment(start=10.5, end=15.25, text="Third segment"),
    ]


@pytest.fixture
def sample_video_info():
    """Create sample video info."""
    return VideoInfo(
        id="test123",
        title="Test Video",
        channel="Test Channel",
        upload_date="20241227",
        duration=300,
        view_count=1000,
        url="https://youtube.com/watch?v=test123",
        description="Test description",
    )


def test_format_time_srt():
    """Test SRT time formatting."""
    assert format_time_srt(0.0) == "00:00:00,000"
    assert format_time_srt(5.5) == "00:00:05,500"
    assert format_time_srt(65.123) == "00:01:05,123"
    assert format_time_srt(3661.456) == "01:01:01,456"


def test_format_time_vtt():
    """Test VTT time formatting."""
    assert format_time_vtt(0.0) == "00:00:00.000"
    assert format_time_vtt(5.5) == "00:00:05.500"
    assert format_time_vtt(65.123) == "00:01:05.123"
    assert format_time_vtt(3661.456) == "01:01:01.456"


def test_format_txt_plain(sample_segments):
    """Test plain text formatting without metadata."""
    result = format_txt(sample_segments)
    assert "Hello world This is a test Third segment" == result


def test_format_txt_with_metadata(sample_segments, sample_video_info):
    """Test plain text formatting with metadata."""
    result = format_txt(sample_segments, sample_video_info, include_metadata=True)

    assert "# Test Video" in result
    assert "**Channel:** Test Channel" in result
    assert "**URL:** https://youtube.com/watch?v=test123" in result
    assert "**Upload Date:** 2024-12-27" in result
    assert "**Duration:** 5m 0s" in result
    assert "Hello world This is a test Third segment" in result


def test_format_srt(sample_segments):
    """Test SRT formatting."""
    result = format_srt(sample_segments)

    lines = result.strip().split('\n')

    # Check first segment
    assert lines[0] == "1"
    assert lines[1] == "00:00:00,000 --> 00:00:05,000"
    assert lines[2] == "Hello world"

    # Check second segment
    assert lines[4] == "2"
    assert lines[5] == "00:00:05,000 --> 00:00:10,500"
    assert lines[6] == "This is a test"

    # Check third segment
    assert lines[8] == "3"
    assert lines[9] == "00:00:10,500 --> 00:00:15,250"
    assert lines[10] == "Third segment"


def test_format_vtt(sample_segments):
    """Test VTT formatting."""
    result = format_vtt(sample_segments)

    lines = result.strip().split('\n')

    # Check header
    assert lines[0] == "WEBVTT"

    # Check first segment
    assert lines[2] == "00:00:00.000 --> 00:00:05.000"
    assert lines[3] == "Hello world"

    # Check second segment
    assert lines[5] == "00:00:05.000 --> 00:00:10.500"
    assert lines[6] == "This is a test"

    # Check third segment
    assert lines[8] == "00:00:10.500 --> 00:00:15.250"
    assert lines[9] == "Third segment"


def test_format_json_minimal(sample_segments):
    """Test JSON formatting without metadata."""
    result = format_json(sample_segments)
    data = json.loads(result)

    assert "segments" in data
    assert len(data["segments"]) == 3

    # Check first segment
    assert data["segments"][0]["start"] == 0.0
    assert data["segments"][0]["end"] == 5.0
    assert data["segments"][0]["text"] == "Hello world"

    # No metadata when not provided
    assert "metadata" not in data


def test_format_json_with_metadata(sample_segments, sample_video_info):
    """Test JSON formatting with metadata."""
    result = format_json(
        sample_segments,
        sample_video_info,
        language="en",
        is_auto_generated=False
    )
    data = json.loads(result)

    assert "segments" in data
    assert "metadata" in data

    # Check metadata
    metadata = data["metadata"]
    assert metadata["id"] == "test123"
    assert metadata["title"] == "Test Video"
    assert metadata["channel"] == "Test Channel"
    assert metadata["url"] == "https://youtube.com/watch?v=test123"
    assert metadata["upload_date"] == "20241227"
    assert metadata["duration"] == 300
    assert metadata["view_count"] == 1000
    assert metadata["language"] == "en"
    assert metadata["is_auto_generated"] is False


def test_get_formatter():
    """Test formatter retrieval."""
    assert get_formatter("txt") == format_txt
    assert get_formatter("srt") == format_srt
    assert get_formatter("vtt") == format_vtt
    assert get_formatter("json") == format_json

    with pytest.raises(ValueError, match="Unsupported format"):
        get_formatter("invalid")


def test_get_file_extension():
    """Test file extension retrieval."""
    assert get_file_extension("txt") == "txt"
    assert get_file_extension("srt") == "srt"
    assert get_file_extension("vtt") == "vtt"
    assert get_file_extension("json") == "json"


def test_format_json_unicode(sample_video_info):
    """Test JSON formatting with unicode characters."""
    segments = [
        TranscriptSegment(start=0.0, end=5.0, text="Hello 世界"),
        TranscriptSegment(start=5.0, end=10.0, text="Привет мир"),
    ]

    result = format_json(segments, sample_video_info)
    data = json.loads(result)

    # Verify unicode is preserved
    assert data["segments"][0]["text"] == "Hello 世界"
    assert data["segments"][1]["text"] == "Привет мир"


def test_format_srt_empty():
    """Test SRT formatting with empty segments."""
    result = format_srt([])
    assert result == ""


def test_format_vtt_empty():
    """Test VTT formatting with empty segments."""
    result = format_vtt([])
    assert result == "WEBVTT\n"
