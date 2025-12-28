"""Tests for configuration file support."""

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from yt_transcript_dl.config import (
    DEFAULT_CONFIG,
    find_config_file,
    init_config_file,
    load_config,
    merge_config,
)


class TestInitConfigFile:
    """Tests for init_config_file function."""

    def test_creates_config_file(self, tmp_path):
        """Test that config file is created with default content."""
        config_path = tmp_path / "test-config.toml"
        init_config_file(config_path)

        assert config_path.exists()
        content = config_path.read_text()
        assert "yt-transcript-dl configuration" in content
        assert "lang = " in content

    def test_creates_parent_directories(self, tmp_path):
        """Test that parent directories are created if they don't exist."""
        config_path = tmp_path / "subdir" / "another" / "config.toml"
        init_config_file(config_path)

        assert config_path.exists()
        assert config_path.parent.exists()

    def test_config_content_matches_default(self, tmp_path):
        """Test that created config matches DEFAULT_CONFIG constant."""
        config_path = tmp_path / "config.toml"
        init_config_file(config_path)

        content = config_path.read_text()
        assert content == DEFAULT_CONFIG

    def test_overwrites_existing_file(self, tmp_path):
        """Test that existing file is overwritten."""
        config_path = tmp_path / "config.toml"
        config_path.write_text("old content")

        init_config_file(config_path)

        content = config_path.read_text()
        assert content == DEFAULT_CONFIG
        assert "old content" not in content


class TestLoadConfig:
    """Tests for load_config function."""

    def test_loads_valid_toml(self, tmp_path):
        """Test loading a valid TOML configuration."""
        config_path = tmp_path / "config.toml"
        config_path.write_text("""
lang = "es"
format = "srt"
retry = 5
verbose = true
delay = 1.5
""")

        config = load_config(config_path)

        assert config["lang"] == "es"
        assert config["format"] == "srt"
        assert config["retry"] == 5
        assert config["verbose"] is True
        assert config["delay"] == 1.5

    def test_empty_file_returns_empty_dict(self, tmp_path):
        """Test that empty file returns empty dictionary."""
        config_path = tmp_path / "config.toml"
        config_path.write_text("")

        config = load_config(config_path)

        assert config == {}

    def test_nonexistent_file_returns_empty_dict(self, tmp_path):
        """Test that nonexistent file returns empty dictionary."""
        config_path = tmp_path / "nonexistent.toml"

        config = load_config(config_path)

        assert config == {}

    def test_invalid_toml_raises_exception(self, tmp_path):
        """Test that invalid TOML raises an exception."""
        config_path = tmp_path / "config.toml"
        config_path.write_text("invalid toml { [ content")

        with pytest.raises(Exception):
            load_config(config_path)

    def test_loads_all_config_types(self, tmp_path):
        """Test loading various TOML data types."""
        config_path = tmp_path / "config.toml"
        config_path.write_text("""
string_val = "hello"
int_val = 42
float_val = 3.14
bool_val = true
empty_string = ""
""")

        config = load_config(config_path)

        assert config["string_val"] == "hello"
        assert config["int_val"] == 42
        assert config["float_val"] == 3.14
        assert config["bool_val"] is True
        assert config["empty_string"] == ""

    @pytest.mark.skipif(sys.version_info >= (3, 11), reason="tomllib built-in for Python 3.11+")
    def test_missing_tomli_raises_error(self, tmp_path):
        """Test that missing tomli library raises appropriate error."""
        config_path = tmp_path / "config.toml"
        config_path.write_text("lang = 'en'")

        with patch("yt_transcript_dl.config.tomllib", None):
            with pytest.raises(ValueError, match="TOML support not available"):
                load_config(config_path)

    def test_unicode_content(self, tmp_path):
        """Test loading config with unicode characters."""
        config_path = tmp_path / "config.toml"
        config_path.write_text("""
lang = "日本語"
filename_pattern = "{title}_🎥_{date}"
""", encoding='utf-8')

        config = load_config(config_path)

        assert config["lang"] == "日本語"
        assert config["filename_pattern"] == "{title}_🎥_{date}"


