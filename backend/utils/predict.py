import io
import json
import os
import time
from pathlib import Path

import numpy as np
import tensorflow as tf
from tensorflow.keras.applications.mobilenet_v2 import preprocess_input as mobilenet_v2_preprocess
from PIL import Image, ImageEnhance, ImageOps, UnidentifiedImageError

from .class_rules import apply_class_rules
from .class_rules.common import has_general_non_tomato_leaf_profile

try:
    import cv2
except ImportError:
    cv2 = None


BASE_DIR = Path(__file__).resolve().parents[1]
MODEL_PATH = BASE_DIR / "model" / "tomato_disease_model.h5"
CLASS_NAMES_PATH = BASE_DIR / "model" / "class_names.json"
IMAGE_SIZE = (224, 224)
ANALYSIS_MAX_DIMENSION = 1024
PREPROCESSING_MODE = os.getenv("MODEL_PREPROCESSING", "rescale").strip().lower()
APPLY_VISUAL_DISEASE_CALIBRATION = (
    os.getenv("APPLY_VISUAL_DISEASE_CALIBRATION", "false").strip().lower()
    in {"1", "true", "yes", "on"}
)
CONFIDENCE_WARNING_THRESHOLD = 0.65
REGION_CONFIDENCE_THRESHOLD = 0.6
DISEASE_BOOST_THRESHOLD = 0.55
TOP_VARIANT_COUNT = 3
SECONDARY_SCORE_RATIO = 0.95
SECONDARY_MIN_REGIONS = 2
SECONDARY_MIN_SCORE = 0.72
SOFT_EVIDENCE_THRESHOLD = 0.1
BALANCED_LEAF_CANDIDATE_LIMIT = 2
FAST_LEAF_CANDIDATE_LIMIT = 1
DISEASE_CLASSES = {"Early Blight", "Late Blight", "Leaf Mold"}
HEALTHY_CLASS = "Healthy Tomato Leaf"
NON_LEAF_CLASS = "Non-Tomato Leaf"
REPORTABLE_CLASSES = DISEASE_CLASSES | {HEALTHY_CLASS, NON_LEAF_CLASS}
SUPPORTED_LEAF_CLASSES = REPORTABLE_CLASSES
NON_LEAF_CONFIDENCE_THRESHOLD = 0.9
NON_LEAF_REGION_RATIO_THRESHOLD = 0.55
NON_LEAF_DISEASE_PROBABILITY_CEILING = 0.12
MIN_VISIBLE_DISEASE_SYMPTOM_RATIO = 0.012
STRONG_GLOBAL_NON_LEAF_THRESHOLD = 0.97
GLOBAL_DISEASE_SUPPORT_THRESHOLD = 0.55
MIN_PLANT_COLOR_RATIO = 0.025
MIN_GREEN_COLOR_RATIO = 0.012
MIN_PLANT_CONTOUR_RATIO = 0.018
MIN_GREEN_CONTOUR_RATIO = 0.01
MIN_TOTAL_PLANT_RATIO = 0.06
MIN_CENTER_PLANT_RATIO = 0.045
MIN_CENTER_GREEN_RATIO = 0.012
MIN_CENTER_GREEN_CONTOUR_RATIO = 0.006
MIN_CENTER_SYMPTOM_RATIO = 0.018
MAX_DIAGRAM_GREEN_RATIO = 0.025
LIGHT_BACKGROUND_RATIO = 0.42
LOW_NATURAL_GREEN_RATIO = 0.04
DIAGRAM_LINE_COUNT_THRESHOLD = 18
DIAGRAM_EDGE_DENSITY_THRESHOLD = 0.035
GRAPHIC_DOMINANT_COLOR_RATIO = 0.46
GRAPHIC_TOP_COLOR_RATIO = 0.18
ARTIFICIAL_BLUE_RATIO = 0.08
GRAPHIC_GREEN_RATIO = 0.12
LEAF_MOLD_YELLOW_RATIO_THRESHOLD = 0.055
LATE_BLIGHT_DARK_RATIO_THRESHOLD = 0.055
EARLY_BLIGHT_COMPETING_SCORE_RATIO = 0.78
EARLY_BLIGHT_LESION_RATIO_THRESHOLD = 0.008
EARLY_BLIGHT_BROWN_RATIO_THRESHOLD = 0.012
EARLY_BLIGHT_TOTAL_LESION_RATIO_THRESHOLD = 0.02
HEALTHY_DISEASE_OVERRIDE_SCORE_RATIO = 0.72
HEALTHY_DISEASE_OVERRIDE_MIN_REGIONS = 2
HEALTHY_DISEASE_OVERRIDE_MIN_CONFIDENCE = 0.75
LEAF_MOLD_CHLOROSIS_OVERRIDE_RATIO = 0.04
BROAD_SIMPLE_LEAF_AREA_RATIO = 0.22
BROAD_SIMPLE_LEAF_CENTER_GREEN_RATIO = 0.18
BROAD_SIMPLE_LEAF_SOLIDITY = 0.78
BROAD_SIMPLE_LEAF_EXTENT = 0.42
BROAD_SIMPLE_LEAF_MAX_CANDIDATES = 8
BROAD_SIMPLE_LEAF_DOMINANCE_RATIO = 0.42
PREDICTION_PROFILES = {"fast", "balanced"}

DEFAULT_CLASS_NAMES = [
    "Early Blight",
    "Healthy Tomato Leaf",
    "Late Blight",
    "Leaf Mold",
    "Non-Tomato Leaf",
]


def _load_class_names() -> list[str]:
    if CLASS_NAMES_PATH.exists():
        with CLASS_NAMES_PATH.open("r", encoding="utf-8") as file:
            class_names = json.load(file)

        if not isinstance(class_names, list) or not all(isinstance(item, str) for item in class_names):
            raise ValueError("model/class_names.json must contain a JSON list of class names.")

        return class_names

    return DEFAULT_CLASS_NAMES


CLASS_NAMES = _load_class_names()
MODEL = tf.keras.models.load_model(MODEL_PATH, compile=False)


def _model_input_name() -> str | None:
    input_names = getattr(MODEL, "input_names", None)
    if input_names:
        return input_names[0]

    model_inputs = getattr(MODEL, "inputs", None)
    if model_inputs:
        return str(model_inputs[0].name).split(":")[0]

    return None


MODEL_INPUT_NAME = _model_input_name()


def normalize_prediction_profile(profile: str | None) -> str:
    value = (profile or "balanced").strip().lower()
    return value if value in PREDICTION_PROFILES else "balanced"


def _unsupported_leaf_message() -> str:
    return "This is not a leaf image. Please upload a clear leaf photo."


def _visual_metric(visual_evidence: dict, key: str) -> float:
    value = visual_evidence.get(key)
    return float(value) if isinstance(value, (int, float)) else 0.0


def _has_possible_leaf_visual_signal(visual_evidence: dict) -> bool:
    return (
        bool(visual_evidence.get("has_enough_total_plant_signal"))
        or bool(visual_evidence.get("has_centered_leaf_signal"))
        or bool(visual_evidence.get("has_centered_symptom_signal"))
        or _visual_metric(visual_evidence, "plant_color_ratio") >= MIN_PLANT_COLOR_RATIO
        or _visual_metric(visual_evidence, "green_color_ratio") >= MIN_GREEN_COLOR_RATIO
        or _visual_metric(visual_evidence, "green_contour_area_ratio") >= (MIN_GREEN_CONTOUR_RATIO * 0.5)
        or _visual_metric(visual_evidence, "max_contour_area_ratio") >= MIN_PLANT_CONTOUR_RATIO
        or int(_visual_metric(visual_evidence, "candidate_count")) > 0
    )


def _has_photographic_leaf_signal(visual_evidence: dict) -> bool:
    """Allow real leaf photos that look graphic because of a plain background."""
    straight_line_count = int(_visual_metric(visual_evidence, "straight_line_count"))
    candidate_count = int(_visual_metric(visual_evidence, "candidate_count"))
    aspect_ratio = _visual_metric(visual_evidence, "largest_green_contour_aspect_ratio")

    has_centered_green_leaf = (
        bool(visual_evidence.get("has_centered_leaf_signal"))
        and _visual_metric(visual_evidence, "center_green_color_ratio") >= 0.025
        and (
            _visual_metric(visual_evidence, "green_contour_area_ratio") >= 0.035
            or _visual_metric(visual_evidence, "max_contour_area_ratio") >= 0.05
        )
    )
    has_leaf_shaped_contour = (
        1.15 <= aspect_ratio <= 6.0
        and (
            _visual_metric(visual_evidence, "largest_green_contour_dominance_ratio") >= 0.3
            or candidate_count <= 3
        )
    )
    lacks_diagram_line_structure = straight_line_count < DIAGRAM_LINE_COUNT_THRESHOLD

    return has_centered_green_leaf and has_leaf_shaped_contour and lacks_diagram_line_structure


