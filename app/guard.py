from __future__ import annotations

import math
import re
from typing import Any


def canonical(value: str) -> str:
    value = value.lower().strip()
    replacements = {
        "vulpes vulpes": "red fox",
        "red foxes": "red fox",
        "grey wolf": "gray wolf",
        "canis lupus": "gray wolf",
        "domestic dog": "dog",
        "brown bear": "bear",
    }
    return replacements.get(value, re.sub(r"\s+", " ", value))


def cosine(left: list[float], right: list[float]) -> float:
    if not left or len(left) != len(right):
        return 0.0
    dot = sum(a * b for a, b in zip(left, right))
    left_norm = math.sqrt(sum(a * a for a in left))
    right_norm = math.sqrt(sum(b * b for b in right))
    return dot / (left_norm * right_norm) if left_norm and right_norm else 0.0


def evaluate_candidate(post: dict[str, Any], image: dict[str, Any], similarity: float, confidence_threshold: float, similarity_threshold: float) -> dict[str, Any]:
    tags = image.get("tags") or {}
    reasons: list[dict[str, str]] = []
    confidence = float(tags.get("confidence", 0))
    if image.get("tag_status") != "ready":
        reasons.append({"code": "invalid_metadata", "message": "image metadata is not schema-valid and ready"})
    if confidence < confidence_threshold:
        reasons.append({"code": "low_confidence", "message": f"vision confidence {confidence:.3f} is below {confidence_threshold:.3f}"})
    expected = canonical(str(post.get("subject", "")))
    detected = canonical(str(tags.get("subject", "")))
    if expected and detected and expected != detected:
        reasons.append({"code": "category_mismatch", "message": f"expected {expected}, detected {detected}"})
    if similarity < similarity_threshold:
        reasons.append({"code": "similarity_below_threshold", "message": f"similarity {similarity:.3f} is below {similarity_threshold:.3f}"})
    return {
        "accepted": not reasons,
        "decision": "accepted" if not reasons else "rejected",
        "similarity": round(similarity, 6),
        "reasons": reasons,
    }