class TestFindConfigFile:
    """Tests for find_config_file function."""

    def test_finds_local_config(self, tmp_path, monkeypatch):
        """Test that local .yt-transcript-dl.toml is found first."""
        # Create local config
        local_config = tmp_path / ".yt-transcript-dl.toml"
        local_config.write_text("lang = 'local'")

        # Create global config
        global_config_dir = tmp_path / ".config" / "yt-transcript-dl"
        global_config_dir.mkdir(parents=True)
        global_config = global_config_dir / "config.toml"
        global_config.write_text("lang = 'global'")

        # Mock current directory and home
        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr(Path, "home", lambda: tmp_path)

        result = find_config_file()

        assert result == local_config

    def test_finds_global_config_when_no_local(self, tmp_path, monkeypatch):
        """Test that global config is found when no local config exists."""
        # Create only global config
        global_config_dir = tmp_path / ".config" / "yt-transcript-dl"
        global_config_dir.mkdir(parents=True)
        global_config = global_config_dir / "config.toml"
        global_config.write_text("lang = 'global'")

        # Mock current directory and home
        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr(Path, "home", lambda: tmp_path)

        result = find_config_file()

        assert result == global_config

    def test_returns_none_when_no_config_exists(self, tmp_path, monkeypatch):
        """Test that None is returned when no config exists."""
        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr(Path, "home", lambda: tmp_path)

        result = find_config_file()

        assert result is None

    def test_local_config_has_priority(self, tmp_path, monkeypatch):
        """Test that local config is prioritized over global."""
        # Create both configs
        local_config = tmp_path / ".yt-transcript-dl.toml"
        local_config.write_text("# local")

        global_config_dir = tmp_path / ".config" / "yt-transcript-dl"
        global_config_dir.mkdir(parents=True)
        global_config = global_config_dir / "config.toml"
        global_config.write_text("# global")

        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr(Path, "home", lambda: tmp_path)

        result = find_config_file()

        # Should return local, not global
        assert result == local_config
        assert result != global_config


class TestMergeConfig:
    """Tests for merge_config function."""

    def test_cli_value_overrides_config(self):
        """Test that CLI value overrides config when different from default."""
        config = {"lang": "es"}
        cli_value = "fr"
        cli_default = "en"

        result = merge_config(config, cli_value, "lang", cli_default)

        assert result == "fr"

    def test_config_value_used_when_cli_is_default(self):
        """Test that config value is used when CLI value is the default."""
        config = {"lang": "es"}
        cli_value = "en"  # Same as default
        cli_default = "en"

        result = merge_config(config, cli_value, "lang", cli_default)

        assert result == "es"

    def test_cli_default_used_when_no_config_key(self):
        """Test that CLI default is used when config doesn't have the key."""
        config = {}
        cli_value = "en"
        cli_default = "en"

        result = merge_config(config, cli_value, "lang", cli_default)

        assert result == "en"

    def test_boolean_values(self):
        """Test merge_config with boolean values."""
        config = {"verbose": True}
        cli_value = False  # Default
        cli_default = False

        result = merge_config(config, cli_value, "verbose", cli_default)

        assert result is True

    def test_integer_values(self):
        """Test merge_config with integer values."""
        config = {"retry": 10}
        cli_value = 3  # Default
        cli_default = 3

        result = merge_config(config, cli_value, "retry", cli_default)

        assert result == 10

    def test_float_values(self):
        """Test merge_config with float values."""
        config = {"delay": 2.5}
        cli_value = 0.0  # Default
        cli_default = 0.0

        result = merge_config(config, cli_value, "delay", cli_default)

        assert result == 2.5

    def test_cli_explicit_false_overrides_config(self):
        """Test that explicitly set CLI false value overrides config."""
        config = {"verbose": True}
        cli_value = False
        cli_default = True  # Different default

        result = merge_config(config, cli_value, "verbose", cli_default)

        assert result is False

    def test_cli_explicit_zero_overrides_config(self):
        """Test that explicitly set CLI zero value overrides config."""
        config = {"retry": 5}
        cli_value = 0
        cli_default = 3  # Different default

        result = merge_config(config, cli_value, "retry", cli_default)

        assert result == 0

    def test_string_values_with_empty_string(self):
        """Test that empty string in CLI doesn't override config."""
        config = {"lang_fallback": "en,es"}
        cli_value = ""  # Empty default
        cli_default = ""

        result = merge_config(config, cli_value, "lang_fallback", cli_default)

        assert result == "en,es"

    def test_none_values(self):
        """Test merge_config with None values."""
        config = {"filename_pattern": "{title}"}
        cli_value = None  # Default
        cli_default = None

        result = merge_config(config, cli_value, "filename_pattern", cli_default)

        assert result == "{title}"

    def test_cli_none_does_not_override_when_different_default(self):
        """Test that CLI None doesn't override when default is different."""
        config = {"output_dir": "./transcripts"}
        cli_value = None
        cli_default = "."  # Different default

        result = merge_config(config, cli_value, "output_dir", cli_default)

        # CLI value is None, default is ".", so should use config
        assert result == "./transcripts"


