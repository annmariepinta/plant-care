DISEASE_CLASSES = {"Early Blight", "Late Blight", "Leaf Mold"}
HEALTHY_CLASS = "Healthy Tomato Leaf"
NON_LEAF_CLASS = "Non-Tomato Leaf"

REGION_CONFIDENCE_THRESHOLD = 0.6
SECONDARY_MIN_REGIONS = 2
MIN_VISIBLE_DISEASE_SYMPTOM_RATIO = 0.012
MIN_CENTER_GREEN_RATIO = 0.012
MIN_CENTER_GREEN_CONTOUR_RATIO = 0.006
LEAF_MOLD_CHLOROSIS_OVERRIDE_RATIO = 0.04
LATE_BLIGHT_DARK_RATIO_THRESHOLD = 0.055
EARLY_BLIGHT_COMPETING_SCORE_RATIO = 0.78
EARLY_BLIGHT_BROWN_RATIO_THRESHOLD = 0.012
EARLY_BLIGHT_TOTAL_LESION_RATIO_THRESHOLD = 0.02
HEALTHY_DISEASE_OVERRIDE_MIN_CONFIDENCE = 0.75
BROAD_NON_TOMATO_AREA_RATIO = 0.12
BROAD_NON_TOMATO_CENTER_GREEN_RATIO = 0.08
BROAD_NON_TOMATO_SOLIDITY = 0.62
BROAD_NON_TOMATO_EXTENT = 0.28


def metric(visual_evidence: dict, key: str) -> float:
    value = visual_evidence.get(key)
    return float(value) if isinstance(value, (int, float)) else 0.0


def symptom_evidence(visual_evidence: dict) -> dict:
    yellow_ratio = metric(visual_evidence, "yellow_symptom_ratio")
    brown_ratio = metric(visual_evidence, "brown_symptom_ratio")
    dark_ratio = metric(visual_evidence, "dark_symptom_ratio")
    lesion_ratio = brown_ratio + dark_ratio

    return {
        "yellow_symptom_ratio": yellow_ratio,
        "brown_symptom_ratio": brown_ratio,
        "dark_symptom_ratio": dark_ratio,
        "lesion_ratio": lesion_ratio,
        "visible_symptom_ratio": yellow_ratio + lesion_ratio,
        "center_green_color_ratio": metric(visual_evidence, "center_green_color_ratio"),
        "center_green_contour_area_ratio": metric(visual_evidence, "center_green_contour_area_ratio"),
    }


def summary_item(summary: dict, class_name: str) -> dict | None:
    return next(
        (
            item for item in summary.get("disease_summary", [])
            if item.get("class") == class_name
        ),
        None,
    )


def supported_candidate(
    summary: dict,
    class_name: str,
    min_confidence: float = REGION_CONFIDENCE_THRESHOLD,
) -> dict | None:
    candidate = summary_item(summary, class_name)
    if (
        candidate
        and candidate.get("region_count", 0) >= SECONDARY_MIN_REGIONS
        and candidate.get("best_confidence", 0.0) >= min_confidence
    ):
        return candidate

    return None


def replace_primary(summary: dict, new_class: str, reason: str, evidence: dict) -> dict:
    disease_summary = list(summary.get("disease_summary", []))
    old_primary = summary.get("primary_disease")
    old_class = old_primary.get("class") if old_primary else None
    replacement = summary_item(summary, new_class)

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

    replacement = {
        **replacement,
        "calibrated_from": old_class,
        "calibration_reason": reason,
    }
    disease_summary = [
        item for item in disease_summary
        if item.get("class") != new_class
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
        "is_uncertain": False,
        "visual_consistency": {
            "applied": True,
            "from": old_class,
            "to": new_class,
            "reason": reason,
            "evidence": evidence,
        },
    }


def uncertain(summary: dict, reason: str, evidence: dict) -> dict:
    return {
        **summary,
        "diseases_found": [],
        "primary_disease": None,
        "secondary_diseases": [],
        "competing_diseases": summary.get("disease_summary", []),
        "is_uncertain": True,
        "uncertainty_reason": reason,
        "visual_consistency": {
            "applied": True,
            "reason": reason,
            "evidence": evidence,
        },
    }


