import cv2
from PIL import Image


def check_image_quality(image_path):
    results = {}

    # --------------------------------------------------
    # LOAD IMAGE
    # --------------------------------------------------

    image = cv2.imread(
        str(image_path)
    )

    if image is None:
        return {
            "readable": False,
            "reason": "IMAGE_LOAD_FAILED"
        }


    height, width = image.shape[:2]

    results["readable"] = True
    results["width"] = width
    results["height"] = height


    # --------------------------------------------------
    # 1. RESOLUTION CHECK
    # --------------------------------------------------
    #
    # Previous rule:
    #
    # width < 500 OR height < 500
    #
    # was too strict.
    #
    # Example:
    # 620 × 495 is still reasonably usable
    # for OCR but was incorrectly marked LOW.
    #
    # New rule catches genuinely small images.

    if width < 450 or height < 350:

        results["resolution_check"] = "LOW"

    else:

        results["resolution_check"] = "OK"


    # --------------------------------------------------
    # 2. BLUR CHECK
    # --------------------------------------------------

    gray = cv2.cvtColor(
        image,
        cv2.COLOR_BGR2GRAY
    )


    blur_score = cv2.Laplacian(
        gray,
        cv2.CV_64F
    ).var()


    results["blur_score"] = round(
        float(blur_score),
        2
    )


    if blur_score < 80:

        results["blur_check"] = "BLURRY"

    else:

        results["blur_check"] = "OK"


    # --------------------------------------------------
    # 3. BRIGHTNESS + CONTRAST CHECK
    # --------------------------------------------------

    brightness = gray.mean()

    contrast = gray.std()


    results["brightness"] = round(
        float(brightness),
        2
    )


    results["contrast"] = round(
        float(contrast),
        2
    )


    if brightness < 50:

        results["brightness_check"] = (
            "TOO_DARK"
        )


    elif (
        brightness > 245
        and contrast < 25
    ):

        results["brightness_check"] = (
            "TOO_BRIGHT"
        )


    else:

        results["brightness_check"] = "OK"


    # --------------------------------------------------
    # 4. IMAGE METADATA CHECK
    # --------------------------------------------------
    #
    # Software metadata can be suspicious,
    # but it is NOT proof of fraud.
    #
    # Therefore this is only recorded as an
    # indicator for the decision engine.

    try:

        with Image.open(
            image_path
        ) as pil_image:

            metadata = (
                pil_image.getexif()
            )

            software = (
                metadata.get(305)
            )


            if software:

                results[
                    "editing_software"
                ] = str(
                    software
                )

                results[
                    "metadata_suspicious"
                ] = True


            else:

                results[
                    "editing_software"
                ] = None

                results[
                    "metadata_suspicious"
                ] = False


    except Exception:

        # Metadata failure should not make
        # the whole receipt verification fail.

        results[
            "editing_software"
        ] = None

        results[
            "metadata_suspicious"
        ] = False


    return results