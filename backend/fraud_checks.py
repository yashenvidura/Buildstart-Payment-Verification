import hashlib
import imagehash
from  PIL import Image

def check_reference_reuse(receipt_reference, used_references):
    """
    Check whether a receipt reference has already
    been associated with a previous payment.
    """

    if receipt_reference is None:
        return "MISSING"

    if receipt_reference in used_references:
        return "REUSED"

    return "NEW"

def calculate_file_hash(image_path):
    """
    Calculate a SHA-256 fingerprint for an image file.
    """

    sha256 = hashlib.sha256()

    with open(image_path, "rb") as file:
        while True:
            chunk = file.read(8192)

            if not chunk:
                break

            sha256.update(chunk)

    return sha256.hexdigest()

def check_exact_duplicate(image_hash, used_image_hashes):
    """
    Check whether this exact image has already been submitted.
    """

    if image_hash in used_image_hashes:
        return "DUPLICATE"

    return "NEW"

def calculate_perceptual_hash(image_path):
    """
    Calculate a perceptual hash based on the visual appearance
    of an image.
    """

    with Image.open(image_path) as image:
        perceptual_hash = imagehash.phash(image)

    return str(perceptual_hash)


def check_similar_image(
    current_hash,
    used_perceptual_hashes,
    threshold=6
):
    """
    Compare the current perceptual hash against previously
    submitted images.

    A smaller Hamming distance means greater visual similarity.
    """

    current = imagehash.hex_to_hash(current_hash)

    closest_distance = None

    for stored_hash_text in used_perceptual_hashes:

        stored_hash = imagehash.hex_to_hash(
            stored_hash_text
        )

        distance =int( current - stored_hash)

        if (
            closest_distance is None
            or distance < closest_distance
        ):
            closest_distance = distance

    if (
        closest_distance is not None
        and closest_distance <= threshold
    ):
        return {
            "status": "SIMILAR",
            "distance": closest_distance
        }

    return {
        "status": "NEW",
        "distance": closest_distance
    }