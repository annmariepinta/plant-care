from .common import (
    EARLY_BLIGHT_BROWN_RATIO_THRESHOLD,
    HEALTHY_DISEASE_OVERRIDE_MIN_CONFIDENCE,
    LATE_BLIGHT_DARK_RATIO_THRESHOLD,
    LEAF_MOLD_CHLOROSIS_OVERRIDE_RATIO,
    replace_primary,
    supported_candidate,
    symptom_evidence,
)


def apply_late_blight_rule(summary: dict, visual_evidence: dict) -> dict:
    primary = summary.get("primary_disease")
    if not primary or primary.get("class") != "Late Blight":
        return summary

    evidence = symptom_evidence(visual_evidence)
    if evidence["dark_symptom_ratio"] >= LATE_BLIGHT_DARK_RATIO_THRESHOLD:
        return summary

    leaf_mold = supported_candidate(summary, "Leaf Mold", HEALTHY_DISEASE_OVERRIDE_MIN_CONFIDENCE)
    early_blight = supported_candidate(summary, "Early Blight", HEALTHY_DISEASE_OVERRIDE_MIN_CONFIDENCE)

    if evidence["yellow_symptom_ratio"] >= LEAF_MOLD_CHLOROSIS_OVERRIDE_RATIO and leaf_mold:
        return replace_primary(
            summary,
            "Leaf Mold",
            "yellow_chlorosis_overrides_late_blight_without_dark_lesions",
            evidence,
        )

    if evidence["brown_symptom_ratio"] >= EARLY_BLIGHT_BROWN_RATIO_THRESHOLD and early_blight:
        return replace_primary(
            summary,
            "Early Blight",
            "brown_lesion_signal_overrides_late_blight_without_dark_lesions",
            evidence,
        )

    return summary
