import logging
from pathlib import Path

from PIL import Image
from aiogram import types
from aiogram.enums import ParseMode
import numpy as np
from deepface import DeepFace
from deepface.modules import verification as dst

from core.config import BACKEND, DISTANCE_METRIC, MODEL
from core.database.methods.client import get_all_clients
from core.database.models import Client
from core.handlers.utils import TokenCancelCheck
from core.keyboards.inline import cancel_keyboard


def find_faces(image_path: Path) -> list[dict]:
	img = Image.open(image_path)
	np_img = np.array(img)
	img.close()

	embeddings = DeepFace.represent(np_img, model_name=MODEL, detector_backend=BACKEND, enforce_detection=False)
	return list(filter(lambda e: e['face_confidence'] > .75, embeddings))


def get_distance(distance_metric, embedding1, embedding2) -> int:
	if distance_metric == "cosine":
		return dst.find_cosine_distance(embedding1, embedding2)
	elif distance_metric == "euclidean":
		return dst.find_euclidean_distance(embedding1, embedding2)
	elif distance_metric == "euclidean_l2":
		return dst.find_euclidean_distance(
			dst.l2_normalize(embedding1), dst.l2_normalize(embedding2)
		)
	else:
		raise ValueError("Invalid distance_metric passed - ", distance_metric)


def compare_faces(known_faces: list[dict], face2compare: dict) -> list[bool]:
	"""
		:param known_faces: list of known face encodings
		:param face2compare: face encoding to find similar faces
	"""
	threshold = dst.find_threshold(MODEL, DISTANCE_METRIC)

	return [
		get_distance(DISTANCE_METRIC, face['embedding'], face2compare['embedding']) < threshold
		for face in known_faces
	]


async def find_faces_with_match(image_path: Path, msg: types.Message, token_canceled: TokenCancelCheck) -> tuple[list[Client] | None, dict | None]:
	try:
		embeddings = find_faces(image_path)
	except Exception as e:
		logging.error(str(e))
		await msg.edit_text('Произошла ошибка обработки фотографии\.\n'
		                    'Пожалуйста, свяжитесь с администратором\.',
		                    reply_markup=cancel_keyboard('Назад'), parse_mode=ParseMode.MARKDOWN_V2)
		return None, None

	if await token_canceled():
		return None, None

	if len(embeddings) > 1:
		await msg.edit_text(f'Обнаружено {len(embeddings)} лиц\!\n'
		                    f'На фотографии должен быть только 1 человек\.\n'
		                    f'Попробуйте отправить другую фотографию\.',
		                    reply_markup=cancel_keyboard('Назад'), parse_mode=ParseMode.MARKDOWN_V2)
		return None, None

	if len(embeddings) == 0:
		await msg.edit_text('Ни одного лица на фотографии не обнаружено\!\n'
		                    'Попробуйте отправить другую фотографию\.',
		                    reply_markup=cancel_keyboard('Назад'), parse_mode=ParseMode.MARKDOWN_V2)
		return None, None

	await msg.edit_text('📇 Обнаружено 1 лицо\!\n'
	                    'Поиск совпадений в базе данных\. 🗄',
	                    reply_markup=cancel_keyboard(), parse_mode=ParseMode.MARKDOWN_V2)

	face = embeddings[0]

	# Get known faces encoding
	clients = await get_all_clients()
	known_faces = [client.face_encoding for client in clients]

	if await token_canceled():
		return None, face

	# Compare with known faces
	try:
		results = compare_faces(known_faces, face)
	except Exception as e:
		logging.error(str(e))
		await msg.edit_text('Произошла ошибка сравнения лица в бд\.\n'
		                    'Пожалуйста, свяжитесь с администратором\.',
		                    reply_markup=cancel_keyboard('Назад'), parse_mode=ParseMode.MARKDOWN_V2)
		return None, None

	# Extract matches
	indexes = np.nonzero(results)[0]  # axe=0

	# Clients with this face aren't found.
	if len(indexes) == 0:
		return None, face  # Return only face encoding

	return [clients[i] for i in indexes], face  # Return an array of clients and face encoding
