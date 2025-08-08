import json
import logging
import time
from pathlib import Path

import cv2
from PIL import Image, ImageOps
from deepface import DeepFace
from deepface.commons import distance as dst
from pyvis.network import Network
from tqdm import tqdm

# noinspection DuplicatedCode
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


# noinspection DuplicatedCode
def process_image(img_path: str | Path) -> Path | None:
	img_path = Path(img_path)
	if not img_path.exists() or not img_path.is_file():
		logging.warning("No Image provided")
		return None

	with Image.open(img_path) as img:
		ImageOps.exif_transpose(img, in_place=True)
		img.save(img_path)

	return img_path


# noinspection DuplicatedCode
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

	return embedding_objs


def change_range(value, min1, max1, min2, max2):
	return (value - min1) / (max1 - min1) * (max2 - min2) + min2


# noinspection DuplicatedCode
def show_graph(adjacency: dict, graph_path: Path):
	nodes = []
	edges = []

	for people, faces in adjacency.items():
		nodes.append(people)
		for face in faces:
			edges.append((people, face['people'].removesuffix('.jpg'), {
				'distance': face['distance'],
				'threshold': face['threshold']
			}))

	net = Network(filter_menu=True, cdn_resources='remote')
	for i, node in tqdm(enumerate(nodes), desc='Add nodes'):
		net.add_node(i, label=node)

	for e1, e2, info in tqdm(edges, desc='Add edges'):
		i1, i2 = nodes.index(e1), nodes.index(e2)
		if i1 == i2:
			continue

		threshold, distance = info['threshold'], info['distance']
		new_threshold = threshold * 1
		if distance > new_threshold:
			continue

		w = abs(change_range(distance, 0, new_threshold, -10, -0.01))
		net.add_edge(i1, i2, width=w, title=round(distance / new_threshold, 2))

	net.show(str(graph_path), notebook=False)  # save visualization in 'graph.html'


def main(folder: Path):
	source_img = folder / 'face.jpg'
	source_faces = represent_face(source_img)
	source_embedding = source_faces[0]['embedding']

	threshold = dst.findThreshold(MODEL, DISTANCE_METRIC)
	verified_dataset = {}

	dataset = folder / 'dataset'
	for dataset_img in tqdm(dataset.glob('*.jpg'), desc='Verifying dataset'):
		tic = time.time()

		faces = represent_face(dataset_img)
		embedding = faces[0]['embedding']

		toc = time.time()

		distance = get_distance(DISTANCE_METRIC, source_embedding, embedding)
		verified_dataset[dataset_img.stem] = {
			"verified": True if distance <= threshold else False,
			"distance": distance,
			"threshold": threshold,
			"similarity_metric": DISTANCE_METRIC,
			"time": round(toc - tic, 2),
		}

	with open(folder / 'dataset.json', 'w') as f:
		json.dump(verified_dataset, f, ensure_ascii=True, indent=4)

	show_graph(verified_dataset, folder / 'dataset.html')

	for video_path in tqdm(folder.glob('*.mov'), desc='Verifying video'):
		verified_video = {}

		vidcap = cv2.VideoCapture(video_path, cv2.CAP_ANY)
		success, image = vidcap.read()
		count = 0

		while success:
			if count % 30 == 0:
				tic = time.time()

				faces = represent_face(image)
				embedding = faces[0]['embedding']

				toc = time.time()

				distance = get_distance(DISTANCE_METRIC, source_embedding, embedding)
				verified_video[count] = {
					"verified": True if distance <= threshold else False,
					"distance": distance,
					"threshold": threshold,
					"similarity_metric": DISTANCE_METRIC,
					"time": round(toc - tic, 2),
				}

			success, image = vidcap.read()
			count += 1

		with open(folder / f'{video_path.stem}.json', 'w') as f:
			json.dump(verified_video, f, ensure_ascii=True, indent=4)

		show_graph(verified_video, folder / f'{video_path.stem}.html')


if __name__ == '__main__':
	for folder in tqdm(Path('../people').iterdir()):
		main(folder)
