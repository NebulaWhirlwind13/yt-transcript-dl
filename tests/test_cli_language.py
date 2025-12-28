"""Tests for CLI language selection options."""

import pytest
from click.testing import CliRunner
from unittest.mock import patch, MagicMock

from yt_transcript_dl.cli import main
from yt_transcript_dl.downloader import VideoInfo


class TestCLILanguageOptions:
    """Tests for CLI language selection and fallback options."""

    def test_lang_fallback_parsing(self):
        """Test that --lang-fallback parses comma-separated values correctly."""
        runner = CliRunner()

        with patch('yt_transcript_dl.cli.TranscriptDownloader') as mock_downloader_class:
            mock_downloader = MagicMock()
            mock_downloader_class.return_value = mock_downloader

            # Mock the methods
            mock_downloader.detect_url_type.return_value = 1  # VIDEO
            mock_downloader.get_video_info.return_value = VideoInfo(
                id="test123",
                title="Test Video",
                channel="Test Channel",
                upload_date="20240101",
                duration=100,
                view_count=1000,
                url="https://youtube.com/watch?v=test",
                description="Test"
            )
            mock_downloader.download_transcript.return_value = MagicMock(
                video_info=mock_downloader.get_video_info.return_value,
                transcript="Test transcript",
                segments=[],
                language="en",
                is_auto_generated=False
            )

            result = runner.invoke(main, [
                'https://youtube.com/watch?v=test',
                '--lang-fallback', 'en,es,auto',
                '--no-config'
            ])

            # Check that downloader was initialized with correct fallback list
            call_kwargs = mock_downloader_class.call_args[1]
            assert call_kwargs['lang_fallback'] == ['en', 'es', 'auto']

    def test_require_lang_flag(self):
        """Test that --require-lang flag is passed to downloader."""
        runner = CliRunner()

        with patch('yt_transcript_dl.cli.TranscriptDownloader') as mock_downloader_class:
            mock_downloader = MagicMock()
            mock_downloader_class.return_value = mock_downloader

            # Mock the methods
            mock_downloader.detect_url_type.return_value = 1  # VIDEO
            mock_downloader.get_video_info.return_value = VideoInfo(
                id="test123",
                title="Test Video",
                channel="Test Channel",
                upload_date="20240101",
                duration=100,
                view_count=1000,
                url="https://youtube.com/watch?v=test",
                description="Test"
            )
            mock_downloader.download_transcript.return_value = MagicMock(
                video_info=mock_downloader.get_video_info.return_value,
                transcript="Test transcript",
                segments=[],
                language="en",
                is_auto_generated=False
            )

            result = runner.invoke(main, [
                'https://youtube.com/watch?v=test',
                '--require-lang',
                '--no-config'
            ])

            # Check that downloader was initialized with require_lang=True
            call_kwargs = mock_downloader_class.call_args[1]
            assert call_kwargs['require_lang'] is True

    def test_list_langs_option(self):
        """Test that --list-langs displays available languages and exits."""
        runner = CliRunner()

        with patch('yt_transcript_dl.cli.TranscriptDownloader') as mock_downloader_class:
            mock_downloader = MagicMock()
            mock_downloader_class.return_value = mock_downloader

            # Mock get_available_languages
            mock_downloader.get_available_languages.return_value = {
                'manual': ['en', 'es', 'fr'],
                'auto': ['en', 'de', 'ja']
            }

            result = runner.invoke(main, [
                'https://youtube.com/watch?v=test',
                '--list-langs',
                '--no-config'
            ])

            # Check output contains language codes
            assert 'Manual subtitles:' in result.output
            assert 'Auto-generated captions:' in result.output
            assert 'en' in result.output
            assert 'es' in result.output
            assert 'de' in result.output
            assert result.exit_code == 0

    def test_list_langs_no_manual_subtitles(self):
        """Test --list-langs when only auto-generated captions are available."""
        runner = CliRunner()

        with patch('yt_transcript_dl.cli.TranscriptDownloader') as mock_downloader_class:
            mock_downloader = MagicMock()
            mock_downloader_class.return_value = mock_downloader

            # Mock get_available_languages
            mock_downloader.get_available_languages.return_value = {
                'manual': [],
                'auto': ['en', 'de']
            }

            result = runner.invoke(main, [
                'https://youtube.com/watch?v=test',
                '--list-langs',
                '--no-config'
            ])

            # Check output
            assert 'No manual subtitles available' in result.output
            assert 'Auto-generated captions:' in result.output
            assert result.exit_code == 0

    def test_list_langs_requires_url(self):
        """Test that --list-langs requires a URL argument."""
        runner = CliRunner()

        result = runner.invoke(main, [
            '--list-langs',
            '--no-config'
        ])

        assert 'requires a video URL' in result.output
        assert result.exit_code == 1

    def test_list_langs_error_handling(self):
        """Test error handling in --list-langs."""
        runner = CliRunner()

        with patch('yt_transcript_dl.cli.TranscriptDownloader') as mock_downloader_class:
            mock_downloader = MagicMock()
            mock_downloader_class.return_value = mock_downloader

            # Mock get_available_languages to raise error
            mock_downloader.get_available_languages.side_effect = ValueError("Network error")

            result = runner.invoke(main, [
                'https://youtube.com/watch?v=test',
                '--list-langs',
                '--no-config'
            ])

            assert 'Network error' in result.output
            assert result.exit_code == 1