def _is_hard_visual_reject(visual_evidence: dict) -> bool:
    """Reject only obvious unsupported inputs before model inference.

    Real leaf photos vary a lot in lighting, background, disease color, and framing.
    Diagram and graphic-like inputs are different: colored blocks can look green
    enough to mimic plant pixels, so reject them before model inference.
    """
    has_possible_leaf_signal = _has_possible_leaf_visual_signal(visual_evidence)
    has_photographic_leaf_signal = _has_photographic_leaf_signal(visual_evidence)

    if visual_evidence.get("is_diagram_like") or visual_evidence.get("is_graphic_like"):
        return not has_photographic_leaf_signal

    if not has_possible_leaf_signal:
        return True

    return False


def _unsupported_region_response(started_at: float, profile: str, visual_evidence: dict) -> dict:
    return {
        "summary": {
            "diseases_found": [],
            "primary_disease": None,
            "secondary_diseases": [],
            "competing_diseases": [],
            "disease_summary": [],
            "soft_disease_evidence": [],
            "is_supported_leaf_image": False,
            "guardrail_reason": _unsupported_leaf_message(),
            "visual_leaf_evidence": visual_evidence,
            "confident_region_count": 0,
            "unique_region_count": 0,
            "region_count": 0,
            "confidence_threshold": REGION_CONFIDENCE_THRESHOLD,
            "prediction_profile": profile,
            "processing_time_ms": round((time.perf_counter() - started_at) * 1000, 2),
            "is_uncertain": True,
        },
        "regions": [],
    }


def _load_image(image_bytes: bytes) -> Image.Image:
    try:
        image = Image.open(io.BytesIO(image_bytes))
        return ImageOps.exif_transpose(image).convert("RGB")
    except UnidentifiedImageError as error:
        raise ValueError("Uploaded file is not a valid image.") from error


def _resize_for_analysis(image: Image.Image) -> Image.Image:
    largest_side = max(image.size)
    if largest_side <= ANALYSIS_MAX_DIMENSION:
        return image

    scale = ANALYSIS_MAX_DIMENSION / largest_side
    next_size = (
        max(int(image.width * scale), 1),
        max(int(image.height * scale), 1),
    )
    return image.resize(next_size, Image.Resampling.BILINEAR)


