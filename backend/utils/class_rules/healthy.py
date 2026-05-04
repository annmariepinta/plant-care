from .common import (
    DISEASE_CLASSES,
    HEALTHY_CLASS,
    LEAF_MOLD_CHLOROSIS_OVERRIDE_RATIO,
    LATE_BLIGHT_DARK_RATIO_THRESHOLD,
    MIN_VISIBLE_DISEASE_SYMPTOM_RATIO,
    replace_primary,
    supported_candidate,
    symptom_evidence,
    uncertain,
)


def apply_healthy_rule(summary: dict, visual_evidence: dict) -> dict:
    primary = summary.get("primary_disease")
    if not primary or primary.get("class") != HEALTHY_CLASS:
        return summary

    evidence = symptom_evidence(visual_evidence)
    has_clear_symptoms = (
        evidence["visible_symptom_ratio"] >= max(MIN_VISIBLE_DISEASE_SYMPTOM_RATIO * 2.5, 0.035)
        and (
            evidence["yellow_symptom_ratio"] >= 0.025
            or evidence["brown_symptom_ratio"] >= 0.012
            or evidence["dark_symptom_ratio"] >= 0.012
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
    if best_disease and supported_candidate(summary, best_disease["class"], min_confidence=0.75):
        return replace_primary(
            summary,
            best_disease["class"],
            "visible_symptoms_prevent_healthy_result",
            {
                **evidence,
                "previous_healthy_score": float(primary.get("score", 0.0)),
                "best_model_disease_class": best_disease.get("class"),
                "best_model_disease_confidence": float(best_disease.get("best_confidence", 0.0)),
            },
        )

    return uncertain(
        summary,
        "visible_symptoms_conflict_with_healthy_result",
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


def apply_supported_healthy_rule(summary: dict, visual_evidence: dict) -> dict:
    primary = summary.get("primary_disease")
    if not primary or primary.get("class") not in DISEASE_CLASSES:
        return summary

    healthy_candidate = supported_candidate(summary, HEALTHY_CLASS)
    if not healthy_candidate:
        return summary

    evidence = symptom_evidence(visual_evidence)
    has_weak_symptom_signal = (
        evidence["visible_symptom_ratio"] < max(MIN_VISIBLE_DISEASE_SYMPTOM_RATIO * 1.5, 0.02)
        and evidence["brown_symptom_ratio"] < 0.008
        and evidence["dark_symptom_ratio"] < LATE_BLIGHT_DARK_RATIO_THRESHOLD
        and evidence["yellow_symptom_ratio"] < LEAF_MOLD_CHLOROSIS_OVERRIDE_RATIO
    )
    healthy_is_competitive = (
        healthy_candidate.get("score", 0.0) >= primary.get("score", 0.0) * 0.5
        or healthy_candidate.get("region_count", 0) >= max(primary.get("region_count", 0) // 2, 1)
    )

    if has_weak_symptom_signal and healthy_is_competitive:
        return replace_primary(
            summary,
            HEALTHY_CLASS,
            "supported_healthy_result_overrides_weak_symptom_disease",
            {
                **evidence,
                "previous_primary_class": primary.get("class"),
                "previous_primary_score": float(primary.get("score", 0.0)),
                "healthy_score": float(healthy_candidate.get("score", 0.0)),
            },
        )

    return summary
