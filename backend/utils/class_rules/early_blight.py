from .common import (
    EARLY_BLIGHT_BROWN_RATIO_THRESHOLD,
    EARLY_BLIGHT_COMPETING_SCORE_RATIO,
    EARLY_BLIGHT_TOTAL_LESION_RATIO_THRESHOLD,
    HEALTHY_CLASS,
    LEAF_MOLD_CHLOROSIS_OVERRIDE_RATIO,
    has_healthy_visual_profile,
    replace_primary,
    summary_item,
    supported_candidate,
    symptom_evidence,
    uncertain,
    visual_healthy,
)


def apply_early_blight_rule(summary: dict, visual_evidence: dict) -> dict:
    primary = summary.get("primary_disease")
    if not primary or primary.get("class") != "Early Blight":
        return summary

    evidence = symptom_evidence(visual_evidence)
    has_early_lesion_signal = (
        evidence["brown_symptom_ratio"] >= EARLY_BLIGHT_BROWN_RATIO_THRESHOLD
        and evidence["lesion_ratio"] >= EARLY_BLIGHT_TOTAL_LESION_RATIO_THRESHOLD
    )
    if has_early_lesion_signal:
        return summary

    healthy_candidate = summary_item(summary, HEALTHY_CLASS)
    if healthy_candidate:
        return replace_primary(
            summary,
            HEALTHY_CLASS,
            "healthy_leaf_signal_overrides_early_blight_without_lesions",
            evidence,
        )

    if has_healthy_visual_profile(visual_evidence):
        return visual_healthy(
            summary,
            "healthy_visual_profile_overrides_early_blight_without_lesions",
            evidence,
        )

    if evidence["yellow_symptom_ratio"] >= LEAF_MOLD_CHLOROSIS_OVERRIDE_RATIO:
        leaf_mold = supported_candidate(summary, "Leaf Mold")
        if leaf_mold and leaf_mold.get("score", 0.0) >= primary.get("score", 0.0) * EARLY_BLIGHT_COMPETING_SCORE_RATIO:
            return replace_primary(
                summary,
                "Leaf Mold",
                "yellow_chlorosis_overrides_early_blight_without_lesions",
                evidence,
            )

    return uncertain(
        summary,
        "early_blight_prediction_missing_lesion_evidence",
        evidence,
    )
