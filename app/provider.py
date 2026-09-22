from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

from .config import settings
from .schemas import ImageTags


def _subject_from_id(image_id: str) -> str:
    value = image_id.rsplit("_", 1)[0].replace("_", " ")
    return {"red fox": "red fox", "gray wolf": "gray wolf"}.get(value, value)


def fixture_tags(image_id: str) -> ImageTags:
    subject = _subject_from_id(image_id)
    confidence = 0.55 if image_id.endswith("_10") else 0.95
    return ImageTags(
        subject=subject,
        category="animal",
        attributes=["wildlife", "animal", subject],
        caption=f"A {subject} in a natural outdoor setting",
        confidence=confidence,
    )


def _fixture_vector(text: str) -> list[float]:
    subject = "unknown"
    lowered = text.lower()
    for candidate in ("red fox", "gray wolf", "dog", "bear", "deer", "glacier"):
        if candidate in lowered or (candidate == "red fox" and "vulpes vulpes" in lowered) or (candidate == "gray wolf" and "canis lupus" in lowered):
            subject = candidate
            break
    digest = hashlib.sha256(subject.encode()).digest()
    vector = [((byte / 255.0) * 2) - 1 for byte in digest[:16]]
    return vector


def fixture_embedding(text: str) -> tuple[list[float], dict[str, int]]:
    return _fixture_vector(text), {"prompt_tokens": max(1, len(text.split())), "candidates_tokens": 0}


def _client():
    if not settings.gemini_api_key:
        raise RuntimeError("GEMINI_API_KEY is required when AI_MODE=gemini")
    from google import genai

    return genai.Client(api_key=settings.gemini_api_key)


def vision_tags(image_id: str, image_path: Path | None = None) -> tuple[ImageTags, dict[str, int]]:
    if settings.ai_mode == "fixture":
        return fixture_tags(image_id), {"prompt_tokens": 0, "candidates_tokens": 0}
    from google.genai import types

    if image_path is None or not image_path.exists():
        raise FileNotFoundError(f"missing local image: {image_path}")
    response = _client().models.generate_content(
        model=settings.vision_model,
        contents=[types.Part.from_bytes(data=image_path.read_bytes(), mime_type="image/jpeg"), "Return the image metadata as JSON."],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_json_schema=ImageTags.model_json_schema(),
        ),
    )
    tags = ImageTags.model_validate_json(response.text)
    usage = getattr(response, "usage_metadata", None)
    return tags, {"prompt_tokens": int(getattr(usage, "prompt_token_count", 0) or 0), "candidates_tokens": int(getattr(usage, "candidates_token_count", 0) or 0)}


def embed_text(text: str) -> tuple[list[float], dict[str, int]]:
    if settings.ai_mode == "fixture":
        return fixture_embedding(text)
    response = _client().models.embed_content(
        model=settings.embedding_model,
        contents=f"task: sentence similarity | query: {text}",
    )
    embedding = response.embeddings[0]
    values = list(embedding.values or [])
    return values, {"prompt_tokens": max(1, len(text.split())), "candidates_tokens": 0}

