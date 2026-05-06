def apply_class_rules(summary: dict, visual_evidence: dict) -> dict:
    """Keep classification aligned with the trained five-class model.

    Visual analysis is still used before inference to reject obvious non-leaf
    uploads. Once an image reaches the model, avoid hand-authored disease
    correction rules so late blight, leaf mold, healthy, and non-tomato leaves
    are not converted into Early Blight by heuristics.
    """
    return summary
