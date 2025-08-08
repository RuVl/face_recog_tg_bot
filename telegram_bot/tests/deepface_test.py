import json
import logging
import time
from pathlib import Path

from PIL import Image, ImageDraw, ImageOps
from deepface import DeepFace
from deepface.commons import distance as dst
from tqdm import tqdm

models = [
	"VGG-Face",
	"Facenet",
	"Facenet512",
	"OpenFace",
	"DeepFace",
	"DeepID",
	"ArcFace",
	"Dlib",
	"SFace",
]

backends = [
	'opencv',
	'ssd',
	'dlib',
	'mtcnn',
	'retinaface',
	'mediapipe',
	'yolov8',
	'yunet',
	'fastmtcnn',
]

distance_metrics = [
	'cosine',
	'euclidean',
	'euclidean_l2'
]

MODEL = models[2]
BACKEND = backends[4]
DISTANCE_METRIC = distance_metrics[0]


def process_image(img_path: str | Path) -> Path | None:
	img_path = Path(img_path)
	if not img_path.exists() or not img_path.is_file():
		logging.warning("No Image provided")
		return None

	save_folder = Path('drive/MyDrive/temp')
	if not save_folder.exists():
		save_folder.mkdir()

	with Image.open(img_path) as img:
		ImageOps.exif_transpose(img, in_place=True)
		# img.thumbnail(size=(1024,1024))
		img.save(save_folder / img_path.name)

	return save_folder / img_path.name


def represent_face(img_path: str | Path) -> list | None:
	img_path = process_image(img_path)
	if img_path is None:
		return None

	try:
		embedding_objs = DeepFace.represent(
			img_path=img_path,
			model_name=MODEL,
			detector_backend=BACKEND
		)
	except:
		logging.warning(f'Face not found! {img_path.name}')
		return None

	with Image.open(img_path) as img:
		draw = ImageDraw.Draw(img)

		for embedding in embedding_objs:
			fa: dict = embedding['facial_area']
			xy = [fa['x'], fa['y'], fa['x'] + fa['w'], fa['y'] + fa['h']]
			draw.rectangle(xy, outline=(255, 0, 0), width=3)

		img.save(img_path)

	return embedding_objs


def save_all_encodings(images: list[Path], result_file: Path | str = 'result.json') -> None:
	result_file = Path(result_file)
	if not result_file.exists():
		result_file.write_text('{}')

	with open(result_file, 'r') as f:
		data: dict = json.load(f)

	try:
		for img_path in tqdm(images):
			if img_path.name in data:
				continue

			embeddings = represent_face(img_path)
			data[img_path.name] = embeddings
	except Exception as e:
		logging.exception(e)
	finally:
		with open(result_file, 'w') as f:
			json.dump(data, f, indent=4, ensure_ascii=True)


def get_distance(distance_metric, embedding1, embedding2) -> int:
	if distance_metric == "cosine":
		return dst.findCosineDistance(embedding1, embedding2)
	elif distance_metric == "euclidean":
		return dst.findEuclideanDistance(embedding1, embedding2)
	elif distance_metric == "euclidean_l2":
		return dst.findEuclideanDistance(
			dst.l2_normalize(embedding1), dst.l2_normalize(embedding2)
		)
	else:
		raise ValueError("Invalid distance_metric passed - ", distance_metric)


def check_face(img_path: Path | str,
               result_file: Path | str = 'result.json',
               model_name='VGG-Face',
               distance_metric='cosine') -> dict:
	img_path = process_image(img_path)
	if img_path is None:
		return False

	result_file = Path(result_file)
	if not result_file.exists():
		return False

	tic = time.time()

	source_people = img_path.stem
	source_faces = represent_face(img_path)
	source_embedding = source_faces[0]['embedding']  # Берём первое лицо (если их больше - плохо)

	with open(result_file, 'r') as f:
		data: dict[str, list] = json.load(f)

	threshold = dst.findThreshold(model_name, distance_metric)
	verified = {}

	toc = time.time()

	for people, faces in data.items():
		embedding = faces[0]['embedding']  # Берём первое лицо (если их больше - плохо)
		distance = get_distance(distance_metric, source_embedding, embedding)
		verified[people] = {
			"verified": True if distance <= threshold else False,
			"distance": distance,
			"threshold": threshold,
			"similarity_metric": distance_metric,
			"time": round(toc - tic, 2),
		}

	return verified


if __name__ == '__main__':
	# folder = Path(r'../temp/')
	# images = folder.glob('*.jpg')
	# save_all_encodings(images)

	check_face('')