def _analyze_leaf_visual_evidence(image: Image.Image) -> dict:
    rgb = np.asarray(image)

    if cv2 is None:
        return {
            "plant_color_ratio": None,
            "green_color_ratio": None,
            "green_contour_area_ratio": None,
            "center_plant_color_ratio": None,
            "center_green_color_ratio": None,
            "center_green_contour_area_ratio": None,
            "top_green_color_ratio": None,
            "max_contour_area_ratio": None,
            "candidate_count": None,
            "light_background_ratio": None,
            "edge_density": None,
            "straight_line_count": None,
            "is_diagram_like": False,
            "is_graphic_like": False,
            "dominant_color_ratio": None,
            "top_color_ratio": None,
            "artificial_blue_ratio": None,
            "yellow_symptom_ratio": None,
            "brown_symptom_ratio": None,
            "dark_symptom_ratio": None,
            "has_centered_symptom_signal": None,
            "largest_green_contour_solidity": None,
            "largest_green_contour_extent": None,
            "largest_green_contour_aspect_ratio": None,
            "largest_green_contour_dominance_ratio": None,
            "is_broad_simple_leaf_like": False,
            "has_leaf_like_color": True,
        }

    height, width = rgb.shape[:2]
    image_area = max(width * height, 1)
    center_left = int(width * 0.15)
    center_right = int(width * 0.85)
    center_top = int(height * 0.15)
    center_bottom = int(height * 0.85)
    center_area = max((center_right - center_left) * (center_bottom - center_top), 1)
    top_bottom = max(int(height * 0.35), 1)
    top_area = max(width * top_bottom, 1)
    hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)
    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)

    green_mask = cv2.inRange(hsv, np.array([25, 35, 30]), np.array([95, 255, 255]))
    natural_green_mask = cv2.inRange(hsv, np.array([35, 45, 25]), np.array([95, 255, 245]))
    yellow_brown_mask = cv2.inRange(hsv, np.array([5, 35, 25]), np.array([35, 255, 235]))
    yellow_symptom_mask = cv2.inRange(hsv, np.array([18, 45, 80]), np.array([42, 255, 255]))
    brown_symptom_mask = cv2.inRange(hsv, np.array([3, 35, 25]), np.array([25, 255, 170]))
    dark_symptom_mask = cv2.inRange(hsv, np.array([0, 20, 0]), np.array([180, 255, 95]))
    plant_mask = cv2.bitwise_or(green_mask, yellow_brown_mask)

    kernel = np.ones((7, 7), np.uint8)
    plant_mask = cv2.morphologyEx(plant_mask, cv2.MORPH_OPEN, kernel)
    plant_mask = cv2.morphologyEx(plant_mask, cv2.MORPH_CLOSE, kernel)
    natural_green_mask = cv2.morphologyEx(natural_green_mask, cv2.MORPH_OPEN, kernel)
    natural_green_mask = cv2.morphologyEx(natural_green_mask, cv2.MORPH_CLOSE, kernel)
    leaf_context_mask = cv2.dilate(
        cv2.bitwise_or(plant_mask, natural_green_mask),
        kernel,
        iterations=1,
    )
    non_green_leaf_context_mask = cv2.bitwise_and(
        leaf_context_mask,
        cv2.bitwise_not(natural_green_mask),
    )
    yellow_symptom_mask = cv2.bitwise_and(yellow_symptom_mask, leaf_context_mask)
    brown_symptom_mask = cv2.bitwise_and(brown_symptom_mask, leaf_context_mask)
    dark_symptom_mask = cv2.bitwise_and(dark_symptom_mask, non_green_leaf_context_mask)

    contours, _ = cv2.findContours(plant_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    green_contours, _ = cv2.findContours(natural_green_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contour_area_ratios = [
        cv2.contourArea(contour) / image_area
        for contour in contours
    ]
    green_contour_area_ratios = [
        cv2.contourArea(contour) / image_area
        for contour in green_contours
    ]
    max_contour_area_ratio = max(contour_area_ratios, default=0.0)
    max_green_contour_area_ratio = max(green_contour_area_ratios, default=0.0)
    largest_green_contour_solidity = 0.0
    largest_green_contour_extent = 0.0
    largest_green_contour_aspect_ratio = 0.0
    largest_green_contour_dominance_ratio = 0.0

    if green_contours:
        largest_green_contour = max(green_contours, key=cv2.contourArea)
        largest_green_area = cv2.contourArea(largest_green_contour)
        x, y, w, h = cv2.boundingRect(largest_green_contour)
        hull = cv2.convexHull(largest_green_contour)
        hull_area = cv2.contourArea(hull)
        largest_green_contour_solidity = float(largest_green_area / max(hull_area, 1.0))
        largest_green_contour_extent = float(largest_green_area / max(w * h, 1))
        largest_green_contour_aspect_ratio = float(max(w, h) / max(min(w, h), 1))
        largest_green_contour_dominance_ratio = float(
            largest_green_area / max(sum(cv2.contourArea(contour) for contour in green_contours), 1.0)
        )

    center_green_contour_area_ratio = 0.0
    for contour in green_contours:
        x, y, w, h = cv2.boundingRect(contour)
        contour_center_x = x + (w / 2)
        contour_center_y = y + (h / 2)
        intersects_center = (
            x < center_right
            and x + w > center_left
            and y < center_bottom
            and y + h > center_top
        )
        center_is_inside = (
            center_left <= contour_center_x <= center_right
            and center_top <= contour_center_y <= center_bottom
        )
        if intersects_center or center_is_inside:
            center_green_contour_area_ratio = max(
                center_green_contour_area_ratio,
                cv2.contourArea(contour) / image_area,
            )

    candidate_count = sum(
        area_ratio >= MIN_PLANT_CONTOUR_RATIO
        for area_ratio in contour_area_ratios
    )
    plant_color_ratio = float(np.count_nonzero(plant_mask) / image_area)
    green_color_ratio = float(np.count_nonzero(natural_green_mask) / image_area)
    center_plant_color_ratio = float(
        np.count_nonzero(plant_mask[center_top:center_bottom, center_left:center_right]) / center_area
    )
    center_green_color_ratio = float(
        np.count_nonzero(natural_green_mask[center_top:center_bottom, center_left:center_right]) / center_area
    )
    top_green_color_ratio = float(np.count_nonzero(natural_green_mask[:top_bottom, :]) / top_area)
    light_background_ratio = float(np.count_nonzero(gray >= 235) / image_area)
    artificial_blue_mask = cv2.inRange(hsv, np.array([95, 35, 30]), np.array([135, 255, 255]))
    artificial_blue_ratio = float(np.count_nonzero(artificial_blue_mask) / image_area)
    center_yellow_symptom_ratio = float(
        np.count_nonzero(yellow_symptom_mask[center_top:center_bottom, center_left:center_right]) / center_area
    )
    center_brown_symptom_ratio = float(
        np.count_nonzero(brown_symptom_mask[center_top:center_bottom, center_left:center_right]) / center_area
    )
    center_dark_symptom_ratio = float(
        np.count_nonzero(dark_symptom_mask[center_top:center_bottom, center_left:center_right]) / center_area
    )

    sample_rgb = cv2.resize(rgb, (128, 128), interpolation=cv2.INTER_AREA)
    quantized = (sample_rgb // 32).reshape(-1, 3)
    _, color_counts = np.unique(quantized, axis=0, return_counts=True)
    sorted_color_counts = np.sort(color_counts)[::-1]
    sample_pixel_count = max(len(quantized), 1)
    dominant_color_ratio = float(sorted_color_counts[:5].sum() / sample_pixel_count)
    top_color_ratio = float(sorted_color_counts[0] / sample_pixel_count)

    edges = cv2.Canny(gray, 80, 180)
    edge_density = float(np.count_nonzero(edges) / image_area)
    min_line_length = max(min(width, height) // 8, 40)
    lines = cv2.HoughLinesP(
        edges,
        rho=1,
        theta=np.pi / 180,
        threshold=80,
        minLineLength=min_line_length,
        maxLineGap=8,
    )
    straight_line_count = 0
    if lines is not None:
        for line in lines[:, 0]:
            x1, y1, x2, y2 = line
            dx = abs(x2 - x1)
            dy = abs(y2 - y1)
            if dx >= min_line_length or dy >= min_line_length:
                if dx <= max(dy * 0.18, 4) or dy <= max(dx * 0.18, 4):
                    straight_line_count += 1

    is_diagram_like = (
        green_color_ratio < MAX_DIAGRAM_GREEN_RATIO
        and (
            straight_line_count >= DIAGRAM_LINE_COUNT_THRESHOLD
            or (
                light_background_ratio >= LIGHT_BACKGROUND_RATIO
                and edge_density >= DIAGRAM_EDGE_DENSITY_THRESHOLD
            )
        )
    )
    is_graphic_like = (
        dominant_color_ratio >= GRAPHIC_DOMINANT_COLOR_RATIO
        and top_color_ratio >= GRAPHIC_TOP_COLOR_RATIO
        and (
            artificial_blue_ratio >= ARTIFICIAL_BLUE_RATIO
            or (
                light_background_ratio >= 0.18
                and green_color_ratio >= GRAPHIC_GREEN_RATIO
                and edge_density >= 0.025
            )
        )
    )
    has_enough_total_plant_signal = (
        plant_color_ratio >= MIN_TOTAL_PLANT_RATIO
        or green_color_ratio >= LOW_NATURAL_GREEN_RATIO
        or max_green_contour_area_ratio >= MIN_GREEN_CONTOUR_RATIO
    )
    has_centered_symptom_signal = (
        (center_yellow_symptom_ratio + center_brown_symptom_ratio + center_dark_symptom_ratio) >= MIN_CENTER_SYMPTOM_RATIO
        and (
            center_plant_color_ratio >= MIN_CENTER_PLANT_RATIO
            or center_green_contour_area_ratio >= (MIN_CENTER_GREEN_CONTOUR_RATIO * 0.5)
        )
    )
    has_centered_leaf_signal = (
        center_green_color_ratio >= MIN_CENTER_GREEN_RATIO
        or center_green_contour_area_ratio >= MIN_CENTER_GREEN_CONTOUR_RATIO
        or has_centered_symptom_signal
        or (
            center_plant_color_ratio >= MIN_CENTER_PLANT_RATIO
            and green_color_ratio >= MIN_GREEN_COLOR_RATIO
        )
    )
    is_background_vegetation_only = (
        not has_centered_leaf_signal
        and top_green_color_ratio > max(center_green_color_ratio * 2.5, MIN_GREEN_COLOR_RATIO)
    )
    is_broad_simple_leaf_like = (
        max_green_contour_area_ratio >= BROAD_SIMPLE_LEAF_AREA_RATIO
        and center_green_color_ratio >= BROAD_SIMPLE_LEAF_CENTER_GREEN_RATIO
        and largest_green_contour_solidity >= BROAD_SIMPLE_LEAF_SOLIDITY
        and largest_green_contour_extent >= BROAD_SIMPLE_LEAF_EXTENT
        and (
            candidate_count <= BROAD_SIMPLE_LEAF_MAX_CANDIDATES
            or largest_green_contour_dominance_ratio >= BROAD_SIMPLE_LEAF_DOMINANCE_RATIO
        )
    )
    is_multi_leaf_scene = (
        candidate_count >= 4
        or (
            green_color_ratio >= 0.18
            and largest_green_contour_dominance_ratio < 0.65
        )
        or (
            plant_color_ratio >= 0.28
            and largest_green_contour_dominance_ratio < 0.72
        )
    )
    has_leaf_like_color = (
        not is_diagram_like
        and not is_graphic_like
        and not is_background_vegetation_only
        and not is_broad_simple_leaf_like
        and has_enough_total_plant_signal
        and has_centered_leaf_signal
    )

    return {
        "plant_color_ratio": plant_color_ratio,
        "green_color_ratio": green_color_ratio,
        "green_contour_area_ratio": float(max_green_contour_area_ratio),
        "center_plant_color_ratio": center_plant_color_ratio,
        "center_green_color_ratio": center_green_color_ratio,
        "center_green_contour_area_ratio": float(center_green_contour_area_ratio),
        "top_green_color_ratio": top_green_color_ratio,
        "max_contour_area_ratio": float(max_contour_area_ratio),
        "candidate_count": int(candidate_count),
        "light_background_ratio": light_background_ratio,
        "edge_density": edge_density,
        "straight_line_count": int(straight_line_count),
        "is_diagram_like": bool(is_diagram_like),
        "is_graphic_like": bool(is_graphic_like),
        "dominant_color_ratio": dominant_color_ratio,
        "top_color_ratio": top_color_ratio,
        "artificial_blue_ratio": artificial_blue_ratio,
        "yellow_symptom_ratio": center_yellow_symptom_ratio,
        "brown_symptom_ratio": center_brown_symptom_ratio,
        "dark_symptom_ratio": center_dark_symptom_ratio,
        "largest_green_contour_solidity": largest_green_contour_solidity,
        "largest_green_contour_extent": largest_green_contour_extent,
        "largest_green_contour_aspect_ratio": largest_green_contour_aspect_ratio,
        "largest_green_contour_dominance_ratio": largest_green_contour_dominance_ratio,
        "is_broad_simple_leaf_like": bool(is_broad_simple_leaf_like),
        "is_multi_leaf_scene": bool(is_multi_leaf_scene),
        "is_background_vegetation_only": bool(is_background_vegetation_only),
        "has_enough_total_plant_signal": bool(has_enough_total_plant_signal),
        "has_centered_symptom_signal": bool(has_centered_symptom_signal),
        "has_centered_leaf_signal": bool(has_centered_leaf_signal),
        "has_leaf_like_color": bool(has_leaf_like_color),
    }


def _center_crop(image: Image.Image, crop_ratio: float) -> Image.Image:
    width, height = image.size
    crop_width = int(width * crop_ratio)
    crop_height = int(height * crop_ratio)
    left = max((width - crop_width) // 2, 0)
    top = max((height - crop_height) // 2, 0)
    return image.crop((left, top, left + crop_width, top + crop_height))


def _corner_crop(image: Image.Image, crop_ratio: float, horizontal: str, vertical: str) -> Image.Image:
    width, height = image.size
    crop_width = int(width * crop_ratio)
    crop_height = int(height * crop_ratio)

    left = 0 if horizontal == "left" else width - crop_width
    top = 0 if vertical == "top" else height - crop_height
    return image.crop((left, top, left + crop_width, top + crop_height))


def _resize(image: Image.Image) -> Image.Image:
    return image.resize(IMAGE_SIZE, Image.Resampling.LANCZOS)


def _build_image_variants(image: Image.Image, profile: str = "balanced") -> list[Image.Image]:
    variants = [
        ImageOps.pad(image, IMAGE_SIZE, method=Image.Resampling.LANCZOS, color=(0, 0, 0)),
        _resize(ImageOps.fit(image, IMAGE_SIZE, method=Image.Resampling.LANCZOS, centering=(0.5, 0.5))),
        _resize(_center_crop(image, 0.9)),
    ]

    if profile == "fast":
        enhanced = ImageEnhance.Contrast(image).enhance(1.15)
        variants.append(_resize(ImageOps.fit(enhanced, IMAGE_SIZE, method=Image.Resampling.LANCZOS)))
        return variants

    variants.append(_resize(_center_crop(image, 0.75)))

    if min(image.size) >= 180:
        variants.extend(
            [
                _resize(_corner_crop(image, 0.82, "left", "top")),
                _resize(_corner_crop(image, 0.82, "right", "top")),
                _resize(_corner_crop(image, 0.82, "left", "bottom")),
                _resize(_corner_crop(image, 0.82, "right", "bottom")),
            ]
        )

    enhanced = ImageEnhance.Contrast(image).enhance(1.2)
    enhanced = ImageEnhance.Sharpness(enhanced).enhance(1.15)
    variants.append(_resize(ImageOps.fit(enhanced, IMAGE_SIZE, method=Image.Resampling.LANCZOS)))

    mirrored = ImageOps.mirror(image)
    variants.append(_resize(ImageOps.fit(mirrored, IMAGE_SIZE, method=Image.Resampling.LANCZOS)))

    return variants


def _to_model_batch(images: list[Image.Image]) -> np.ndarray:
    batch = np.asarray(
        [np.asarray(image, dtype=np.float32) for image in images],
        dtype=np.float32,
    )

    if PREPROCESSING_MODE in {"mobilenet_v2", "mobilenet"}:
        return mobilenet_v2_preprocess(batch)

    if PREPROCESSING_MODE in {"rescale", "rescale_1_255", "0_1"}:
        return batch / 255.0

    if PREPROCESSING_MODE in {"none", "raw"}:
        return batch

    raise ValueError(
        "Unsupported MODEL_PREPROCESSING value. "
        "Use 'mobilenet_v2', 'rescale', or 'none'."
    )


def _predict_batch(images: list[Image.Image]) -> np.ndarray:
    if not images:
        return np.empty((0, len(CLASS_NAMES)), dtype=np.float32)

    batch = _to_model_batch(images)
    model_input = {MODEL_INPUT_NAME: batch} if MODEL_INPUT_NAME else batch
    return MODEL(model_input, training=False).numpy()


def _probabilities_to_result(predictions: np.ndarray) -> dict:
    class_id = int(np.argmax(predictions))
    confidence = float(predictions[class_id])

    if class_id >= len(CLASS_NAMES):
        raise ValueError("Model returned an unknown class index.")

    top_predictions = sorted(
        (
            {"class": CLASS_NAMES[index], "confidence": float(probability)}
            for index, probability in enumerate(predictions[: len(CLASS_NAMES)])
        ),
        key=lambda item: item["confidence"],
        reverse=True,
    )

    return {
        "class_index": class_id,
        "class": CLASS_NAMES[class_id],
        "confidence": confidence,
        "is_uncertain": confidence < CONFIDENCE_WARNING_THRESHOLD,
        "top_predictions": top_predictions,
        "probabilities": {
            CLASS_NAMES[index]: float(probability)
            for index, probability in enumerate(predictions[: len(CLASS_NAMES)])
        },
    }


def _combine_variant_predictions(variant_predictions: np.ndarray) -> tuple[np.ndarray, dict]:
    mean_predictions = np.mean(variant_predictions, axis=0)
    max_predictions = np.max(variant_predictions, axis=0)
    combined_predictions = mean_predictions.copy()
    evidence = {}

    for index, class_name in enumerate(CLASS_NAMES):
        class_scores = variant_predictions[:, index]
        top_scores = np.sort(class_scores)[-TOP_VARIANT_COUNT:]
        top_mean = float(np.mean(top_scores))
        support_count = int(np.sum(class_scores >= DISEASE_BOOST_THRESHOLD))

        evidence[class_name] = {
            "mean": float(mean_predictions[index]),
            "max": float(max_predictions[index]),
            "top_mean": top_mean,
            "support_count": support_count,
        }

        if class_name in DISEASE_CLASSES and support_count >= 2:
            combined_predictions[index] = (mean_predictions[index] * 0.45) + (top_mean * 0.55)

    combined_predictions = combined_predictions / np.sum(combined_predictions)
    return combined_predictions, evidence


def _predict_image_object(image: Image.Image, profile: str = "balanced") -> tuple[dict, int]:
    variants = [_resize(image)]
    variant_predictions = _predict_batch(variants)
    predictions, variant_evidence = _combine_variant_predictions(variant_predictions)
    result = _probabilities_to_result(predictions)

    return {
        **result,
        "variant_count": len(variants),
        "variant_evidence": variant_evidence,
    }, len(variants)


def _crop_region(image: Image.Image, name: str, box: tuple[int, int, int, int]) -> dict:
    width, height = image.size
    left, top, right, bottom = box

    return {
        "name": name,
        "box": box,
        "bbox": {
            "left": left,
            "top": top,
            "right": right,
            "bottom": bottom,
        },
        "bbox_ratio": {
            "left": left / width,
            "top": top / height,
            "right": right / width,
            "bottom": bottom / height,
        },
        "image": image.crop(box),
    }


def _expand_box(
    box: tuple[int, int, int, int],
    image_size: tuple[int, int],
    padding_ratio: float = 0.18,
) -> tuple[int, int, int, int]:
    width, height = image_size
    left, top, right, bottom = box
    box_width = right - left
    box_height = bottom - top
    pad_x = int(box_width * padding_ratio)
    pad_y = int(box_height * padding_ratio)

    return (
        max(left - pad_x, 0),
        max(top - pad_y, 0),
        min(right + pad_x, width),
        min(bottom + pad_y, height),
    )


def _build_leaf_candidate_crops(image: Image.Image, max_candidates: int = 6) -> list[dict]:
    if cv2 is None:
        return []

    rgb = np.asarray(image)
    height, width = rgb.shape[:2]
    hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)

    green_mask = cv2.inRange(hsv, np.array([25, 25, 30]), np.array([95, 255, 255]))
    yellow_brown_mask = cv2.inRange(hsv, np.array([5, 30, 25]), np.array([35, 255, 235]))
    mask = cv2.bitwise_or(green_mask, yellow_brown_mask)

    kernel = np.ones((7, 7), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    candidates = []
    image_area = width * height

    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        area = w * h

        if area < image_area * 0.025 or area > image_area * 0.85:
            continue

        aspect_ratio = w / max(h, 1)
        if aspect_ratio < 0.18 or aspect_ratio > 7.0:
            continue

        box = _expand_box((x, y, x + w, y + h), (width, height))
        candidates.append((area, box))

    candidates.sort(key=lambda item: item[0], reverse=True)

    regions = []
    seen_boxes = set()
    for index, (_, box) in enumerate(candidates[:max_candidates], start=1):
        if box in seen_boxes:
            continue
        seen_boxes.add(box)
        regions.append(_crop_region(image, f"leaf-candidate-{index}", box))

    return regions


def _build_region_crops(image: Image.Image, profile: str = "balanced") -> list[dict]:
    width, height = image.size
    return [
        _crop_region(image, "full", (0, 0, width, height)),
    ]


def _build_fast_leaf_variants(image: Image.Image) -> list[Image.Image]:
    return [
        ImageOps.pad(image, IMAGE_SIZE, method=Image.Resampling.LANCZOS, color=(0, 0, 0)),
        _resize(ImageOps.fit(image, IMAGE_SIZE, method=Image.Resampling.LANCZOS, centering=(0.5, 0.5))),
    ]


def _dedupe_region_results(region_results: list[dict]) -> list[dict]:
    best_by_box = {}

    for result in region_results:
        box_key = (
            result["bbox"]["left"],
            result["bbox"]["top"],
            result["bbox"]["right"],
            result["bbox"]["bottom"],
        )
        existing = best_by_box.get(box_key)

        if existing is None or result["confidence"] > existing["confidence"]:
            best_by_box[box_key] = result

    return list(best_by_box.values())


def _summary_item_for_class(disease_summary: list[dict], disease_class: str) -> dict | None:
    return next((item for item in disease_summary if item["class"] == disease_class), None)


def _has_decisive_non_leaf_summary_conflict(primary: dict | None, non_leaf: dict | None) -> bool:
    if not primary or not non_leaf or primary.get("class") == NON_LEAF_CLASS:
        return False

    primary_regions = int(primary.get("region_count", 0))
    non_leaf_regions = int(non_leaf.get("region_count", 0))
    primary_score = float(primary.get("score", 0.0))
    non_leaf_score = float(non_leaf.get("score", 0.0))
    non_leaf_best_confidence = float(non_leaf.get("best_confidence", 0.0))
    non_leaf_average_confidence = float(non_leaf.get("average_confidence", 0.0))

    has_region_tie_or_better = non_leaf_regions >= max(primary_regions, 1)
    has_near_tie_score = non_leaf_score >= primary_score * 0.75
    has_extreme_non_leaf_confidence = (
        non_leaf_best_confidence >= 0.995
        and non_leaf_average_confidence >= 0.95
    )

    return (
        primary.get("class") in DISEASE_CLASSES
        and non_leaf_best_confidence >= NON_LEAF_CONFIDENCE_THRESHOLD
        and has_region_tie_or_better
        and (has_near_tie_score or has_extreme_non_leaf_confidence)
    )


def _replace_primary_disease(summary: dict, new_class: str, reason: str, evidence: dict) -> dict:
    disease_summary = list(summary.get("disease_summary", []))
    old_primary = summary.get("primary_disease")
    old_class = old_primary.get("class") if old_primary else None
    replacement = _summary_item_for_class(disease_summary, new_class)

    if replacement is None:
        replacement = {
            "class": new_class,
            "score": float((old_primary or {}).get("score", 0.0)),
            "region_count": int((old_primary or {}).get("region_count", 0)),
            "best_confidence": float((old_primary or {}).get("best_confidence", 0.0)),
            "average_confidence": float((old_primary or {}).get("average_confidence", 0.0)),
            "full_image_confidence": 0.0,
        }
        disease_summary.append(replacement)

    replacement = dict(replacement)
    replacement["calibrated_from"] = old_class
    replacement["calibration_reason"] = reason

    disease_summary = [
        item for item in disease_summary if item["class"] != new_class
    ]
    disease_summary.insert(0, replacement)

    secondary_diseases = [
        item for item in summary.get("secondary_diseases", [])
        if item.get("class") != new_class
    ]
    if old_primary and old_class and old_class != new_class:
        secondary_diseases = [
            item for item in secondary_diseases
            if item.get("class") != old_class
        ]
        secondary_diseases.insert(0, {
            **old_primary,
            "calibrated_to_secondary": True,
        })

    diseases_found = [new_class]
    diseases_found.extend(
        item["class"]
        for item in secondary_diseases
        if item.get("class") and item["class"] != new_class
    )

    return {
        **summary,
        "diseases_found": diseases_found,
        "primary_disease": replacement,
        "secondary_diseases": secondary_diseases,
        "disease_summary": disease_summary,
        "calibration": {
            "applied": True,
            "from": old_class,
            "to": new_class,
            "reason": reason,
            "evidence": evidence,
        },
    }


def _apply_late_leaf_mold_calibration(summary: dict, visual_evidence: dict) -> dict:
    primary = summary.get("primary_disease")
    if not primary:
        return {
            **summary,
            "calibration": {"applied": False},
        }

    yellow_ratio = float(visual_evidence.get("yellow_symptom_ratio") or 0.0)
    brown_ratio = float(visual_evidence.get("brown_symptom_ratio") or 0.0)
    dark_ratio = float(visual_evidence.get("dark_symptom_ratio") or 0.0)
    dark_brown_ratio = max(dark_ratio, brown_ratio)
    evidence = {
        "yellow_symptom_ratio": yellow_ratio,
        "brown_symptom_ratio": brown_ratio,
        "dark_symptom_ratio": dark_ratio,
    }

    if primary.get("class") == HEALTHY_CLASS:
        disease_candidates = [
            item for item in summary.get("disease_summary", [])
            if item.get("class") in DISEASE_CLASSES
        ]
        best_disease = max(
            disease_candidates,
            key=lambda item: item.get("score", 0.0),
            default=None,
        )
        if best_disease:
            healthy_score = float(primary.get("score", 0.0))
            disease_score = float(best_disease.get("score", 0.0))
            disease_regions = int(best_disease.get("region_count", 0))
            disease_confidence = float(best_disease.get("best_confidence", 0.0))
            has_chlorosis = yellow_ratio >= LEAF_MOLD_CHLOROSIS_OVERRIDE_RATIO
            has_symptoms = (yellow_ratio + brown_ratio + dark_ratio) >= MIN_VISIBLE_DISEASE_SYMPTOM_RATIO
            has_strong_disease_signal = (
                disease_regions >= HEALTHY_DISEASE_OVERRIDE_MIN_REGIONS
                and disease_confidence >= HEALTHY_DISEASE_OVERRIDE_MIN_CONFIDENCE
                and disease_score >= healthy_score * HEALTHY_DISEASE_OVERRIDE_SCORE_RATIO
            )

            if has_chlorosis and best_disease.get("class") in {"Leaf Mold", "Late Blight"}:
                return _replace_primary_disease(
                    summary,
                    "Leaf Mold",
                    "visible_yellow_chlorosis_overrides_healthy",
                    {
                        **evidence,
                        "healthy_score": healthy_score,
                        "best_disease_score": disease_score,
                        "best_disease_class": best_disease.get("class"),
                    },
                )

            if has_symptoms and has_strong_disease_signal:
                return _replace_primary_disease(
                    summary,
                    best_disease["class"],
                    "visible_symptoms_and_disease_signal_override_healthy",
                    {
                        **evidence,
                        "healthy_score": healthy_score,
                        "best_disease_score": disease_score,
                        "best_disease_class": best_disease.get("class"),
                    },
                )

        return {
            **summary,
            "calibration": {
                "applied": False,
                "evidence": evidence,
            },
        }

    if primary.get("class") not in {"Late Blight", "Leaf Mold"}:
        return {
            **summary,
            "calibration": {
                "applied": False,
                "evidence": evidence,
            },
        }

    leaf_mold_visual = (
        yellow_ratio >= LEAF_MOLD_YELLOW_RATIO_THRESHOLD
        and yellow_ratio >= dark_brown_ratio * 1.15
    )
    late_blight_visual = (
        dark_brown_ratio >= LATE_BLIGHT_DARK_RATIO_THRESHOLD
        and dark_brown_ratio >= yellow_ratio * 1.15
    )

    if primary["class"] == "Late Blight" and leaf_mold_visual:
        return _replace_primary_disease(
            summary,
            "Leaf Mold",
            "yellow_chlorotic_symptoms_favor_leaf_mold",
            evidence,
        )

    if primary["class"] == "Leaf Mold" and late_blight_visual:
        return _replace_primary_disease(
            summary,
            "Late Blight",
            "dark_water_soaked_symptoms_favor_late_blight",
            evidence,
        )

    return {
        **summary,
        "calibration": {
            "applied": False,
            "evidence": evidence,
        },
    }


def _apply_healthy_symptom_safeguard(summary: dict, visual_evidence: dict) -> dict:
    primary = summary.get("primary_disease")
    if not primary or primary.get("class") != HEALTHY_CLASS:
        return summary

    yellow_ratio = float(visual_evidence.get("yellow_symptom_ratio") or 0.0)
    brown_ratio = float(visual_evidence.get("brown_symptom_ratio") or 0.0)
    dark_ratio = float(visual_evidence.get("dark_symptom_ratio") or 0.0)
    visible_symptom_ratio = yellow_ratio + brown_ratio + dark_ratio
    evidence = {
        "yellow_symptom_ratio": yellow_ratio,
        "brown_symptom_ratio": brown_ratio,
        "dark_symptom_ratio": dark_ratio,
        "visible_symptom_ratio": visible_symptom_ratio,
    }

    has_clear_symptoms = (
        visible_symptom_ratio >= max(MIN_VISIBLE_DISEASE_SYMPTOM_RATIO * 2.5, 0.035)
        and (
            yellow_ratio >= 0.025
            or brown_ratio >= 0.012
            or dark_ratio >= 0.012
        )
    )
    if not has_clear_symptoms:
        return summary

    disease_candidates = [
        item for item in summary.get("disease_summary", [])
        if item.get("class") in DISEASE_CLASSES
    ]
    best_disease = max(
        disease_candidates,
        key=lambda item: item.get("score", 0.0),
        default=None,
    )

    has_supported_disease_alternative = (
        best_disease is not None
        and int(best_disease.get("region_count", 0)) >= HEALTHY_DISEASE_OVERRIDE_MIN_REGIONS
        and float(best_disease.get("best_confidence", 0.0)) >= HEALTHY_DISEASE_OVERRIDE_MIN_CONFIDENCE
    )

    if not has_supported_disease_alternative:
        return {
            **summary,
            "diseases_found": [],
            "primary_disease": None,
            "secondary_diseases": [],
            "competing_diseases": summary.get("disease_summary", []),
            "is_uncertain": True,
            "symptom_safeguard": {
                "applied": True,
                "reason": "visible_symptoms_conflict_with_healthy_result",
                "evidence": {
                    **evidence,
                    "previous_healthy_score": float(primary.get("score", 0.0)),
                    "best_model_disease_class": best_disease.get("class") if best_disease else None,
                    "best_model_disease_confidence": (
                        float(best_disease.get("best_confidence", 0.0))
                        if best_disease
                        else 0.0
                    ),
                },
            },
        }

    guarded = _replace_primary_disease(
        summary,
        best_disease["class"],
        "visible_symptoms_prevent_healthy_result",
        {
            **evidence,
            "previous_healthy_score": float(primary.get("score", 0.0)),
            "best_model_disease_class": best_disease.get("class") if best_disease else None,
            "best_model_disease_confidence": (
                float(best_disease.get("best_confidence", 0.0))
                if best_disease
                else 0.0
            ),
        },
    )
    if guarded.get("primary_disease"):
        guarded["primary_disease"] = {
            **guarded["primary_disease"],
            "symptom_safeguard": True,
        }
    return guarded


def _apply_low_symptom_disease_safeguard(summary: dict, visual_evidence: dict) -> dict:
    primary = summary.get("primary_disease")
    if not primary or primary.get("class") not in DISEASE_CLASSES:
        return summary

    yellow_ratio = float(visual_evidence.get("yellow_symptom_ratio") or 0.0)
    brown_ratio = float(visual_evidence.get("brown_symptom_ratio") or 0.0)
    dark_ratio = float(visual_evidence.get("dark_symptom_ratio") or 0.0)
    visible_symptom_ratio = yellow_ratio + brown_ratio + dark_ratio
    center_green_ratio = float(visual_evidence.get("center_green_color_ratio") or 0.0)
    green_contour_ratio = float(visual_evidence.get("center_green_contour_area_ratio") or 0.0)
    has_healthy_visual_profile = (
        visible_symptom_ratio < MIN_VISIBLE_DISEASE_SYMPTOM_RATIO
        and yellow_ratio < 0.01
        and brown_ratio < 0.006
        and dark_ratio < 0.006
        and (
            center_green_ratio >= MIN_CENTER_GREEN_RATIO
            or green_contour_ratio >= MIN_CENTER_GREEN_CONTOUR_RATIO
        )
    )

    if not has_healthy_visual_profile:
        return summary

    healthy_candidate = _summary_item_for_class(summary.get("disease_summary", []), HEALTHY_CLASS)
    evidence = {
        "yellow_symptom_ratio": yellow_ratio,
        "brown_symptom_ratio": brown_ratio,
        "dark_symptom_ratio": dark_ratio,
        "visible_symptom_ratio": visible_symptom_ratio,
        "center_green_color_ratio": center_green_ratio,
        "center_green_contour_area_ratio": green_contour_ratio,
        "previous_primary_class": primary.get("class"),
        "previous_primary_score": float(primary.get("score", 0.0)),
    }

    if (
        healthy_candidate
        and healthy_candidate.get("region_count", 0) >= SECONDARY_MIN_REGIONS
        and healthy_candidate.get("best_confidence", 0.0) >= REGION_CONFIDENCE_THRESHOLD
    ):
        return _replace_primary_disease(
            summary,
            HEALTHY_CLASS,
            "healthy_visual_profile_overrides_symptomless_disease",
            evidence,
        )

    visual_healthy = {
        "class": HEALTHY_CLASS,
        "score": 0.7,
        "region_count": 0,
        "best_confidence": 0.7,
        "average_confidence": 0.7,
        "full_image_confidence": 0.0,
        "visual_safeguard": True,
        "calibrated_from": primary.get("class"),
        "calibration_reason": "symptomless_green_leaf_visual_override",
    }

    return {
        **summary,
        "diseases_found": [HEALTHY_CLASS],
        "primary_disease": visual_healthy,
        "secondary_diseases": [],
        "competing_diseases": summary.get("disease_summary", []),
        "disease_summary": [
            visual_healthy,
            *(
                item for item in summary.get("disease_summary", [])
                if item.get("class") != HEALTHY_CLASS
            ),
        ],
        "is_uncertain": False,
        "symptom_safeguard": {
            "applied": True,
            "reason": "symptomless_green_leaf_visual_override",
            "evidence": evidence,
        },
    }


def _apply_supported_healthy_safeguard(summary: dict, visual_evidence: dict) -> dict:
    primary = summary.get("primary_disease")
    if not primary or primary.get("class") not in DISEASE_CLASSES:
        return summary

    healthy_candidate = _supported_summary_candidate(summary, HEALTHY_CLASS)
    if not healthy_candidate:
        return summary

    yellow_ratio = float(visual_evidence.get("yellow_symptom_ratio") or 0.0)
    brown_ratio = float(visual_evidence.get("brown_symptom_ratio") or 0.0)
    dark_ratio = float(visual_evidence.get("dark_symptom_ratio") or 0.0)
    visible_symptom_ratio = yellow_ratio + brown_ratio + dark_ratio
    has_weak_symptom_signal = (
        visible_symptom_ratio < max(MIN_VISIBLE_DISEASE_SYMPTOM_RATIO * 1.5, 0.02)
        and brown_ratio < EARLY_BLIGHT_LESION_RATIO_THRESHOLD
        and dark_ratio < LATE_BLIGHT_DARK_RATIO_THRESHOLD
        and yellow_ratio < LEAF_MOLD_CHLOROSIS_OVERRIDE_RATIO
    )
    healthy_is_competitive = (
        healthy_candidate.get("score", 0.0) >= primary.get("score", 0.0) * 0.65
        or healthy_candidate.get("region_count", 0) >= primary.get("region_count", 0)
    )

    if not (has_weak_symptom_signal and healthy_is_competitive):
        return summary

    return _replace_primary_disease(
        summary,
        HEALTHY_CLASS,
        "supported_healthy_result_overrides_weak_symptom_disease",
        {
            "yellow_symptom_ratio": yellow_ratio,
            "brown_symptom_ratio": brown_ratio,
            "dark_symptom_ratio": dark_ratio,
            "visible_symptom_ratio": visible_symptom_ratio,
            "previous_primary_class": primary.get("class"),
            "previous_primary_score": float(primary.get("score", 0.0)),
            "healthy_score": float(healthy_candidate.get("score", 0.0)),
        },
    )


def _supported_summary_candidate(summary: dict, class_name: str, min_confidence: float = REGION_CONFIDENCE_THRESHOLD) -> dict | None:
    candidate = _summary_item_for_class(summary.get("disease_summary", []), class_name)
    if (
        candidate
        and candidate.get("region_count", 0) >= SECONDARY_MIN_REGIONS
        and candidate.get("best_confidence", 0.0) >= min_confidence
    ):
        return candidate

    return None


def _uncertain_visual_conflict(summary: dict, reason: str, evidence: dict) -> dict:
    return {
        **summary,
        "diseases_found": [],
        "primary_disease": None,
        "secondary_diseases": [],
        "competing_diseases": summary.get("disease_summary", []),
        "is_uncertain": True,
        "visual_consistency": {
            "applied": True,
            "reason": reason,
            "evidence": evidence,
        },
    }


def _apply_class_visual_consistency_safeguards(summary: dict, visual_evidence: dict) -> dict:
    primary = summary.get("primary_disease")
    if not primary:
        return summary

    yellow_ratio = float(visual_evidence.get("yellow_symptom_ratio") or 0.0)
    brown_ratio = float(visual_evidence.get("brown_symptom_ratio") or 0.0)
    dark_ratio = float(visual_evidence.get("dark_symptom_ratio") or 0.0)
    lesion_ratio = brown_ratio + dark_ratio
    visible_symptom_ratio = yellow_ratio + lesion_ratio
    has_leaf_signal = _has_possible_leaf_visual_signal(visual_evidence)
    evidence = {
        "yellow_symptom_ratio": yellow_ratio,
        "brown_symptom_ratio": brown_ratio,
        "dark_symptom_ratio": dark_ratio,
        "lesion_ratio": lesion_ratio,
        "visible_symptom_ratio": visible_symptom_ratio,
        "previous_primary_class": primary.get("class"),
        "previous_primary_score": float(primary.get("score", 0.0)),
    }

    primary_class = primary.get("class")

    if primary_class == NON_LEAF_CLASS and has_leaf_signal:
        for candidate_class in ("Early Blight", "Late Blight", "Leaf Mold", HEALTHY_CLASS):
            candidate = _supported_summary_candidate(summary, candidate_class)
            if candidate:
                return _replace_primary_disease(
                    summary,
                    candidate_class,
                    "leaf_visual_signal_overrides_non_leaf_result",
                    evidence,
                )

        return _uncertain_visual_conflict(
            summary,
            "leaf_visual_signal_conflicts_with_non_leaf_result",
            evidence,
        )

    if primary_class == "Early Blight":
        has_early_lesion_signal = (
            brown_ratio >= EARLY_BLIGHT_BROWN_RATIO_THRESHOLD
            and lesion_ratio >= EARLY_BLIGHT_TOTAL_LESION_RATIO_THRESHOLD
        )
        if has_early_lesion_signal:
            return summary

        healthy_candidate = _summary_item_for_class(summary.get("disease_summary", []), HEALTHY_CLASS)
        if healthy_candidate:
            return _replace_primary_disease(
                summary,
                HEALTHY_CLASS,
                "healthy_leaf_signal_overrides_early_blight_without_lesions",
                evidence,
            )

        if yellow_ratio >= LEAF_MOLD_CHLOROSIS_OVERRIDE_RATIO:
            leaf_mold = _supported_summary_candidate(summary, "Leaf Mold")
            if leaf_mold and leaf_mold.get("score", 0.0) >= primary.get("score", 0.0) * EARLY_BLIGHT_COMPETING_SCORE_RATIO:
                return _replace_primary_disease(
                    summary,
                    "Leaf Mold",
                    "yellow_chlorosis_overrides_early_blight_without_lesions",
                    evidence,
                )

        return _uncertain_visual_conflict(
            summary,
            "early_blight_prediction_missing_lesion_evidence",
            evidence,
        )

    if primary_class == "Leaf Mold":
        has_leaf_mold_signal = yellow_ratio >= LEAF_MOLD_CHLOROSIS_OVERRIDE_RATIO
        if has_leaf_mold_signal:
            return summary

        early_blight = _supported_summary_candidate(summary, "Early Blight", HEALTHY_DISEASE_OVERRIDE_MIN_CONFIDENCE)
        late_blight = _supported_summary_candidate(summary, "Late Blight", HEALTHY_DISEASE_OVERRIDE_MIN_CONFIDENCE)
        if lesion_ratio >= EARLY_BLIGHT_LESION_RATIO_THRESHOLD and early_blight:
            return _replace_primary_disease(
                summary,
                "Early Blight",
                "lesion_signal_overrides_leaf_mold_without_chlorosis",
                evidence,
            )
        if dark_ratio >= LATE_BLIGHT_DARK_RATIO_THRESHOLD and late_blight:
            return _replace_primary_disease(
                summary,
                "Late Blight",
                "dark_lesion_signal_overrides_leaf_mold_without_chlorosis",
                evidence,
            )

    if primary_class == "Late Blight":
        has_late_blight_signal = dark_ratio >= LATE_BLIGHT_DARK_RATIO_THRESHOLD
        if has_late_blight_signal:
            return summary

        leaf_mold = _supported_summary_candidate(summary, "Leaf Mold", HEALTHY_DISEASE_OVERRIDE_MIN_CONFIDENCE)
        early_blight = _supported_summary_candidate(summary, "Early Blight", HEALTHY_DISEASE_OVERRIDE_MIN_CONFIDENCE)
        if yellow_ratio >= LEAF_MOLD_CHLOROSIS_OVERRIDE_RATIO and leaf_mold:
            return _replace_primary_disease(
                summary,
                "Leaf Mold",
                "yellow_chlorosis_overrides_late_blight_without_dark_lesions",
                evidence,
            )
        if brown_ratio >= EARLY_BLIGHT_LESION_RATIO_THRESHOLD and early_blight:
            return _replace_primary_disease(
                summary,
                "Early Blight",
                "brown_lesion_signal_overrides_late_blight_without_dark_lesions",
                evidence,
            )

    return summary


def _summarize_region_results(region_results: list[dict], visual_evidence: dict | None = None) -> dict:
    unique_results = _dedupe_region_results(region_results)
    confident_diseases = [
        item for item in unique_results if item["is_confident_disease"]
    ]

    full_result = next(
        (item for item in unique_results if item["region"] == "full"),
        None,
    )
    disease_summary = []
    soft_disease_evidence = []

    for disease in sorted(REPORTABLE_CLASSES):
        disease_regions = [
            item for item in confident_diseases if item["class"] == disease
        ]
        all_probabilities = [
            item["probabilities"].get(disease, 0.0)
            for item in unique_results
        ]
        sorted_probabilities = sorted(all_probabilities, reverse=True)
        top_probabilities = sorted_probabilities[:5]
        soft_support_count = sum(
            probability >= SOFT_EVIDENCE_THRESHOLD
            for probability in all_probabilities
        )
        soft_score = (
            (max(all_probabilities, default=0.0) * 0.5)
            + ((sum(top_probabilities) / max(len(top_probabilities), 1)) * 0.35)
            + (min(soft_support_count, 5) / 5 * 0.15)
        )
        soft_disease_evidence.append(
            {
                "class": disease,
                "soft_score": float(soft_score),
                "max_probability": float(max(all_probabilities, default=0.0)),
                "top5_average_probability": float(sum(top_probabilities) / max(len(top_probabilities), 1)),
                "support_count_at_threshold": int(soft_support_count),
            }
        )

        if not disease_regions:
            continue

        confidences = [item["confidence"] for item in disease_regions]
        full_confidence = (
            full_result["confidence"]
            if full_result is not None and full_result["class"] == disease
            else 0.0
        )
        region_support = min(len(disease_regions), 3) / 3
        score = (
            (max(confidences) * 0.4)
            + ((sum(confidences) / len(confidences)) * 0.25)
            + (region_support * 0.2)
            + (full_confidence * 0.15)
        )

        disease_summary.append(
            {
                "class": disease,
                "score": float(score),
                "region_count": len(disease_regions),
                "best_confidence": float(max(confidences)),
                "average_confidence": float(sum(confidences) / len(confidences)),
                "full_image_confidence": float(full_confidence),
            }
        )

    disease_summary.sort(key=lambda item: item["score"], reverse=True)
    soft_disease_evidence.sort(key=lambda item: item["soft_score"], reverse=True)
    primary_disease = disease_summary[0] if disease_summary else None
    non_leaf_candidate = _summary_item_for_class(disease_summary, NON_LEAF_CLASS)

    if _has_decisive_non_leaf_summary_conflict(primary_disease, non_leaf_candidate):
        previous_primary = primary_disease
        primary_disease = {
            **non_leaf_candidate,
            "prioritized_over": previous_primary.get("class"),
            "priority_reason": "decisive_non_leaf_model_conflict",
            "priority_evidence": {
                "previous_primary_score": float(previous_primary.get("score", 0.0)),
                "previous_primary_region_count": int(previous_primary.get("region_count", 0)),
                "non_leaf_score": float(non_leaf_candidate.get("score", 0.0)),
                "non_leaf_region_count": int(non_leaf_candidate.get("region_count", 0)),
                "non_leaf_best_confidence": float(non_leaf_candidate.get("best_confidence", 0.0)),
                "non_leaf_average_confidence": float(non_leaf_candidate.get("average_confidence", 0.0)),
            },
        }
        disease_summary = [
            primary_disease,
            *(
                item for item in disease_summary
                if item.get("class") != NON_LEAF_CLASS
            ),
        ]

    secondary_diseases = []

    if primary_disease is not None:
        for disease in disease_summary[1:]:
            has_enough_score = disease["score"] >= SECONDARY_MIN_SCORE
            is_close_to_primary = disease["score"] >= primary_disease["score"] * SECONDARY_SCORE_RATIO
            has_enough_regions = disease["region_count"] >= SECONDARY_MIN_REGIONS
            has_full_image_support = disease["full_image_confidence"] >= REGION_CONFIDENCE_THRESHOLD

            if (has_enough_score and is_close_to_primary and has_enough_regions) or has_full_image_support:
                secondary_diseases.append(disease)

    diseases_found = []
    if primary_disease is not None:
        diseases_found.append(primary_disease["class"])
        diseases_found.extend(item["class"] for item in secondary_diseases)

    full_non_leaf_confidence = (
        full_result["confidence"]
        if full_result is not None and full_result["class"] == NON_LEAF_CLASS
        else 0.0
    )
    center_result = next(
        (item for item in unique_results if item["region"] == "center"),
        None,
    )
    center_non_leaf_confidence = (
        center_result["confidence"]
        if center_result is not None and center_result["class"] == NON_LEAF_CLASS
        else 0.0
    )
    full_disease_confidence = (
        full_result["confidence"]
        if full_result is not None and full_result["class"] in DISEASE_CLASSES
        else 0.0
    )
    center_disease_confidence = (
        center_result["confidence"]
        if center_result is not None and center_result["class"] in DISEASE_CLASSES
        else 0.0
    )
    confident_non_leaf_regions = [
        item for item in unique_results
        if item["class"] == NON_LEAF_CLASS and item["confidence"] >= NON_LEAF_CONFIDENCE_THRESHOLD
    ]
    non_leaf_region_ratio = len(confident_non_leaf_regions) / max(len(unique_results), 1)
    best_supported_leaf_confidence = max(
        (
            item["confidence"]
            for item in unique_results
            if item["class"] in SUPPORTED_LEAF_CLASSES
        ),
        default=0.0,
    )
    max_disease_probability = max(
        (
            max(
                item["probabilities"].get(disease, 0.0)
                for disease in DISEASE_CLASSES
            )
            for item in unique_results
        ),
        default=0.0,
    )
    visual_evidence = visual_evidence or {}
    visual_non_tomato_leaf_profile = has_general_non_tomato_leaf_profile(visual_evidence)
    visible_symptom_ratio = float(
        (visual_evidence.get("yellow_symptom_ratio") or 0.0)
        + (visual_evidence.get("brown_symptom_ratio") or 0.0)
        + (visual_evidence.get("dark_symptom_ratio") or 0.0)
    )
    has_visible_disease_symptoms = visible_symptom_ratio >= MIN_VISIBLE_DISEASE_SYMPTOM_RATIO
    has_global_disease_support = (
        full_disease_confidence >= GLOBAL_DISEASE_SUPPORT_THRESHOLD
        or center_disease_confidence >= GLOBAL_DISEASE_SUPPORT_THRESHOLD
    )
    has_supported_healthy_primary = (
        primary_disease is not None
        and primary_disease.get("class") == HEALTHY_CLASS
    )
    has_strong_global_non_leaf_conflict = (
        full_non_leaf_confidence >= STRONG_GLOBAL_NON_LEAF_THRESHOLD
        and center_non_leaf_confidence >= STRONG_GLOBAL_NON_LEAF_THRESHOLD
    )
    lacks_tomato_disease_support = (
        primary_disease is not None
        and primary_disease.get("class") in DISEASE_CLASSES
        and not has_visible_disease_symptoms
        and not has_global_disease_support
    )
    is_low_support_disease_prediction = (
        lacks_tomato_disease_support
        and (
            primary_disease.get("score", 0.0) < 0.8
            or primary_disease.get("region_count", 0) <= 2
        )
    )
    model_predicts_non_tomato_leaf = (
        (
            full_non_leaf_confidence >= NON_LEAF_CONFIDENCE_THRESHOLD
            and center_non_leaf_confidence >= NON_LEAF_CONFIDENCE_THRESHOLD
            and max_disease_probability < NON_LEAF_DISEASE_PROBABILITY_CEILING
        )
        or (
            non_leaf_region_ratio >= NON_LEAF_REGION_RATIO_THRESHOLD
            and best_supported_leaf_confidence < REGION_CONFIDENCE_THRESHOLD
        )
        or (
            has_strong_global_non_leaf_conflict
            and lacks_tomato_disease_support
            and not has_supported_healthy_primary
        )
        or (
            non_leaf_region_ratio >= NON_LEAF_REGION_RATIO_THRESHOLD
            and lacks_tomato_disease_support
            and not has_supported_healthy_primary
        )
    )
    should_clear_disease_report = is_low_support_disease_prediction
    uncertainty_reason = None
    if should_clear_disease_report:
        uncertainty_reason = "low_support_disease_prediction_without_visual_or_global_support"
    elif primary_disease is None:
        uncertainty_reason = "no_confident_region_class_after_model_and_visual_rules"

    return {
        "diseases_found": [] if should_clear_disease_report else diseases_found,
        "primary_disease": None if should_clear_disease_report else primary_disease,
        "secondary_diseases": [] if should_clear_disease_report else secondary_diseases,
        "competing_diseases": [] if should_clear_disease_report or primary_disease is None else disease_summary[1:],
        "disease_summary": [] if should_clear_disease_report else disease_summary,
        "soft_disease_evidence": soft_disease_evidence,
        "is_supported_leaf_image": True,
        "guardrail_reason": None,
        "non_leaf_evidence": {
            "full_image_confidence": float(full_non_leaf_confidence),
            "center_confidence": float(center_non_leaf_confidence),
            "region_ratio": float(non_leaf_region_ratio),
            "best_supported_leaf_confidence": float(best_supported_leaf_confidence),
            "max_disease_probability": float(max_disease_probability),
            "full_disease_confidence": float(full_disease_confidence),
            "center_disease_confidence": float(center_disease_confidence),
            "visible_symptom_ratio": float(visible_symptom_ratio),
            "has_visible_disease_symptoms": bool(has_visible_disease_symptoms),
            "has_global_disease_support": bool(has_global_disease_support),
            "has_strong_global_non_leaf_conflict": bool(has_strong_global_non_leaf_conflict),
            "visual_non_tomato_leaf_profile": bool(visual_non_tomato_leaf_profile),
            "lacks_tomato_disease_support": bool(lacks_tomato_disease_support),
            "is_low_support_disease_prediction": bool(is_low_support_disease_prediction),
            "model_predicts_non_tomato_leaf": bool(model_predicts_non_tomato_leaf),
        },
        "confident_region_count": len(confident_diseases),
        "unique_region_count": len(unique_results),
        "region_count": len(region_results),
        "confidence_threshold": REGION_CONFIDENCE_THRESHOLD,
        "secondary_score_ratio": SECONDARY_SCORE_RATIO,
        "secondary_min_score": SECONDARY_MIN_SCORE,
        "soft_evidence_threshold": SOFT_EVIDENCE_THRESHOLD,
        "leaf_mold_detectability_warning": next(
            (
                item["max_probability"] < REGION_CONFIDENCE_THRESHOLD
                for item in soft_disease_evidence
                if item["class"] == "Leaf Mold"
            ),
            False,
        ),
        "is_uncertain": should_clear_disease_report or primary_disease is None,
        "uncertainty_reason": uncertainty_reason,
    }


def predict_image(image_bytes: bytes):
    started_at = time.perf_counter()
    image = _load_image(image_bytes)
    visual_evidence = _analyze_leaf_visual_evidence(_resize_for_analysis(image))
    if _is_hard_visual_reject(visual_evidence):
        return {
            "class": NON_LEAF_CLASS,
            "confidence": 1.0,
            "is_uncertain": True,
            "is_supported_leaf_image": False,
            "guardrail_reason": _unsupported_leaf_message(),
            "visual_leaf_evidence": visual_evidence,
            "processing_time_ms": round((time.perf_counter() - started_at) * 1000, 2),
        }

    result, _ = _predict_image_object(image)
    return {
        **result,
        "is_supported_leaf_image": True,
        "guardrail_reason": None,
        "visual_leaf_evidence": visual_evidence,
        "processing_time_ms": round((time.perf_counter() - started_at) * 1000, 2),
    }


def predict_image_regions(image_bytes: bytes, profile: str = "balanced"):
    started_at = time.perf_counter()
    profile = normalize_prediction_profile(profile)
    image = _load_image(image_bytes)
    analysis_image = _resize_for_analysis(image)
    visual_evidence = _analyze_leaf_visual_evidence(analysis_image)

    if _is_hard_visual_reject(visual_evidence):
        return _unsupported_region_response(started_at, profile, visual_evidence)

    regions = _build_region_crops(analysis_image, profile)
    region_results = []

    regular_regions = [region for region in regions if not region["name"].startswith("leaf-candidate")]
    leaf_regions = [region for region in regions if region["name"].startswith("leaf-candidate")]

    if regular_regions:
        predictions = _predict_batch([
            _resize(region["image"])
            for region in regular_regions
        ])

        for region, region_predictions in zip(regular_regions, predictions):
            result = _probabilities_to_result(region_predictions)
            region_results.append(
                {
                    "region": region["name"],
                    "bbox": region["bbox"],
                    "bbox_ratio": region["bbox_ratio"],
                    **result,
                    "is_confident_disease": (
                        result["class"] in REPORTABLE_CLASSES
                        and result["confidence"] >= REGION_CONFIDENCE_THRESHOLD
                    ),
                }
            )

    if leaf_regions:
        leaf_variant_groups = []
        leaf_variant_images = []
        for region in leaf_regions:
            variants = (
                _build_fast_leaf_variants(region["image"])
                if profile == "fast"
                else _build_image_variants(region["image"], "fast")
            )
            leaf_variant_groups.append((region, len(variants)))
            leaf_variant_images.extend(variants)

        leaf_predictions = _predict_batch(leaf_variant_images)
        offset = 0

        for region, variant_count in leaf_variant_groups:
            variant_predictions = leaf_predictions[offset:offset + variant_count]
            offset += variant_count
            predictions, variant_evidence = _combine_variant_predictions(variant_predictions)
            result = _probabilities_to_result(predictions)
            region_results.append(
                {
                    "region": region["name"],
                    "bbox": region["bbox"],
                    "bbox_ratio": region["bbox_ratio"],
                    **result,
                    "variant_count": variant_count,
                    "variant_evidence": variant_evidence,
                    "leaf_focused": True,
                    "is_confident_disease": (
                        result["class"] in REPORTABLE_CLASSES
                        and result["confidence"] >= REGION_CONFIDENCE_THRESHOLD
                    ),
                }
            )

    region_results.sort(key=lambda item: item["confidence"], reverse=True)
    summary = _summarize_region_results(region_results, visual_evidence)
    summary = apply_class_rules(summary, visual_evidence)
    if not summary.get("calibration", {}).get("applied"):
        summary = {
            **summary,
            "calibration": {"applied": False, "disabled": True, "reason": "model_output_only"},
        }

    return {
        "summary": {
            **summary,
            "prediction_profile": profile,
            "visual_leaf_evidence": visual_evidence,
            "processing_time_ms": round((time.perf_counter() - started_at) * 1000, 2),
        },
        "regions": region_results,
    }
