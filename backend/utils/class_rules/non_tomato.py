from .common import (
    DISEASE_CLASSES,
    HEALTHY_CLASS,
    NON_LEAF_CLASS,
    has_broad_non_tomato_leaf_profile,
    has_general_non_tomato_leaf_profile,
    has_large_banana_like_leaf_profile,
    has_possible_leaf_signal,
    metric,
    replace_primary,
    supported_candidate,
    symptom_evidence,
    visual_non_tomato,
)


TOMATO_CLASSES = DISEASE_CLASSES | {HEALTHY_CLASS}


def has_supported_tomato_candidate(summary: dict) -> bool:
    return any(
        supported_candidate(summary, candidate_class)
        for candidate_class in TOMATO_CLASSES
    )


def apply_non_tomato_rule(summary: dict, visual_evidence: dict) -> dict:
    primary = summary.get("primary_disease")
    primary_class = primary.get("class") if primary else None
    evidence = symptom_evidence(visual_evidence)
    has_visible_symptoms = (
        evidence["visible_symptom_ratio"] >= 0.012
        or evidence["yellow_symptom_ratio"] >= 0.018
        or evidence["brown_symptom_ratio"] >= 0.008
        or evidence["dark_symptom_ratio"] >= 0.012
    )
    is_multi_leaf_scene = bool(visual_evidence.get("is_multi_leaf_scene"))
    has_tomato_primary = primary_class in TOMATO_CLASSES
    has_tomato_support = has_supported_tomato_candidate(summary)

    if (
        has_large_banana_like_leaf_profile(visual_evidence)
        and not has_tomato_primary
        and not has_tomato_support
    ):
        return visual_non_tomato(
            summary,
            "large_broad_banana_like_leaf_detected",
            evidence,
        )

    if (
        has_general_non_tomato_leaf_profile(visual_evidence)
        and not has_tomato_primary
        and not has_tomato_support
    ):
        return visual_non_tomato(
            summary,
            "general_non_tomato_leaf_profile_detected",
            evidence,
        )

    if is_multi_leaf_scene and has_visible_symptoms:
        return summary

    has_clean_leaf_without_tomato_shape = (
        has_possible_leaf_signal(visual_evidence)
        and not bool(visual_evidence.get("has_leaf_like_color"))
        and not has_visible_symptoms
        and (
            metric(visual_evidence, "center_green_color_ratio") >= 0.08
            or metric(visual_evidence, "green_contour_area_ratio") >= 0.08
            or metric(visual_evidence, "max_contour_area_ratio") >= 0.12
        )
    )
    if has_clean_leaf_without_tomato_shape:
        return visual_non_tomato(
            summary,
            "clean_leaf_without_tomato_shape_detected",
            evidence,
        )

    non_leaf_evidence = summary.get("non_leaf_evidence", {})
    has_strong_non_leaf_model_signal = (
        bool(non_leaf_evidence.get("model_predicts_non_tomato_leaf"))
        or float(non_leaf_evidence.get("full_image_confidence", 0.0)) >= 0.75
        or float(non_leaf_evidence.get("center_confidence", 0.0)) >= 0.75
        or float(non_leaf_evidence.get("region_ratio", 0.0)) >= 0.25
    )
    has_tomato_disease_symptom_signal = (
        evidence["visible_symptom_ratio"] >= 0.018
        or evidence["yellow_symptom_ratio"] >= 0.025
        or evidence["brown_symptom_ratio"] >= 0.01
        or evidence["dark_symptom_ratio"] >= 0.018
    )
    if has_strong_non_leaf_model_signal and not has_tomato_disease_symptom_signal:
        return visual_non_tomato(
            summary,
            "non_leaf_model_signal_without_tomato_symptoms",
            {
                **evidence,
                "non_leaf_evidence": non_leaf_evidence,
            },
        )

    if (
        not primary
        and has_possible_leaf_signal(visual_evidence)
        and not has_visible_symptoms
        and not supported_candidate(summary, HEALTHY_CLASS, min_confidence=0.45)
    ):
        return visual_non_tomato(
            summary,
            "uncertain_clean_leaf_defaults_to_non_tomato",
            {
                **evidence,
                "non_leaf_evidence": non_leaf_evidence,
            },
        )

    if has_broad_non_tomato_leaf_profile(visual_evidence):
        if has_tomato_primary or has_tomato_support:
            return summary

        if not primary or primary.get("class") != NON_LEAF_CLASS:
            return visual_non_tomato(
                summary,
                "broad_simple_leaf_profile_detected",
                evidence,
            )
        return summary

    if not primary or primary.get("class") != NON_LEAF_CLASS:
        return summary

    if not has_possible_leaf_signal(visual_evidence):
        return summary

    for candidate_class in ("Early Blight", "Late Blight", "Leaf Mold", HEALTHY_CLASS):
        candidate = supported_candidate(summary, candidate_class)
        if candidate:
            return replace_primary(
                summary,
                candidate_class,
                "leaf_visual_signal_overrides_non_leaf_result",
                evidence,
            )

    return {
        **summary,
        "is_uncertain": False,
        "uncertainty_reason": None,
        "visual_consistency": {
            "applied": True,
            "from": NON_LEAF_CLASS,
            "to": NON_LEAF_CLASS,
            "reason": "leaf_visual_signal_keeps_non_tomato_leaf_result",
            "evidence": evidence,
        },
    }
