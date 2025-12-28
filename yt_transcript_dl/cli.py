"""Command-line interface for yt-transcript-dl."""

import logging
import sys
import time
from pathlib import Path

import click

from . import __version__
from .config import find_config_file, init_config_file, load_config, merge_config
from .downloader import TranscriptDownloader, URLType
from .formatters import get_formatter, get_file_extension, FORMATTERS
from .sync_state import SyncState
from .utils import format_filename, print_error, print_info, print_success, sanitize_filename


def save_transcript(result, base_filename, output_dir, formats, include_metadata=False, embed_description=False, overwrite=False):
    """
    Save transcript in specified format(s).

    Args:
        result: TranscriptResult object
        base_filename: Base filename without extension
        output_dir: Output directory Path
        formats: List of format names ('txt', 'srt', 'vtt', 'json')
        include_metadata: Whether to include metadata in output
        embed_description: Whether to include description in output (txt/json only)
        overwrite: Whether to overwrite existing files

    Returns:
        List of saved file paths
    """
    saved_files = []

    for fmt in formats:
        extension = get_file_extension(fmt)
        output_file = output_dir / f"{base_filename}.{extension}"

        # Check if file exists (skip unless overwrite enabled)
        if output_file.exists() and not overwrite:
            continue

        # Get formatter and format the output
        formatter = get_formatter(fmt)

        # Prepare formatter arguments
        kwargs = {
            'segments': result.segments,
            'video_info': result.video_info,
            'include_metadata': include_metadata,
            'language': result.language,
            'is_auto_generated': result.is_auto_generated,
            'embed_description': embed_description,
        }

        content = formatter(**kwargs)

        # Write output
        output_file.write_text(content, encoding='utf-8')
        saved_files.append(output_file)

    return saved_files


def download_with_retry(downloader, url, max_retries, logger=None):
    """
    Download transcript with retry logic.

    Args:
        downloader: TranscriptDownloader instance
        url: Video URL
        max_retries: Maximum number of retry attempts
        logger: Optional logger instance

    Returns:
        TranscriptResult on success

    Raises:
        Last exception encountered after all retries
    """
    last_error = None

    for attempt in range(1, max_retries + 1):
        try:
            if logger:
                logger.debug(f"Attempt {attempt}/{max_retries} for URL: {url}")

            result = downloader.download_transcript(url)

            if logger:
                logger.debug(f"Successfully downloaded transcript on attempt {attempt}")

            return result

        except Exception as e:
            last_error = e
            if logger:
                logger.warning(f"Attempt {attempt}/{max_retries} failed: {str(e)}")

            if attempt < max_retries:
                wait_time = 2 ** attempt  # Exponential backoff: 2s, 4s, 8s...
                if logger:
                    logger.debug(f"Waiting {wait_time}s before retry...")
                time.sleep(wait_time)
            else:
                if logger:
                    logger.error(f"All {max_retries} attempts failed for URL: {url}")

    raise last_error


