# AGENTS.md - Agentic Coding Guidelines

This document provides guidelines for agentic coding agents operating in this repository.

## Project Overview

This is a Flask-based MP3/MP4 video downloader application using yt-dlp. The application runs in Docker and provides a web interface for downloading audio and video from various sources.

## Project Structure

```
/workspace/descargador_mp3/
├── app/
│   ├── app.py              # Flask web application
│   ├── gestion_download.py # Download logic with yt-dlp
│   ├── templates/
│   │   └── index.html     # Web interface template
│   ├── Dockerfile         # Docker image definition
│   └── docker-compose.yml # Docker Compose configuration
├── tests/
│   ├── __init__.py
│   └── test_gestion_download.py # Unit tests
├── varios/
│   └── imagenes/          # Documentation images
├── LICENSE
├── README.md
└── AGENTS.md              # Agent coding guidelines
```

## Build, Run, and Development Commands

### Docker Commands

```bash
# Build the Docker image
docker-compose build

# Run the container
docker-compose up

# Run in detached mode
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the container
docker-compose down
```

### Local Development (without Docker)

```bash
# Install dependencies
pip install flask imageio[ffmpeg] yt_dlp

# Run the Flask application
cd app
python app.py

# The app runs on http://127.0.0.1:5000
```

### Testing

This project uses pytest for testing:

```bash
# Install test dependencies
pip install pytest

# Run all tests
pytest

# Run a single test file
pytest tests/test_gestion_download.py

# Run a single test function
pytest tests/test_gestion_download.py::TestDownloadMp3::test_download_mp3_exitoso

# Run with verbose output
pytest -v
```

### Linting

**Note:** This project currently has no linting configuration. When adding linting, use:

```bash
# Install ruff (recommended for Python)
pip install ruff

# Run ruff linter
ruff check .

# Auto-fix issues
ruff check --fix .

# Format code
ruff format .
```

## Code Style Guidelines

### General Principles

- Keep functions small and focused (under 50 lines when possible)
- Write clear, descriptive variable and function names
- Add docstrings to all public functions and classes
- Handle errors explicitly and provide meaningful error messages

### Python Version

- Target Python 3.9+ (as specified in Dockerfile)
- Use f-strings for string formatting (Python 3.6+)

### Imports

- Standard library imports first
- Third-party imports second
- Local/application imports last
- Use explicit imports (avoid `from x import *`)
- Sort imports alphabetically within each group

```python
# Correct
import os
import re
import threading
from functools import partial

import flask
import yt_dlp

from gestion_download import download_mp3, borrar_archivos
```

### Formatting

- Maximum line length: 100 characters
- Use 4 spaces for indentation (no tabs)
- Add blank lines between top-level definitions (2 lines) and method definitions (1 line)
- Use spaces around operators: `a = b + c`
- No spaces inside parentheses: `function(arg1, arg2)`

### Type Hints

- Add type hints for function parameters and return values
- Use `typing` module for complex types

```python
# Good
def download_mp3(url: str, formato: str = 'mp3') -> str | None:
    ...

# Good for complex types
from typing import Optional
def process_file(path: str) -> Optional[dict[str, Any]]:
    ...
```

### Naming Conventions

- **Variables/functions**: snake_case (`download_mp3`, `file_path`)
- **Classes**: PascalCase (`DownloadManager`, `FileHandler`)
- **Constants**: UPPER_SNAKE_CASE (`MAX_FILE_SIZE`, `DEFAULT_FORMAT`)
- **Private methods/variables**: prefix with underscore (`_internal_method`)

### Error Handling

- Use specific exception types rather than catching generic `Exception`
- Provide meaningful error messages
- Log errors appropriately (use `print` for simple cases, logging module for complex apps)
- Never expose sensitive information in error messages

```python
# Good
try:
    result = ydl.extract_info(url, download=True)
except yt_dlp.utils.DownloadError as e:
    logger.error(f"Download failed for {url}: {e}")
    return None
except yt_dlp.utils.ExtractorError as e:
    logger.error(f"Extraction failed: {e}")
    return None

# Avoid
try:
    result = ydl.extract_info(url, download=True)
except Exception as e:
    print(e)
    return None
```

### Documentation

- Use Google-style or NumPy-style docstrings
- Document all public functions with:
  - Brief description
  - Args (if applicable)
  - Returns (if applicable)
  - Raises (if applicable)

```python
def download_mp3(url: str, formato: str = 'mp3') -> str:
    """Download video/audio from URL.

    Args:
        url: The URL of the video to download.
        formato: Output format ('mp3' or 'mp4'). Defaults to 'mp3'.

    Returns:
        Path to the downloaded file.

    Raises:
        ValueError: If URL is invalid or format is not supported.
    """
```

### Flask-Specific Guidelines

- Use `request.form.get()` for form data (safer than `request.form[]`)
- Return appropriate HTTP status codes (200, 404, 500)
- Use `url_for` for generating URLs in templates
- Keep business logic out of route handlers (use separate modules)

### Docker Best Practices

- Use specific base image tags (e.g., `python:3.9-slim`, not `python:latest`)
- Use `--no-cache-dir` with pip to reduce image size
- Order Dockerfile instructions from least to most frequently changed
- Use multi-stage builds for production images

### Security Considerations

- Never commit secrets or API keys to version control
- Use environment variables for configuration
- Validate all user inputs (URLs, file paths, etc.)
- Sanitize file names before saving to prevent path traversal attacks
- Keep dependencies updated

## Common Tasks

### Adding a New Route

1. Add the route in `app.py` using the `@app.route()` decorator
2. Extract parameters using `request.args.get()` or `request.form.get()`
3. Validate inputs
4. Call business logic functions
5. Return appropriate response with status code

### Adding a New Download Format

1. Modify `gestion_download.py`
2. Add format handling in the `download_mp3` function
3. Update the HTML template if needed
4. Test the new format works

### Modifying the UI

1. Edit `app/templates/index.html`
2. Use Bootstrap or similar for quick styling
3. Test responsive behavior

## Dependencies

- **flask**: Web framework
- **yt-dlp**: Video downloading
- **imageio[ffmpeg]**: FFmpeg wrapper for media processing

## Contact

For questions or issues, refer to the README.md or open an issue on GitHub.