def visual_non_tomato(summary: dict, reason: str, evidence: dict) -> dict:
    primary = summary.get("primary_disease") or {}
    replacement = {
        "class": NON_LEAF_CLASS,
        "score": 0.8,
        "region_count": 0,
        "best_confidence": 0.8,
        "average_confidence": 0.8,
        "full_image_confidence": 0.0,
        "visual_safeguard": True,
        "calibrated_from": primary.get("class"),
        "calibration_reason": reason,
    }

    return {
        **summary,
        "diseases_found": [NON_LEAF_CLASS],
        "primary_disease": replacement,
        "secondary_diseases": [],
        "competing_diseases": summary.get("disease_summary", []),
        "disease_summary": [
            replacement,
            *(
                item for item in summary.get("disease_summary", [])
                if item.get("class") != NON_LEAF_CLASS
            ),
        ],
        "is_uncertain": False,
        "visual_consistency": {
            "applied": True,
            "from": primary.get("class"),
            "to": NON_LEAF_CLASS,
            "reason": reason,
            "evidence": evidence,
        },
    }


def visual_healthy(summary: dict, reason: str, evidence: dict) -> dict:
    primary = summary.get("primary_disease") or {}
    replacement = {
        "class": HEALTHY_CLASS,
        "score": 0.7,
        "region_count": 0,
        "best_confidence": 0.7,
        "average_confidence": 0.7,
        "full_image_confidence": 0.0,
        "visual_safeguard": True,
        "calibrated_from": primary.get("class"),
        "calibration_reason": reason,
    }

    return {
        **summary,
        "diseases_found": [HEALTHY_CLASS],
        "primary_disease": replacement,
        "secondary_diseases": [],
        "competing_diseases": summary.get("disease_summary", []),
        "disease_summary": [
            replacement,
            *(
                item for item in summary.get("disease_summary", [])
                if item.get("class") != HEALTHY_CLASS
            ),
        ],
        "is_uncertain": False,
        "visual_consistency": {
            "applied": True,
            "from": primary.get("class"),
            "to": HEALTHY_CLASS,
            "reason": reason,
            "evidence": evidence,
        },
    }


def has_possible_leaf_signal(visual_evidence: dict) -> bool:
    return (
        bool(visual_evidence.get("has_enough_total_plant_signal"))
        or bool(visual_evidence.get("has_centered_leaf_signal"))
        or bool(visual_evidence.get("has_centered_symptom_signal"))
        or metric(visual_evidence, "plant_color_ratio") >= 0.025
        or metric(visual_evidence, "green_color_ratio") >= 0.012
        or metric(visual_evidence, "green_contour_area_ratio") >= 0.005
        or metric(visual_evidence, "max_contour_area_ratio") >= 0.018
        or int(metric(visual_evidence, "candidate_count")) > 0
    )


def has_healthy_visual_profile(visual_evidence: dict) -> bool:
    evidence = symptom_evidence(visual_evidence)
    return (
        evidence["visible_symptom_ratio"] < MIN_VISIBLE_DISEASE_SYMPTOM_RATIO
        and evidence["yellow_symptom_ratio"] < 0.01
        and evidence["brown_symptom_ratio"] < 0.006
        and evidence["dark_symptom_ratio"] < 0.006
        and (
            evidence["center_green_color_ratio"] >= MIN_CENTER_GREEN_RATIO
            or evidence["center_green_contour_area_ratio"] >= MIN_CENTER_GREEN_CONTOUR_RATIO
            or has_possible_leaf_signal(visual_evidence)
        )
    )


def has_broad_non_tomato_leaf_profile(visual_evidence: dict) -> bool:
    evidence = symptom_evidence(visual_evidence)
    has_visible_disease_symptoms = (
        evidence["visible_symptom_ratio"] >= MIN_VISIBLE_DISEASE_SYMPTOM_RATIO
        or evidence["yellow_symptom_ratio"] >= 0.018
        or evidence["brown_symptom_ratio"] >= 0.008
        or evidence["dark_symptom_ratio"] >= 0.012
    )
    if has_visible_disease_symptoms:
        return False

    has_large_single_leaf = (
        metric(visual_evidence, "green_contour_area_ratio") >= BROAD_NON_TOMATO_AREA_RATIO
        and metric(visual_evidence, "center_green_color_ratio") >= BROAD_NON_TOMATO_CENTER_GREEN_RATIO
        and (
            metric(visual_evidence, "largest_green_contour_solidity") >= BROAD_NON_TOMATO_SOLIDITY
            or metric(visual_evidence, "largest_green_contour_extent") >= BROAD_NON_TOMATO_EXTENT
        )
    )
    has_dominant_smooth_leaf = (
        metric(visual_evidence, "center_green_color_ratio") >= 0.18
        and metric(visual_evidence, "largest_green_contour_dominance_ratio") >= 0.36
        and metric(visual_evidence, "largest_green_contour_aspect_ratio") >= 1.45
    )

    return (
        bool(visual_evidence.get("is_broad_simple_leaf_like"))
        or has_large_single_leaf
        or has_dominant_smooth_leaf
    )


