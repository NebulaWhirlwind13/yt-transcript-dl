# Language Selection & Fallback

This document describes the language selection and fallback features implemented in Story 2.3.

## Features

### 1. Language Fallback (`--lang-fallback`)

Specify a comma-separated list of fallback language codes. The tool will try each language in order until it finds available subtitles.

**Syntax:**
```bash
yt-transcript-dl <url> --lang-fallback "en,es,fr,auto"
```

**Example:**
```bash
# Try English, then Spanish, then any auto-generated captions
yt-transcript-dl https://youtube.com/watch?v=xxxxx --lang-fallback "en,es,auto"
```

**Special Keyword: `auto`**
- The `auto` keyword means "any auto-generated caption in any language"
- When `auto` is encountered in the fallback chain, the tool will download the first available auto-generated caption
- Preference order for `auto`: English variants first, then alphabetically

### 2. List Available Languages (`--list-langs`)

Display all available caption languages for a video without downloading anything.

**Syntax:**
```bash
yt-transcript-dl <url> --list-langs
```

**Example:**
```bash
yt-transcript-dl https://youtube.com/watch?v=xxxxx --list-langs
```

**Output:**
```
Available caption languages for: https://youtube.com/watch?v=xxxxx

Manual subtitles:
  - en
  - es
  - fr

Auto-generated captions:
  - de
  - en
  - ja
```

### 3. Require Language (`--require-lang`)

Fail if the preferred language is not available instead of falling back to other languages.

**Syntax:**
```bash
yt-transcript-dl <url> --lang es --require-lang
```

**Example:**
```bash
# Fail if Spanish subtitles are not available
yt-transcript-dl https://youtube.com/watch?v=xxxxx --lang es --require-lang
```

**Behavior:**
- Only tries the language specified with `--lang`
- Does not fall back to auto-generated captions or other languages
- Exits with clear error message if language is not available

## Default Behavior

**Without fallback options:**
1. Try manual subtitles in preferred language (`--lang`, default: `en`)
2. Try auto-generated captions in preferred language
3. Fail if neither is available

**With fallback options:**
1. Try manual subtitles in preferred language
2. Try auto-generated captions in preferred language
3. Try each fallback language (manual first, then auto)
4. If `auto` is in fallback list, try any auto-generated caption
5. Fail if no language in the chain is available

## Usage Examples

### Example 1: Basic Fallback
Try English, then Spanish, then any auto-generated:
```bash
yt-transcript-dl https://youtube.com/watch?v=xxxxx --lang-fallback "en,es,auto"
```

### Example 2: Strict Language Requirement
Only accept Spanish manual subtitles:
```bash
yt-transcript-dl https://youtube.com/watch?v=xxxxx --lang es --require-lang
```

### Example 3: Check Available Languages First
```bash
# First, list available languages
yt-transcript-dl https://youtube.com/watch?v=xxxxx --list-langs

# Then download with appropriate fallback
yt-transcript-dl https://youtube.com/watch?v=xxxxx --lang-fallback "fr,de,en"
```

### Example 4: Batch Processing with Fallback
```bash
# Process multiple videos with fallback
yt-transcript-dl --input-file urls.txt --lang-fallback "en,es,auto" -o ./transcripts
```

### Example 5: Configuration File
Add to `.yt-transcript-dl.yaml`:
```yaml
lang: en
lang_fallback: "es,fr,auto"
```

Then run:
```bash
yt-transcript-dl https://youtube.com/watch?v=xxxxx
```

## Metadata Output

When downloading transcripts, the selected language is included in metadata output:

**JSON format:**
```json
{
  "video_info": { ... },
  "language": "es",
  "is_auto_generated": false,
  "transcript": "..."
}
```

**Text format with metadata:**
```
Title: Video Title
Channel: Channel Name
Language: es (manual)
...
```

## Error Messages

**No matching language found:**
```
Error: No subtitles available in any of the attempted languages: en, es, auto.
Use --list-langs to see available languages.
```

**Require language mode:**
```
Error: No subtitles available for language 'es'.
Use --list-langs to see available languages.
```

## Implementation Notes

- Language selection respects the order specified in `--lang-fallback`
- Manual subtitles are always tried before auto-generated for each language
- The `auto` keyword provides maximum flexibility for content in any language
- Selected language is tracked in metadata for reference
- All language codes follow ISO 639-1 standard (e.g., 'en', 'es', 'fr')