@click.command()
@click.argument('url', required=False)
@click.option(
    '--lang', '-l',
    default='en',
    help='Language code for transcript (default: en)'
)
@click.option(
    '--lang-fallback',
    default=None,
    help='Comma-separated fallback language codes (e.g., "en,es,auto"). "auto" means any auto-generated caption.'
)
@click.option(
    '--require-lang',
    is_flag=True,
    default=False,
    help='Fail if preferred language is not available instead of falling back'
)
@click.option(
    '--list-langs',
    is_flag=True,
    default=False,
    help='List available caption languages for a video and exit'
)
@click.option(
    '--output-dir', '-o',
    type=click.Path(exists=False, file_okay=False, path_type=Path),
    default=None,
    help='Output directory (default: current directory)'
)
@click.option(
    '--include-metadata', '-m',
    is_flag=True,
    default=False,
    help='Include video metadata in output file'
)
@click.option(
    '--description', '-d',
    is_flag=True,
    default=False,
    help='Save video description to separate file'
)
@click.option(
    '--embed-description',
    is_flag=True,
    default=False,
    help='Include video description in the transcript file (txt/json only)'
)
@click.option(
    '--filename-pattern', '-p',
    default=None,
    help='Filename pattern using tokens: {title}, {channel}, {date}, {id}'
)
@click.option(
    '--input-file', '-i',
    type=click.Path(exists=True, file_okay=True, dir_okay=False, path_type=Path),
    default=None,
    help='File containing list of URLs (one per line)'
)
@click.option(
    '--verbose', '-v',
    is_flag=True,
    default=False,
    help='Enable verbose logging'
)
@click.option(
    '--log-file',
    type=click.Path(file_okay=True, dir_okay=False, path_type=Path),
    default=None,
    help='Save logs to file'
)
@click.option(
    '--retry',
    default=3,
    type=int,
    help='Number of retry attempts for failed downloads (default: 3)'
)
@click.option(
    '--delay',
    default=0,
    type=float,
    help='Delay in seconds between requests (default: 0)'
)
@click.option(
    '--version', '-V',
    is_flag=True,
    default=False,
    help='Show version and exit'
)
@click.option(
    '--format', '-f',
    type=click.Choice(['txt', 'srt', 'vtt', 'json', 'all'], case_sensitive=False),
    default='txt',
    help='Output format: txt, srt, vtt, json, or all (default: txt)'
)
@click.option(
    '--overwrite',
    is_flag=True,
    default=False,
    help='Force re-download of existing files'
)
@click.option(
    '--sync',
    is_flag=True,
    default=False,
    help='Only download videos newer than last sync'
)
@click.option(
    '--force-full',
    is_flag=True,
    default=False,
    help='Ignore sync state and download all videos'
)
@click.option(
    '--init-config',
    type=click.Path(file_okay=True, dir_okay=False, path_type=Path),
    default=None,
    help='Create sample configuration file at specified path'
)
@click.option(
    '--no-config',
    is_flag=True,
    default=False,
    help='Ignore configuration files'
)
def main(
    url: str | None,
    lang: str,
    lang_fallback: str | None,
    require_lang: bool,
    list_langs: bool,
    output_dir: Path | None,
    include_metadata: bool,
    description: bool,
    embed_description: bool,
    filename_pattern: str | None,
    input_file: Path | None,
    verbose: bool,
    log_file: Path | None,
    retry: int,
    delay: float,
    version: bool,
    format: str,
    overwrite: bool,
    sync: bool,
    force_full: bool,
    init_config: Path | None,
    no_config: bool,
) -> None:
    """
    Download YouTube video transcripts.

    URL: YouTube video URL to download transcript from (optional if using --input-file).

    \b
    Examples:
      yt-transcript-dl https://youtube.com/watch?v=xxxxx
      yt-transcript-dl https://youtu.be/xxxxx --lang es
      yt-transcript-dl https://youtube.com/watch?v=xxxxx --lang-fallback "en,es,auto"
      yt-transcript-dl https://youtube.com/watch?v=xxxxx --list-langs
      yt-transcript-dl https://youtube.com/watch?v=xxxxx --require-lang --lang es
      yt-transcript-dl https://youtube.com/watch?v=xxxxx -o ./transcripts
      yt-transcript-dl https://youtube.com/watch?v=xxxxx --description
      yt-transcript-dl https://youtube.com/watch?v=xxxxx -p "{channel}_{date}_{title}"
      yt-transcript-dl --input-file urls.txt -o ./transcripts
    """
    if version:
        click.echo(f"yt-transcript-dl {__version__}")
        sys.exit(0)

    # Handle --init-config
    if init_config:
        try:
            init_config_file(init_config)
            print_success(f"Configuration file created: {init_config}")
            sys.exit(0)
        except Exception as e:
            print_error(f"Failed to create configuration file: {e}")
            sys.exit(1)

    # Load configuration file (unless --no-config)
    config = {}
    if not no_config:
        config_file = find_config_file()
        if config_file:
            try:
                config = load_config(config_file)
                # Determine config type for user feedback
                if config_file.name == '.yt-transcript-dl.toml':
                    config_type = "project-specific"
                else:
                    config_type = "global"
                print_info(f"Loaded configuration from: {config_file} ({config_type})")
            except Exception as e:
                print_error(f"Failed to load configuration: {e}")
                sys.exit(1)

    # Merge config with CLI arguments (CLI flags override config)
    lang = merge_config(config, lang, 'lang', 'en')
    lang_fallback = merge_config(config, lang_fallback, 'lang_fallback', None)
    require_lang = merge_config(config, require_lang, 'require_lang', False)
    format = merge_config(config, format, 'format', 'txt')
    include_metadata = merge_config(config, include_metadata, 'include_metadata', False)
    description = merge_config(config, description, 'description', False)
    embed_description = merge_config(config, embed_description, 'embed_description', False)
    verbose = merge_config(config, verbose, 'verbose', False)
    retry = merge_config(config, retry, 'retry', 3)
    delay = merge_config(config, delay, 'delay', 0)
    overwrite = merge_config(config, overwrite, 'overwrite', False)
    sync = merge_config(config, sync, 'sync', False)

    # Merge path-based config values
    if output_dir is None and 'output_dir' in config and config['output_dir']:
        output_dir = Path(config['output_dir'])

    if log_file is None and 'log_file' in config and config['log_file']:
        log_file = Path(config['log_file'])

    # Parse lang_fallback from comma-separated string to list
    lang_fallback_list = []
    if lang_fallback:
        lang_fallback_list = [lang.strip() for lang in lang_fallback.split(',') if lang.strip()]

    # Get optional config values
    filename_pattern = merge_config(config, filename_pattern, 'filename_pattern', None)

    # Determine output formats
    if format == 'all':
        output_formats = ['txt', 'srt', 'vtt', 'json']
    else:
        output_formats = [format]

    # Validate flag combinations
    if sync and force_full:
        print_error("Cannot use both --sync and --force-full")
        sys.exit(1)

    # Setup logging
    log_level = logging.DEBUG if verbose else logging.INFO
    log_format = '%(asctime)s - %(levelname)s - %(message)s'

    handlers = []
    if log_file:
        handlers.append(logging.FileHandler(log_file, encoding='utf-8'))
    if verbose:
        handlers.append(logging.StreamHandler())

    if handlers:
        logging.basicConfig(
            level=log_level,
            format=log_format,
            handlers=handlers,
            force=True
        )
        logger = logging.getLogger(__name__)
    else:
        logger = None

    if logger and verbose:
        logger.info(f"Starting yt-transcript-dl {__version__}")
        logger.debug(f"Verbose logging enabled")
        logger.debug(f"Retry attempts: {retry}")
        logger.debug(f"Delay between requests: {delay}s")

    # Handle --list-langs (requires URL)
    if list_langs:
        if not url:
            print_error("--list-langs requires a video URL")
            sys.exit(1)

        if 'youtube.com' not in url and 'youtu.be' not in url:
            print_error("URL does not appear to be a YouTube link")
            sys.exit(1)

        try:
            downloader = TranscriptDownloader(lang=lang)
            langs_info = downloader.get_available_languages(url)

            print_info(f"\nAvailable caption languages for: {url}\n")

            if langs_info['manual']:
                print_success("Manual subtitles:")
                for lang_code in sorted(langs_info['manual']):
                    print(f"  - {lang_code}")
            else:
                print_info("  No manual subtitles available")

            print("")

            if langs_info['auto']:
                print_success("Auto-generated captions:")
                for lang_code in sorted(langs_info['auto']):
                    print(f"  - {lang_code}")
            else:
                print_info("  No auto-generated captions available")

            sys.exit(0)

        except ValueError as e:
            print_error(str(e))
            sys.exit(1)
        except Exception as e:
            print_error(f"Unexpected error: {e}")
            sys.exit(1)

    # Validate input
    if not url and not input_file:
        print_error("Either URL argument or --input-file option is required")
        sys.exit(1)

    if url and input_file:
        print_error("Cannot specify both URL argument and --input-file option")
        sys.exit(1)

    # Collect URLs to process
    urls_to_process = []
    if input_file:
        print_info(f"Reading URLs from: {input_file}")
        try:
            content = input_file.read_text(encoding='utf-8')
            for line in content.splitlines():
                line = line.strip()
                # Skip empty lines and comments
                if line and not line.startswith('#'):
                    urls_to_process.append(line)
        except Exception as e:
            print_error(f"Failed to read input file: {e}")
            sys.exit(1)

        if not urls_to_process:
            print_error("No valid URLs found in input file")
            sys.exit(1)

        print_info(f"Found {len(urls_to_process)} URLs to process")
    else:
        # Single URL mode
        if 'youtube.com' not in url and 'youtu.be' not in url:
            print_error("URL does not appear to be a YouTube link")
            sys.exit(1)
        urls_to_process.append(url)

    # Set output directory
    if output_dir is None:
        output_dir = Path.cwd()
    else:
        output_dir.mkdir(parents=True, exist_ok=True)

    # Initialize sync state
    sync_state_file = output_dir / '.sync_state.json'
    sync_state = SyncState(sync_state_file)

    if force_full:
        if logger:
            logger.info("Force-full mode: clearing sync state")
        sync_state.clear()

    # Initialize downloader
    downloader = TranscriptDownloader(
        lang=lang,
        lang_fallback=lang_fallback_list,
        require_lang=require_lang
    )

    # Batch processing mode
    if len(urls_to_process) > 1:
        print_info(f"Processing {len(urls_to_process)} URLs in batch mode...")

        total_success = 0
        total_skip = 0
        total_skip_sync = 0  # Skipped due to sync state
        total_error = 0

        for idx, batch_url in enumerate(urls_to_process, 1):
            print_info(f"\n[{idx}/{len(urls_to_process)}] Processing URL: {batch_url}")

            # Validate URL
            if 'youtube.com' not in batch_url and 'youtu.be' not in batch_url:
                print_error("URL does not appear to be a YouTube link, skipping")
                total_error += 1
                continue

            # Detect URL type
            url_type = downloader.detect_url_type(batch_url)

            # Process based on URL type (only videos supported in batch mode)
            if url_type != URLType.VIDEO:
                print_error("Only video URLs are supported in batch mode, skipping")
                total_error += 1
                continue

            try:
                if logger:
                    logger.info(f"Processing URL: {batch_url}")

                # Apply delay if specified
                if delay > 0 and idx > 1:
                    if logger:
                        logger.debug(f"Waiting {delay}s before request...")
                    time.sleep(delay)

                # Get video info first to check sync state
                video_info = downloader.get_video_info(batch_url)
                video_id = video_info.id

                # Check sync state (unless overwrite mode)
                if not overwrite and sync_state.is_downloaded(video_id):
                    print_info(f"Already downloaded (sync state), skipping")
                    total_skip_sync += 1
                    continue

                # Check if should download by date (sync mode)
                if sync and not sync_state.should_download_by_date(video_info.upload_date):
                    print_info(f"Older than last sync, skipping")
                    total_skip_sync += 1
                    continue

                result = download_with_retry(downloader, batch_url, retry, logger)

                # Generate filename
                if filename_pattern:
                    base_filename = format_filename(filename_pattern, result.video_info)
                else:
                    base_filename = sanitize_filename(result.video_info.title)

                # Check if any output file exists (for skipping)
                skip_file = False
                if not overwrite:
                    for fmt in output_formats:
                        ext = get_file_extension(fmt)
                        if (output_dir / f"{base_filename}.{ext}").exists():
                            skip_file = True
                            break

                if skip_file:
                    print_info(f"File already exists, skipping")
                    total_skip += 1
                    # Still mark as downloaded in sync state
                    sync_state.mark_downloaded(video_id)
                    continue

                # Save transcript in requested format(s)
                saved_files = save_transcript(
                    result, base_filename, output_dir,
                    output_formats, include_metadata, embed_description, overwrite
                )

                # Write description to separate file if requested
                if description and result.video_info.description:
                    description_file = output_dir / f"{base_filename}_description.txt"
                    if not description_file.exists() or overwrite:
                        description_file.write_text(result.video_info.description, encoding='utf-8')

                if saved_files:
                    for saved_file in saved_files:
                        print_success(f"Saved: {saved_file.name}")
                    # Mark as downloaded in sync state
                    sync_state.mark_downloaded(video_id)
                    total_success += 1

            except ValueError as e:
                error_msg = f"Failed: {str(e)}"
                print_error(error_msg)
                if logger:
                    logger.error(error_msg)
                total_error += 1
            except Exception as e:
                error_msg = f"Unexpected error: {e}"
                print_error(error_msg)
                if logger:
                    logger.exception("Unexpected error occurred")
                total_error += 1

        # Save sync state
        sync_state.save()

        # Print batch summary
        print_info("")
        print_info("=" * 50)
        print_info("Batch processing complete:")
        print_success(f"  Successfully saved: {total_success}")
        if total_skip > 0:
            print_info(f"  Skipped (existing files): {total_skip}")
        if total_skip_sync > 0:
            print_info(f"  Skipped (sync state): {total_skip_sync}")
        if total_error > 0:
            print_error(f"  Failed: {total_error}")
        print_info(f"  Total processed: {len(urls_to_process)}")
        print_info("=" * 50)

        sys.exit(0 if total_error == 0 else 1)

    # Single URL mode
    url = urls_to_process[0]

    # Detect URL type
    url_type = downloader.detect_url_type(url)

    try:
        if url_type == URLType.CHANNEL:
            # Handle channel URL
            print_info(f"Detected channel URL, enumerating videos...")

            # Collect all video URLs first to show total count
            video_urls = list(downloader.enumerate_channel_videos(url))
            total_videos = len(video_urls)

            if total_videos == 0:
                print_error("No videos found in channel")
                sys.exit(1)

            print_info(f"Found {total_videos} videos in channel")

            # Process each video with progress indication
            success_count = 0
            skip_count = 0
            skip_sync_count = 0
            error_count = 0

            for idx, video_url in enumerate(video_urls, 1):
                try:
                    print_info(f"[{idx}/{total_videos}] Processing: {video_url}")

                    if logger:
                        logger.info(f"Channel video {idx}/{total_videos}: {video_url}")

                    # Apply delay if specified
                    if delay > 0 and idx > 1:
                        if logger:
                            logger.debug(f"Waiting {delay}s before request...")
                        time.sleep(delay)

                    # Get video info first to check sync state
                    video_info = downloader.get_video_info(video_url)
                    video_id = video_info.id

                    # Check sync state (unless overwrite mode)
                    if not overwrite and sync_state.is_downloaded(video_id):
                        print_info(f"Already downloaded (sync state), skipping")
                        skip_sync_count += 1
                        continue

                    # Check if should download by date (sync mode)
                    if sync and not sync_state.should_download_by_date(video_info.upload_date):
                        print_info(f"Older than last sync, skipping")
                        skip_sync_count += 1
                        continue

                    result = download_with_retry(downloader, video_url, retry, logger)

                    # Generate filename
                    if filename_pattern:
                        base_filename = format_filename(filename_pattern, result.video_info)
                    else:
                        base_filename = sanitize_filename(result.video_info.title)

                    # Check if any output file exists (for skipping)
                    skip_file = False
                    if not overwrite:
                        for fmt in output_formats:
                            ext = get_file_extension(fmt)
                            if (output_dir / f"{base_filename}.{ext}").exists():
                                skip_file = True
                                break

                    if skip_file:
                        print_info(f"File already exists, skipping")
                        skip_count += 1
                        sync_state.mark_downloaded(result.video_info.id)
                        continue

                    # Save transcript in requested format(s)
                    saved_files = save_transcript(
                        result, base_filename, output_dir,
                        output_formats, include_metadata, embed_description, overwrite
                    )

                    # Write description to separate file if requested
                    if description and result.video_info.description:
                        description_file = output_dir / f"{base_filename}_description.txt"
                        if not description_file.exists() or overwrite:
                            description_file.write_text(result.video_info.description, encoding='utf-8')

                    if saved_files:
                        for saved_file in saved_files:
                            print_success(f"Saved: {saved_file.name}")
                        sync_state.mark_downloaded(result.video_info.id)
                        success_count += 1

                except ValueError as e:
                    error_msg = f"Failed: {str(e)}"
                    print_error(error_msg)
                    if logger:
                        logger.error(error_msg)
                    error_count += 1
                except Exception as e:
                    error_msg = f"Unexpected error: {e}"
                    print_error(error_msg)
                    if logger:
                        logger.exception("Unexpected error in channel processing")
                    error_count += 1

            # Save sync state
            sync_state.save()

            # Print summary
            print_info("")
            print_info(f"Channel processing complete:")
            print_success(f"  Successfully saved: {success_count}")
            if skip_count > 0:
                print_info(f"  Skipped (existing files): {skip_count}")
            if skip_sync_count > 0:
                print_info(f"  Skipped (sync state): {skip_sync_count}")
            if error_count > 0:
                print_error(f"  Failed: {error_count}")

            if logger:
                logger.info(f"Channel processing complete: {success_count} saved, {skip_count} skipped, {error_count} failed")

            sys.exit(0 if error_count == 0 else 1)

        elif url_type == URLType.PLAYLIST:
            # Handle playlist URL
            print_info(f"Detected playlist URL, enumerating videos...")

            # Collect all video URLs first to show total count
            video_urls = list(downloader.enumerate_playlist_videos(url))
            total_videos = len(video_urls)

            if total_videos == 0:
                print_error("No videos found in playlist")
                sys.exit(1)

            print_info(f"Found {total_videos} videos in playlist")

            # Process each video with progress indication
            success_count = 0
            skip_count = 0
            skip_sync_count = 0
            error_count = 0

            for idx, video_url in enumerate(video_urls, 1):
                try:
                    print_info(f"[{idx}/{total_videos}] Processing: {video_url}")

                    if logger:
                        logger.info(f"Playlist video {idx}/{total_videos}: {video_url}")

                    # Apply delay if specified
                    if delay > 0 and idx > 1:
                        if logger:
                            logger.debug(f"Waiting {delay}s before request...")
                        time.sleep(delay)

                    # Get video info first to check sync state
                    video_info = downloader.get_video_info(video_url)
                    video_id = video_info.id

                    # Check sync state (unless overwrite mode)
                    if not overwrite and sync_state.is_downloaded(video_id):
                        print_info(f"Already downloaded (sync state), skipping")
                        skip_sync_count += 1
                        continue

                    # Check if should download by date (sync mode)
                    if sync and not sync_state.should_download_by_date(video_info.upload_date):
                        print_info(f"Older than last sync, skipping")
                        skip_sync_count += 1
                        continue

                    result = download_with_retry(downloader, video_url, retry, logger)

                    # Generate filename
                    if filename_pattern:
                        base_filename = format_filename(filename_pattern, result.video_info)
                    else:
                        base_filename = sanitize_filename(result.video_info.title)

                    # Check if any output file exists (for skipping)
                    skip_file = False
                    if not overwrite:
                        for fmt in output_formats:
                            ext = get_file_extension(fmt)
                            if (output_dir / f"{base_filename}.{ext}").exists():
                                skip_file = True
                                break

                    if skip_file:
                        print_info(f"File already exists, skipping")
                        skip_count += 1
                        sync_state.mark_downloaded(result.video_info.id)
                        continue

                    # Save transcript in requested format(s)
                    saved_files = save_transcript(
                        result, base_filename, output_dir,
                        output_formats, include_metadata, embed_description, overwrite
                    )

                    # Write description to separate file if requested
                    if description and result.video_info.description:
                        description_file = output_dir / f"{base_filename}_description.txt"
                        if not description_file.exists() or overwrite:
                            description_file.write_text(result.video_info.description, encoding='utf-8')

                    if saved_files:
                        for saved_file in saved_files:
                            print_success(f"Saved: {saved_file.name}")
                        sync_state.mark_downloaded(result.video_info.id)
                        success_count += 1

                except ValueError as e:
                    error_msg = f"Failed: {str(e)}"
                    print_error(error_msg)
                    if logger:
                        logger.error(error_msg)
                    error_count += 1
                except Exception as e:
                    error_msg = f"Unexpected error: {e}"
                    print_error(error_msg)
                    if logger:
                        logger.exception("Unexpected error in playlist processing")
                    error_count += 1

            # Save sync state
            sync_state.save()

            # Print summary
            print_info("")
            print_info(f"Playlist processing complete:")
            print_success(f"  Successfully saved: {success_count}")
            if skip_count > 0:
                print_info(f"  Skipped (existing files): {skip_count}")
            if skip_sync_count > 0:
                print_info(f"  Skipped (sync state): {skip_sync_count}")
            if error_count > 0:
                print_error(f"  Failed: {error_count}")

            if logger:
                logger.info(f"Playlist processing complete: {success_count} saved, {skip_count} skipped, {error_count} failed")

            sys.exit(0 if error_count == 0 else 1)

        elif url_type == URLType.UNKNOWN:
            print_error("Unable to detect URL type. Please provide a valid YouTube video or channel URL.")
            sys.exit(1)

        # Handle single video URL
        print_info(f"Fetching transcript for: {url}")

        if logger:
            logger.info(f"Processing single video URL: {url}")

        # Get video info first to check sync state
        video_info = downloader.get_video_info(url)
        video_id = video_info.id

        # Check sync state (unless overwrite mode)
        if not overwrite and sync_state.is_downloaded(video_id):
            print_info(f"Already downloaded (sync state), skipping")
            sys.exit(0)

        # Check if should download by date (sync mode)
        if sync and not sync_state.should_download_by_date(video_info.upload_date):
            print_info(f"Older than last sync, skipping")
            sys.exit(0)

        result = download_with_retry(downloader, url, retry, logger)

        # Generate output filename
        if filename_pattern:
            base_filename = format_filename(filename_pattern, result.video_info)
        else:
            base_filename = sanitize_filename(result.video_info.title)

        # Check if any output file exists (for skipping)
        skip_file = False
        if not overwrite:
            for fmt in output_formats:
                ext = get_file_extension(fmt)
                if (output_dir / f"{base_filename}.{ext}").exists():
                    skip_file = True
                    break

        if skip_file:
            print_info(f"File already exists, skipping")
            sync_state.mark_downloaded(video_id)
            sync_state.save()
            sys.exit(0)

        # Save transcript in requested format(s)
        saved_files = save_transcript(
            result, base_filename, output_dir,
            output_formats, include_metadata, embed_description, overwrite
        )

        # Print success messages
        for saved_file in saved_files:
            print_success(f"Transcript saved to: {saved_file}")

        # Write description to separate file if requested
        if description and result.video_info.description:
            description_file = output_dir / f"{base_filename}_description.txt"
            if description_file.exists() and not overwrite:
                print_info(f"Description file already exists, skipping: {description_file}")
            else:
                description_file.write_text(result.video_info.description, encoding='utf-8')
                print_success(f"Description saved to: {description_file}")

        # Mark as downloaded and save sync state
        sync_state.mark_downloaded(video_id)
        sync_state.save()

    except ValueError as e:
        print_error(str(e))
        sys.exit(1)
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
