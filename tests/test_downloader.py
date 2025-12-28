"""Tests for transcript downloader functionality."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from yt_transcript_dl.downloader import (
    TranscriptDownloader,
    URLType,
    VideoInfo,
    TranscriptResult,
)


class TestURLDetection:
    """Tests for URL type detection."""

    def test_detect_video_url_watch(self):
        downloader = TranscriptDownloader()
        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        assert downloader.detect_url_type(url) == URLType.VIDEO

    def test_detect_video_url_short(self):
        downloader = TranscriptDownloader()
        url = "https://youtu.be/dQw4w9WgXcQ"
        assert downloader.detect_url_type(url) == URLType.VIDEO

    def test_detect_channel_url(self):
        downloader = TranscriptDownloader()
        url = "https://www.youtube.com/@channelname"
        assert downloader.detect_url_type(url) == URLType.CHANNEL

    def test_detect_playlist_url(self):
        downloader = TranscriptDownloader()
        url = "https://www.youtube.com/playlist?list=PLxxxxxx"
        assert downloader.detect_url_type(url) == URLType.PLAYLIST

    def test_detect_unknown_url(self):
        downloader = TranscriptDownloader()
        url = "https://example.com/video"
        assert downloader.detect_url_type(url) == URLType.UNKNOWN


class TestLanguageSelection:
    """Tests for language selection and fallback."""

    def test_default_language(self):
        """Test default language is 'en'."""
        downloader = TranscriptDownloader()
        assert downloader.lang == "en"
        assert downloader.lang_fallback == []
        assert downloader.require_lang is False

    def test_custom_language(self):
        """Test custom language initialization."""
        downloader = TranscriptDownloader(lang="es")
        assert downloader.lang == "es"

    def test_language_fallback_initialization(self):
        """Test language fallback list initialization."""
        downloader = TranscriptDownloader(
            lang="en",
            lang_fallback=["es", "fr", "auto"]
        )
        assert downloader.lang == "en"
        assert downloader.lang_fallback == ["es", "fr", "auto"]

    def test_require_lang_flag(self):
        """Test require_lang flag initialization."""
        downloader = TranscriptDownloader(lang="en", require_lang=True)
        assert downloader.require_lang is True

    @patch('yt_transcript_dl.downloader.yt_dlp.YoutubeDL')
    def test_get_available_languages(self, mock_ydl_class):
        """Test getting available languages for a video."""
        # Mock the YoutubeDL instance
        mock_ydl = MagicMock()
        mock_ydl_class.return_value.__enter__.return_value = mock_ydl

        # Mock extract_info response
        mock_ydl.extract_info.return_value = {
            'subtitles': {
                'en': [],
                'es': [],
                'fr': [],
            },
            'automatic_captions': {
                'en': [],
                'de': [],
                'ja': [],
            }
        }

        downloader = TranscriptDownloader()
        langs_info = downloader.get_available_languages("https://youtube.com/watch?v=test")

        assert 'manual' in langs_info
        assert 'auto' in langs_info
        assert set(langs_info['manual']) == {'en', 'es', 'fr'}
        assert set(langs_info['auto']) == {'en', 'de', 'ja'}

    @patch('yt_transcript_dl.downloader.yt_dlp.YoutubeDL')
    def test_get_available_languages_none_available(self, mock_ydl_class):
        """Test getting available languages when none exist."""
        mock_ydl = MagicMock()
        mock_ydl_class.return_value.__enter__.return_value = mock_ydl

        mock_ydl.extract_info.return_value = {
            'subtitles': {},
            'automatic_captions': {},
        }

        downloader = TranscriptDownloader()
        langs_info = downloader.get_available_languages("https://youtube.com/watch?v=test")

        assert langs_info['manual'] == []
        assert langs_info['auto'] == []

    @patch('yt_transcript_dl.downloader.yt_dlp.YoutubeDL')
    def test_get_available_languages_error(self, mock_ydl_class):
        """Test error handling when getting available languages."""
        mock_ydl = MagicMock()
        mock_ydl_class.return_value.__enter__.return_value = mock_ydl
        mock_ydl.extract_info.side_effect = Exception("Network error")

        downloader = TranscriptDownloader()

        with pytest.raises(ValueError, match="Failed to extract video info"):
            downloader.get_available_languages("https://youtube.com/watch?v=test")


class TestLanguageFallback:
    """Tests for language fallback logic in transcript extraction."""

    @patch.object(TranscriptDownloader, '_download_subtitles')
    @patch.object(TranscriptDownloader, '_parse_subtitle_file')
    def test_fallback_to_second_language(self, mock_parse, mock_download):
        """Test falling back to second language when first is unavailable."""
        # Mock subtitle download: fail for 'en', succeed for 'es'
        def download_side_effect(url, temp_dir, lang, auto_generated):
            if lang == 'en':
                return None
            elif lang == 'es' and not auto_generated:
                return Path('/tmp/test.vtt')
            return None

        mock_download.side_effect = download_side_effect
        mock_parse.return_value = ("Test transcript", [])

        downloader = TranscriptDownloader(
            lang="en",
            lang_fallback=["es", "fr"]
        )

        with patch.object(downloader, 'get_video_info') as mock_info:
            mock_info.return_value = VideoInfo(
                id="test123",
                title="Test Video",
                channel="Test Channel",
                upload_date="20240101",
                duration=100,
                view_count=1000,
                url="https://youtube.com/watch?v=test",
                description="Test description"
            )

            result = downloader.download_transcript("https://youtube.com/watch?v=test")

            assert result.language == "es"
            assert result.is_auto_generated is False

    @patch.object(TranscriptDownloader, '_download_subtitles')
    @patch.object(TranscriptDownloader, '_download_any_auto_subtitle')
    @patch.object(TranscriptDownloader, '_parse_subtitle_file')
    def test_fallback_to_auto_keyword(self, mock_parse, mock_auto_download, mock_download):
        """Test 'auto' keyword falls back to any auto-generated caption."""
        # Mock subtitle download: fail for specific languages
        mock_download.return_value = None

        # Mock auto subtitle download: succeed
        mock_auto_download.return_value = (Path('/tmp/test.vtt'), 'de')
        mock_parse.return_value = ("Auto-generated transcript", [])

        downloader = TranscriptDownloader(
            lang="en",
            lang_fallback=["es", "auto"]
        )

        with patch.object(downloader, 'get_video_info') as mock_info:
            mock_info.return_value = VideoInfo(
                id="test123",
                title="Test Video",
                channel="Test Channel",
                upload_date="20240101",
                duration=100,
                view_count=1000,
                url="https://youtube.com/watch?v=test",
                description="Test description"
            )

            result = downloader.download_transcript("https://youtube.com/watch?v=test")

            assert result.language == "de"
            assert result.is_auto_generated is True

    @patch.object(TranscriptDownloader, '_download_subtitles')
    def test_require_lang_prevents_fallback(self, mock_download):
        """Test require_lang flag prevents fallback."""
        mock_download.return_value = None

        downloader = TranscriptDownloader(
            lang="en",
            lang_fallback=["es", "fr"],
            require_lang=True
        )

        with patch.object(downloader, 'get_video_info') as mock_info:
            mock_info.return_value = VideoInfo(
                id="test123",
                title="Test Video",
                channel="Test Channel",
                upload_date="20240101",
                duration=100,
                view_count=1000,
                url="https://youtube.com/watch?v=test",
                description="Test description"
            )

            with pytest.raises(ValueError, match="No subtitles available for language 'en'"):
                downloader.download_transcript("https://youtube.com/watch?v=test")

    @patch.object(TranscriptDownloader, '_download_subtitles')
    def test_no_fallback_all_languages_fail(self, mock_download):
        """Test error when all fallback languages fail."""
        mock_download.return_value = None

        downloader = TranscriptDownloader(
            lang="en",
            lang_fallback=["es", "fr"]
        )

        with patch.object(downloader, 'get_video_info') as mock_info:
            mock_info.return_value = VideoInfo(
                id="test123",
                title="Test Video",
                channel="Test Channel",
                upload_date="20240101",
                duration=100,
                view_count=1000,
                url="https://youtube.com/watch?v=test",
                description="Test description"
            )

            with pytest.raises(ValueError, match="No subtitles available in any of the attempted languages"):
                downloader.download_transcript("https://youtube.com/watch?v=test")


class TestVideoInfo:
    """Tests for video info extraction."""

    @patch('yt_transcript_dl.downloader.yt_dlp.YoutubeDL')
    def test_get_video_info_success(self, mock_ydl_class):
        """Test successful video info extraction."""
        mock_ydl = MagicMock()
        mock_ydl_class.return_value.__enter__.return_value = mock_ydl

        mock_ydl.extract_info.return_value = {
            'id': 'test123',
            'title': 'Test Video Title',
            'channel': 'Test Channel',
            'upload_date': '20240101',
            'duration': 300,
            'view_count': 10000,
            'description': 'Test video description',
        }

        downloader = TranscriptDownloader()
        video_info = downloader.get_video_info("https://youtube.com/watch?v=test")

        assert video_info.id == 'test123'
        assert video_info.title == 'Test Video Title'
        assert video_info.channel == 'Test Channel'
        assert video_info.upload_date == '20240101'
        assert video_info.duration == 300
        assert video_info.view_count == 10000
        assert video_info.description == 'Test video description'

    @patch('yt_transcript_dl.downloader.yt_dlp.YoutubeDL')
    def test_get_video_info_error(self, mock_ydl_class):
        """Test error handling in video info extraction."""
        mock_ydl = MagicMock()
        mock_ydl_class.return_value.__enter__.return_value = mock_ydl
        mock_ydl.extract_info.side_effect = Exception("Network error")

        downloader = TranscriptDownloader()

        with pytest.raises(ValueError, match="Failed to extract video info"):
            downloader.get_video_info("https://youtube.com/watch?v=test")
