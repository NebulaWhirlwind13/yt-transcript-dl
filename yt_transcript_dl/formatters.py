"""Output format handlers for transcripts."""

import json
from typing import List

from .downloader import TranscriptSegment, VideoInfo


def format_time_srt(seconds: float) -> str:
    """
    Format time in SRT format (HH:MM:SS,mmm).

    Args:
        seconds: Time in seconds

    Returns:
        Formatted time string
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millisecs = int((seconds % 1) * 1000)

    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millisecs:03d}"


def format_time_vtt(seconds: float) -> str:
    """
    Format time in VTT format (HH:MM:SS.mmm).

    Args:
        seconds: Time in seconds

    Returns:
        Formatted time string
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millisecs = int((seconds % 1) * 1000)

    return f"{hours:02d}:{minutes:02d}:{secs:02d}.{millisecs:03d}"


def format_txt(
    segments: List[TranscriptSegment],
    video_info: VideoInfo | None = None,
    include_metadata: bool = False,
    language: str | None = None,
    is_auto_generated: bool = False,
    embed_description: bool = False,
    **kwargs
) -> str:
    """
    Format transcript as plain text.

    Args:
        segments: List of transcript segments
        video_info: Optional video metadata
        include_metadata: Whether to include video metadata header
        language: Language code
        is_auto_generated: Whether transcript is auto-generated
        embed_description: Whether to include video description in output

    Returns:
        Plain text transcript
    """
    lines = []

    if include_metadata and video_info:
        lines.append(f"# {video_info.title}")
        lines.append("")
        lines.append(f"**Channel:** {video_info.channel}")
        lines.append(f"**URL:** {video_info.url}")
        if video_info.upload_date:
            date_str = f"{video_info.upload_date[:4]}-{video_info.upload_date[4:6]}-{video_info.upload_date[6:]}"
            lines.append(f"**Upload Date:** {date_str}")
        if video_info.duration:
            mins, secs = divmod(video_info.duration, 60)
            hours, mins = divmod(mins, 60)
            if hours:
                lines.append(f"**Duration:** {hours}h {mins}m {secs}s")
            else:
                lines.append(f"**Duration:** {mins}m {secs}s")
        if language:
            lang_type = "auto-generated" if is_auto_generated else "manual"
            lines.append(f"**Language:** {language} ({lang_type})")
        lines.append("")
        lines.append("---")
        lines.append("")

    # Include description if requested
    if embed_description and video_info and video_info.description:
        lines.append("## Description")
        lines.append("")
        lines.append(video_info.description)
        lines.append("")
        lines.append("---")
        lines.append("")

    # Combine all segment text
    text = ' '.join(segment.text for segment in segments)
    lines.append(text)

    return '\n'.join(lines)


def format_srt(segments: List[TranscriptSegment], **kwargs) -> str:
    """
    Format transcript as SRT (SubRip) format.

    Args:
        segments: List of transcript segments
        **kwargs: Additional arguments (ignored for SRT format)

    Returns:
        SRT formatted transcript
    """
    lines = []

    for idx, segment in enumerate(segments, 1):
        lines.append(str(idx))
        lines.append(f"{format_time_srt(segment.start)} --> {format_time_srt(segment.end)}")
        lines.append(segment.text)
        lines.append("")

    return '\n'.join(lines)


def format_vtt(segments: List[TranscriptSegment], **kwargs) -> str:
    """
    Format transcript as WebVTT format.

    Args:
        segments: List of transcript segments
        **kwargs: Additional arguments (ignored for VTT format)

    Returns:
        VTT formatted transcript
    """
    lines = ["WEBVTT", ""]

    for segment in segments:
        lines.append(f"{format_time_vtt(segment.start)} --> {format_time_vtt(segment.end)}")
        lines.append(segment.text)
        lines.append("")

    return '\n'.join(lines)


def format_json(
    segments: List[TranscriptSegment],
    video_info: VideoInfo | None = None,
    language: str | None = None,
    is_auto_generated: bool = False,
    embed_description: bool = False,
    **kwargs
) -> str:
    """
    Format transcript as JSON.

    Args:
        segments: List of transcript segments
        video_info: Optional video metadata
        language: Language code
        is_auto_generated: Whether transcript is auto-generated
        embed_description: Whether to include video description in output
        **kwargs: Additional arguments (ignored)

    Returns:
        JSON formatted transcript
    """
    data = {
        "segments": [
            {
                "start": segment.start,
                "end": segment.end,
                "text": segment.text
            }
            for segment in segments
        ]
    }

    if video_info:
        metadata = {
            "id": video_info.id,
            "title": video_info.title,
            "channel": video_info.channel,
            "url": video_info.url,
            "upload_date": video_info.upload_date,
            "duration": video_info.duration,
            "view_count": video_info.view_count,
        }

        if language:
            metadata["language"] = language

        if language is not None:
            metadata["is_auto_generated"] = is_auto_generated

        if embed_description and video_info.description:
            metadata["description"] = video_info.description

        data["metadata"] = metadata

    return json.dumps(data, indent=2, ensure_ascii=False)


# Format registry
FORMATTERS = {
    'txt': format_txt,
    'srt': format_srt,
    'vtt': format_vtt,
    'json': format_json,
}


def get_formatter(format_name: str):
    """
    Get formatter function by name.

    Args:
        format_name: Format name (txt, srt, vtt, json)

    Returns:
        Formatter function

    Raises:
        ValueError: If format is not supported
    """
    if format_name not in FORMATTERS:
        raise ValueError(f"Unsupported format: {format_name}. Supported formats: {', '.join(FORMATTERS.keys())}")

    return FORMATTERS[format_name]


def get_file_extension(format_name: str) -> str:
    """
    Get file extension for format.

    Args:
        format_name: Format name

    Returns:
        File extension (without dot)
    """
    return format_name
