from deepface.commons import distance as dst

from core.config import MODEL, DISTANCE_METRIC


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


def compare_faces(known_faces: list[dict], face2compare: dict):
    """
        :param known_faces: list of known face encodings
        :param face2compare: face encoding to find similar faces
    """
    threshold = dst.findThreshold(MODEL, DISTANCE_METRIC)

    result = []
    for face in known_faces:
        distance = get_distance(DISTANCE_METRIC, face['embedding'], face2compare['embedding'])
        result.append(distance < threshold)

    return result