def has_large_banana_like_leaf_profile(visual_evidence: dict) -> bool:
    evidence = symptom_evidence(visual_evidence)
    has_large_leaf_signal = (
        metric(visual_evidence, "plant_color_ratio") >= 0.12
        or metric(visual_evidence, "green_color_ratio") >= 0.08
        or metric(visual_evidence, "center_green_color_ratio") >= 0.06
        or metric(visual_evidence, "green_contour_area_ratio") >= 0.06
        or metric(visual_evidence, "max_contour_area_ratio") >= 0.1
    )
    has_broad_smooth_shape = (
        metric(visual_evidence, "largest_green_contour_aspect_ratio") >= 1.25
        or metric(visual_evidence, "largest_green_contour_solidity") >= 0.5
        or metric(visual_evidence, "largest_green_contour_extent") >= 0.22
        or metric(visual_evidence, "largest_green_contour_dominance_ratio") >= 0.28
    )
    has_dominant_smooth_leaf = (
        metric(visual_evidence, "green_contour_area_ratio") >= 0.12
        and metric(visual_evidence, "center_green_color_ratio") >= 0.08
        and metric(visual_evidence, "largest_green_contour_aspect_ratio") >= 1.25
        and (
            metric(visual_evidence, "largest_green_contour_dominance_ratio") >= 0.32
            or metric(visual_evidence, "largest_green_contour_solidity") >= 0.5
            or metric(visual_evidence, "largest_green_contour_extent") >= 0.24
        )
    )
    has_clean_leaf_surface = (
        metric(visual_evidence, "brown_symptom_ratio") < 0.006
        and metric(visual_evidence, "dark_symptom_ratio") < 0.01
        and metric(visual_evidence, "yellow_symptom_ratio") < 0.018
    )
    has_tomato_disease_symptoms = (
        evidence["visible_symptom_ratio"] >= MIN_VISIBLE_DISEASE_SYMPTOM_RATIO
        or evidence["yellow_symptom_ratio"] >= 0.018
        or evidence["brown_symptom_ratio"] >= 0.008
        or evidence["dark_symptom_ratio"] >= 0.012
    )
    has_no_clear_tomato_chlorosis_or_lesions = (
        evidence["yellow_symptom_ratio"] < 0.018
        and evidence["brown_symptom_ratio"] < 0.012
    )

    if has_tomato_disease_symptoms:
        return (
            has_large_leaf_signal
            and has_dominant_smooth_leaf
            and has_no_clear_tomato_chlorosis_or_lesions
        )

    return has_large_leaf_signal and has_broad_smooth_shape and has_clean_leaf_surface


def has_general_non_tomato_leaf_profile(visual_evidence: dict) -> bool:
    evidence = symptom_evidence(visual_evidence)
    has_centered_leaf_mass = (
        metric(visual_evidence, "center_green_color_ratio") >= 0.08
        or metric(visual_evidence, "center_green_contour_area_ratio") >= 0.06
    )
    has_large_leaf_mass = (
        metric(visual_evidence, "green_contour_area_ratio") >= 0.08
        or metric(visual_evidence, "max_contour_area_ratio") >= 0.12
        or metric(visual_evidence, "plant_color_ratio") >= 0.18
        or metric(visual_evidence, "green_color_ratio") >= 0.12
    )
    has_simple_leaf_geometry = (
        bool(visual_evidence.get("is_broad_simple_leaf_like"))
        or metric(visual_evidence, "largest_green_contour_aspect_ratio") >= 1.35
        or metric(visual_evidence, "largest_green_contour_solidity") >= 0.52
        or metric(visual_evidence, "largest_green_contour_extent") >= 0.24
        or metric(visual_evidence, "largest_green_contour_dominance_ratio") >= 0.3
    )
    has_clear_tomato_disease_marks = (
        evidence["yellow_symptom_ratio"] >= 0.025
        or evidence["brown_symptom_ratio"] >= 0.016
    )

    if has_clear_tomato_disease_marks:
        return False

    return (
        has_possible_leaf_signal(visual_evidence)
        and has_centered_leaf_mass
        and has_large_leaf_mass
        and has_simple_leaf_geometry
    )
