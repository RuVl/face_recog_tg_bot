from pathlib import Path

MEDIA_DIR = Path(__file__).parent.parent / 'media'
TEMP_DIR = MEDIA_DIR / 'temp'

SUPPORTED_IMAGE_TYPES = {
    'image/jpeg': '.jpg',
    'image/heif': '.heic'
}

LOCATION_MODEL_NAME = 'cnn'  # hog is less accurate, but faster on CPU, cnn is a more accurate (GPU/CUDA accelerated)
ENCODING_MODEL_NAME = 'large'  # small or large (small returns only 5 points but faster)
TOLERANCE = 0.6  # tolerance for comparing faces
UP_SAMPLE_TIMES = 1

MAX_RESOLUTION = (2048, 2048)

if not MEDIA_DIR.exists():
    MEDIA_DIR.mkdir()

if not TEMP_DIR.exists():
    TEMP_DIR.mkdir()
