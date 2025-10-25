# Image generation & OCR

## Generate
POST /api/image/generate
{
  "prompt": "A photo of a cyberpunk city at night, rain",
  "provider": "auto|stability|replicate|hf",
  "width": 1024,
  "height": 1024,
  "steps": 30
}

ENV:
- STABILITY_API_KEY, STABILITY_ENGINE
- REPLICATE_API_KEY, REPLICATE_IMG_MODEL, REPLICATE_IMG_VERSION
- HUGGINGFACE_API_KEY, HUGGINGFACE_IMG_MODEL

## OCR
POST /api/vision/ocr { "image_url": "http://..." }
- Uses HuggingFace TrOCR by default (HUGGINGFACE_OCR_MODEL, default microsoft/trocr-base-printed).

## UI
- Slash command: /image prompt -> generates and returns attachment.
- After image upload, UI auto-calls /api/vision/describe and /api/vision/ocr and shows both beneath the thumbnail.
