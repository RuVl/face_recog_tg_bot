import logging
from pathlib import Path

from aiogram import types
from aiogram.enums import ParseMode
import grpc
import numpy as np

from core.database.methods.client import get_all_clients
from core.database.models import Client
from core.keyboards.inline import cancel_keyboard
import face_pb2
import face_pb2_grpc
from core.env import RecognizerKeys


def find_faces(image_path: Path) -> list[dict]:
	channel = grpc.insecure_channel(RecognizerKeys.URL)
	stub = face_pb2_grpc.FaceRecognizerServiceStub(channel)

	model = face_pb2.Model.MODEL_FACENET512
	backend = face_pb2.Backend.BACKEND_RETINAFACE

	def image_chunks():
		yield face_pb2.GenerateEmbeddingsRequest(
			info=face_pb2.ImageInfo(model=model, backend=backend)
		)
		with open(image_path, "rb") as f:
			while chunk := f.read(4096):
				yield face_pb2.GenerateEmbeddingsRequest(image_chunk=chunk)

	response = stub.GenerateEmbeddings(image_chunks())

	return [
		{
			"embedding": list(f.vector),
			"face_confidence": f.face_confidence,
			"id": f.id
		} for f in response.faces
	]


def compare_faces(known_faces: list[dict], face2compare: dict) -> list[bool]:
	channel = grpc.insecure_channel(RecognizerKeys.URL)
	stub = face_pb2_grpc.FaceRecognizerServiceStub(channel)

	metric = face_pb2.Metric.METRIC_COSINE

	request = face_pb2.CompareAgainstKnownRequest(
		target_embedding=face_pb2.FaceEmbedding(
			vector=face2compare["embedding"]
		),
		known_embedding_ids=[f["id"] for f in known_faces],
		metric=metric
	)
	response = stub.CompareAgainstKnown(request)
	return [r.is_match for r in response.results]


async def find_faces_with_match(image_path: Path, msg: types.Message, token_canceled) -> tuple[list[Client] | None, dict | None]:
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

	embeddings = list(filter(lambda e: e['face_confidence'] > .75, embeddings))

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
