from .common import (
    EARLY_BLIGHT_BROWN_RATIO_THRESHOLD,
    EARLY_BLIGHT_TOTAL_LESION_RATIO_THRESHOLD,
    LATE_BLIGHT_DARK_RATIO_THRESHOLD,
    LEAF_MOLD_CHLOROSIS_OVERRIDE_RATIO,
    replace_primary,
    supported_candidate,
    symptom_evidence,
)


def apply_visible_disease_fallback(summary: dict, visual_evidence: dict) -> dict:
    if summary.get("primary_disease"):
        return summary

    evidence = symptom_evidence(visual_evidence)
    has_brown_lesions = (
        evidence["brown_symptom_ratio"] >= EARLY_BLIGHT_BROWN_RATIO_THRESHOLD
        or evidence["lesion_ratio"] >= EARLY_BLIGHT_TOTAL_LESION_RATIO_THRESHOLD
    )
    has_dark_lesions = evidence["dark_symptom_ratio"] >= LATE_BLIGHT_DARK_RATIO_THRESHOLD
    has_yellow_chlorosis = evidence["yellow_symptom_ratio"] >= LEAF_MOLD_CHLOROSIS_OVERRIDE_RATIO

    if not (has_brown_lesions or has_dark_lesions or has_yellow_chlorosis):
        return summary

    candidates = []
    if has_brown_lesions:
        candidates.append("Early Blight")
    if has_dark_lesions:
        candidates.append("Late Blight")
    if has_yellow_chlorosis:
        candidates.append("Leaf Mold")

    for candidate_class in candidates:
        candidate = supported_candidate(summary, candidate_class, min_confidence=0.35)
        if candidate:
            return replace_primary(
                summary,
                candidate_class,
                "visible_disease_symptoms_restore_supported_model_class",
                evidence,
            )

    fallback_class = candidates[0]
    return replace_primary(
        summary,
        fallback_class,
        "visible_disease_symptoms_visual_fallback",
        evidence,
    )
