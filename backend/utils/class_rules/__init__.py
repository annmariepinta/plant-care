from .early_blight import apply_early_blight_rule
from .disease_fallback import apply_visible_disease_fallback
from .healthy import apply_healthy_rule, apply_supported_healthy_rule
from .late_blight import apply_late_blight_rule
from .leaf_mold import apply_leaf_mold_rule
from .non_tomato import apply_non_tomato_rule


def apply_class_rules(summary: dict, visual_evidence: dict) -> dict:
    for rule in (
        apply_early_blight_rule,
        apply_leaf_mold_rule,
        apply_late_blight_rule,
        apply_supported_healthy_rule,
        apply_healthy_rule,
        apply_visible_disease_fallback,
        apply_non_tomato_rule,
    ):
        summary = rule(summary, visual_evidence)

    return summary
