from pathlib import Path

MEDIA_DIR = Path(__file__).parent.parent / 'media'
TEMP_DIR = MEDIA_DIR / 'temp'

SUPPORTED_IMAGE_TYPES = {
    'image/jpeg': '.jpg',
    'image/heif': '.heic'
}

MODEL = 'Facenet512'
BACKEND = 'retinaface'
DISTANCE_METRIC = 'cosine'

if not MEDIA_DIR.exists():
    MEDIA_DIR.mkdir()

if not TEMP_DIR.exists():
    TEMP_DIR.mkdir()
