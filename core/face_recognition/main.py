from deepface.modules import verification as dst

from core.config import MODEL, DISTANCE_METRIC


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


def compare_faces(known_faces: list[dict], face2compare: dict):
    """
        :param known_faces: list of known face encodings
        :param face2compare: face encoding to find similar faces
    """
    threshold = dst.find_threshold(MODEL, DISTANCE_METRIC)

    result = []
    for face in known_faces:
        distance = get_distance(DISTANCE_METRIC, face['embedding'], face2compare['embedding'])
        result.append(distance < threshold)

    return result