class TestDefaultConfig:
    """Tests for DEFAULT_CONFIG constant."""

    def test_default_config_is_valid_toml(self, tmp_path):
        """Test that DEFAULT_CONFIG is valid TOML."""
        config_path = tmp_path / "config.toml"
        config_path.write_text(DEFAULT_CONFIG)

        # Should not raise an exception
        config = load_config(config_path)
        assert isinstance(config, dict)

    def test_default_config_contains_all_keys(self, tmp_path):
        """Test that DEFAULT_CONFIG contains all expected configuration keys."""
        config_path = tmp_path / "config.toml"
        config_path.write_text(DEFAULT_CONFIG)

        config = load_config(config_path)

        expected_keys = {
            "lang",
            "lang_fallback",
            "require_lang",
            "output_dir",
            "format",
            "filename_pattern",
            "include_metadata",
            "description",
            "embed_description",
            "verbose",
            "log_file",
            "retry",
            "delay",
            "overwrite",
            "sync",
        }

        assert set(config.keys()) == expected_keys

    def test_default_config_has_correct_types(self, tmp_path):
        """Test that DEFAULT_CONFIG values have correct types."""
        config_path = tmp_path / "config.toml"
        config_path.write_text(DEFAULT_CONFIG)

        config = load_config(config_path)

        # String values
        assert isinstance(config["lang"], str)
        assert isinstance(config["lang_fallback"], str)
        assert isinstance(config["output_dir"], str)
        assert isinstance(config["format"], str)
        assert isinstance(config["filename_pattern"], str)
        assert isinstance(config["log_file"], str)

        # Boolean values
        assert isinstance(config["require_lang"], bool)
        assert isinstance(config["include_metadata"], bool)
        assert isinstance(config["description"], bool)
        assert isinstance(config["embed_description"], bool)
        assert isinstance(config["verbose"], bool)
        assert isinstance(config["overwrite"], bool)
        assert isinstance(config["sync"], bool)

        # Numeric values
        assert isinstance(config["retry"], int)
        assert isinstance(config["delay"], float)

    def test_default_config_has_expected_defaults(self, tmp_path):
        """Test that DEFAULT_CONFIG has sensible default values."""
        config_path = tmp_path / "config.toml"
        config_path.write_text(DEFAULT_CONFIG)

        config = load_config(config_path)

        # Check specific default values
        assert config["lang"] == "en"
        assert config["format"] == "txt"
        assert config["retry"] == 3
        assert config["delay"] == 0.0
        assert config["verbose"] is False
        assert config["overwrite"] is False
        assert config["sync"] is False


class TestConfigIntegration:
    """Integration tests for configuration system."""

    def test_full_workflow(self, tmp_path, monkeypatch):
        """Test complete workflow: create, find, load, merge config."""
        # Setup
        config_dir = tmp_path / ".config" / "yt-transcript-dl"
        config_dir.mkdir(parents=True)
        config_path = config_dir / "config.toml"

        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr(Path, "home", lambda: tmp_path)

        # 1. Create config
        init_config_file(config_path)
        assert config_path.exists()

        # 2. Modify config
        config_content = config_path.read_text()
        config_content = config_content.replace('lang = "en"', 'lang = "es"')
        config_content = config_content.replace('retry = 3', 'retry = 5')
        config_path.write_text(config_content)

        # 3. Find config
        found_config = find_config_file()
        assert found_config == config_path

        # 4. Load config
        config = load_config(found_config)
        assert config["lang"] == "es"
        assert config["retry"] == 5

        # 5. Merge with CLI values
        # CLI keeps default, so use config
        lang = merge_config(config, "en", "lang", "en")
        assert lang == "es"

        # CLI overrides config
        retry = merge_config(config, 10, "retry", 3)
        assert retry == 10

    def test_project_overrides_global(self, tmp_path, monkeypatch):
        """Test that project config overrides global config."""
        # Setup directories
        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr(Path, "home", lambda: tmp_path)

        # Create global config
        global_config_dir = tmp_path / ".config" / "yt-transcript-dl"
        global_config_dir.mkdir(parents=True)
        global_config_path = global_config_dir / "config.toml"
        global_config_path.write_text('lang = "en"\nretry = 3')

        # Create project config
        project_config_path = tmp_path / ".yt-transcript-dl.toml"
        project_config_path.write_text('lang = "fr"\nformat = "srt"')

        # Find config (should find project config)
        found_config = find_config_file()
        assert found_config == project_config_path

        # Load and verify
        config = load_config(found_config)
        assert config["lang"] == "fr"
        assert config["format"] == "srt"
        assert "retry" not in config  # Not in project config
