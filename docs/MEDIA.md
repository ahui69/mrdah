# Video thumbnails (server-side)

- Enable with `FFMPEG_THUMBS=1` and ensure `ffmpeg` binary exists in PATH or set `FFMPEG_BIN=/usr/bin/ffmpeg`.
- On upload of `video/*`, server generates a JPEG snapshot at 1s and exposes it as `/api/files/thumb/<tenant>/<day>/<id>.jpg`.
- Fallback: client will still render video if thumbnail is missing.

# Language detection

- Optional backends:
  - **CLD3** (pycld3): auto-used when installed.
  - **fastText**: set `FASTTEXT_LID_MODEL=/path/to/lid.176.bin` to enable.
- Fallback: lightweight heuristic (PL/EN).
- Endpoint for testing: `POST /api/lang/detect` with `{text}` -> code (e.g., 'pl', 'en', 'und').
