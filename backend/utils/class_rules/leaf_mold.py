from .common import (
    EARLY_BLIGHT_BROWN_RATIO_THRESHOLD,
    EARLY_BLIGHT_TOTAL_LESION_RATIO_THRESHOLD,
    HEALTHY_DISEASE_OVERRIDE_MIN_CONFIDENCE,
    LATE_BLIGHT_DARK_RATIO_THRESHOLD,
    LEAF_MOLD_CHLOROSIS_OVERRIDE_RATIO,
    replace_primary,
    supported_candidate,
    symptom_evidence,
)


def apply_leaf_mold_rule(summary: dict, visual_evidence: dict) -> dict:
    primary = summary.get("primary_disease")
    if not primary or primary.get("class") != "Leaf Mold":
        return summary

    evidence = symptom_evidence(visual_evidence)
    if evidence["yellow_symptom_ratio"] >= LEAF_MOLD_CHLOROSIS_OVERRIDE_RATIO:
        return summary

    early_blight = supported_candidate(summary, "Early Blight", HEALTHY_DISEASE_OVERRIDE_MIN_CONFIDENCE)
    late_blight = supported_candidate(summary, "Late Blight", HEALTHY_DISEASE_OVERRIDE_MIN_CONFIDENCE)

    if (
        evidence["brown_symptom_ratio"] >= EARLY_BLIGHT_BROWN_RATIO_THRESHOLD
        and evidence["lesion_ratio"] >= EARLY_BLIGHT_TOTAL_LESION_RATIO_THRESHOLD
        and early_blight
    ):
        return replace_primary(
            summary,
            "Early Blight",
            "lesion_signal_overrides_leaf_mold_without_chlorosis",
            evidence,
        )

    if evidence["dark_symptom_ratio"] >= LATE_BLIGHT_DARK_RATIO_THRESHOLD and late_blight:
        return replace_primary(
            summary,
            "Late Blight",
            "dark_lesion_signal_overrides_leaf_mold_without_chlorosis",
            evidence,
        )

    return summary
