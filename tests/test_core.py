from app.guard import canonical, cosine, evaluate_candidate
from app.provider import fixture_embedding, fixture_tags


def test_schema_rejects_low_confidence_and_guard_flags_it():
    tags = fixture_tags("red_fox_10")
    result = evaluate_candidate(
        {"subject": "red fox"},
        {"tag_status": "flagged", "tags": tags.model_dump()},
        0.99,
        0.70,
        0.70,
    )
    assert not result["accepted"]
    assert {item["code"] for item in result["reasons"]} == {"invalid_metadata", "low_confidence"}


def test_wolf_is_rejected_for_fox_post_with_explanation():
    tags = fixture_tags("gray_wolf_01")
    result = evaluate_candidate(
        {"subject": "red fox"},
        {"tag_status": "ready", "tags": tags.model_dump()},
        0.99,
        0.70,
        0.70,
    )
    assert not result["accepted"]
    assert any(item["code"] == "category_mismatch" for item in result["reasons"])


def test_synonyms_canonicalize_and_fixture_embeddings_rank_concepts():
    assert canonical("Vulpes vulpes") == "red fox"
    fox, _ = fixture_embedding("red fox Vulpes vulpes forest")
    wolf, _ = fixture_embedding("gray wolf Canis lupus forest")
    assert cosine(fox, fox) > cosine(fox, wolf)


def test_no_confident_match_when_similarity_is_below_threshold():
    result = evaluate_candidate(
        {"subject": "glacier"},
        {"tag_status": "ready", "tags": fixture_tags("red_fox_01").model_dump()},
        0.10,
        0.70,
        0.70,
    )
    assert not result["accepted"]
    assert any(item["code"] == "similarity_below_threshold" for item in result["reasons"])

