from pathlib import Path

MEDIA_DIR = Path(__file__).parent.parent / 'media'

LOCATION_MODEL_NAME = 'hog'  # hog is less accurate but faster on CPU, cnn is a more accurate (GPU/CUDA accelerated)
ENCODING_MODEL_NAME = 'small'  # small or large (small returns only 5 points but faster)
TOLERANCE = 0.6  # tolerance for comparing faces

if not MEDIA_DIR.exists():
    MEDIA_DIR.mkdir()
