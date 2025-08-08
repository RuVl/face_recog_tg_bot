from concurrent import futures
import io
import uuid

from PIL.ImageFile import ImageFile
import grpc
from PIL import Image
import numpy as np
from deepface import DeepFace
from deepface.modules import verification as dst
from pillow_heif import register_heif_opener

import face_pb2
import face_pb2_grpc

ImageFile.LOAD_TRUNCATED_IMAGES = True
register_heif_opener()

# Временное хранилище эмбеддингов (ID -> dict)
known_embeddings = {}

# Конфигурация по умолчанию
DEFAULT_MODEL = "Facenet512"
DEFAULT_BACKEND = "retinaface"

MODEL_MAP = {
	face_pb2.Model.MODEL_ARCFACE: "ArcFace",
	face_pb2.Model.MODEL_VGGFACE: "VGG-Face",
	face_pb2.Model.MODEL_FACENET512: "Facenet512",
}

BACKEND_MAP = {
	face_pb2.Backend.BACKEND_OPENCV: "opencv",
	face_pb2.Backend.BACKEND_DLIB: "dlib",
	face_pb2.Backend.BACKEND_RETINAFACE: "retinaface",
}

METRIC_MAP = {
	face_pb2.Metric.METRIC_COSINE: "cosine",
	face_pb2.Metric.METRIC_EUCLIDEAN: "euclidean",
	face_pb2.Metric.METRIC_EUCLIDEAN_L2: "euclidean_l2",
}


def get_distance(metric, emb1, emb2):
	if metric == "cosine":
		return dst.find_cosine_distance(emb1, emb2)
	elif metric == "euclidean":
		return dst.find_euclidean_distance(emb1, emb2)
	elif metric == "euclidean_l2":
		return dst.find_euclidean_distance(dst.l2_normalize(emb1), dst.l2_normalize(emb2))
	else:
		raise ValueError("Unknown metric")


# noinspection PyMethodMayBeStatic,PyPep8Naming
class FaceRecognizerService(face_pb2_grpc.FaceRecognizerServiceServicer):
	def GenerateEmbeddings(self, request_iterator, context):
		try:
			image_bytes = b""
			model_name = DEFAULT_MODEL
			backend = DEFAULT_BACKEND

			for msg in request_iterator:
				if msg.HasField("info"):
					model_name = MODEL_MAP.get(msg.info.model, DEFAULT_MODEL)
					backend = BACKEND_MAP.get(msg.info.backend, DEFAULT_BACKEND)
				elif msg.HasField("image_chunk"):
					image_bytes += msg.image_chunk

			image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
			np_img = np.array(image)

			embeddings = DeepFace.represent(
				img_path=np_img,
				model_name=model_name,
				detector_backend=backend,
				enforce_detection=False
			)

			results = []
			for emb in embeddings:
				if emb['face_confidence'] >= 0.75:
					results.append(face_pb2.FaceEmbedding(
						id=str(uuid.uuid4()),
						vector=emb['embedding'],
						face_confidence=emb['face_confidence']
					))

			return face_pb2.GenerateEmbeddingsResponse(faces=results)

		except Exception as e:
			context.set_details(str(e))
			context.set_code(grpc.StatusCode.INTERNAL)
			return face_pb2.EmbedResponse(faces=[])

	def AddKnownEmbedding(self, request, context):
		try:
			emb_id = request.embedding.id or str(uuid.uuid4())
			known_embeddings[emb_id] = {
				"embedding": list(request.embedding.vector),
				"confidence": request.embedding.face_confidence,
				"person_name": request.person_name
			}
			return face_pb2.AddKnownEmbeddingResponse(id=emb_id)
		except Exception as e:
			context.set_details(str(e))
			context.set_code(grpc.StatusCode.INTERNAL)
			return face_pb2.AddKnownEmbeddingResponse(id="")

	def CompareAgainstKnown(self, request, context):
		try:
			metric = METRIC_MAP.get(request.metric, "cosine")
			target = list(request.target_embedding.vector)

			results = []
			for known_id in request.known_embedding_ids:
				if known_id not in known_embeddings:
					continue
				known_vec = known_embeddings[known_id]["embedding"]
				score = get_distance(metric, known_vec, target)
				threshold = dst.find_threshold(DEFAULT_MODEL, metric)
				results.append(face_pb2.ComparisonResult(
					known_embedding_id=known_id,
					score=score,
					is_match=score < threshold
				))

			return face_pb2.CompareAgainstKnownResponse(results=results)

		except Exception as e:
			context.set_details(str(e))
			context.set_code(grpc.StatusCode.INTERNAL)
			return face_pb2.CompareAgainstKnownResponse(results=[])


def serve():
	server = grpc.server(futures.ThreadPoolExecutor(max_workers=4))
	face_pb2_grpc.add_FaceRecognizerServiceServicer_to_server(FaceRecognizerService(), server)
	server.add_insecure_port('[::]:50051')
	server.start()
	print("[gRPC] FaceRecognizerService started on port 50051")
	server.wait_for_termination()


if __name__ == "__main__":
	serve()
