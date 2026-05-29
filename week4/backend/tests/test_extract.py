from backend.app.services.extract import extract_action_items, extract_tags


def test_extract_action_items():
    text = """
    This is a note
    - TODO: write tests
    - Ship it!
    Not actionable
    """.strip()
    items = extract_action_items(text)
    assert "TODO: write tests" in items
    assert "Ship it!" in items


# ---------------------------------------------------------------------------
# extract_tags — pure function tests
# ---------------------------------------------------------------------------


def test_extract_tags_returns_names_without_hash():
    # Hashtags must be returned without the leading '#'.
    result = extract_tags("Do this #urgent and #followup")
    assert result == ["urgent", "followup"]


def test_extract_tags_deduplicates_preserving_first_seen_order():
    # Duplicate tags are collapsed; the first occurrence determines position.
    result = extract_tags("#a #b #a")
    assert result == ["a", "b"]


def test_extract_tags_strips_trailing_punctuation():
    # Punctuation immediately after a tag word is not part of the tag.
    result = extract_tags("Mark as #done.")
    assert result == ["done"]


def test_extract_tags_empty_text_returns_empty_list():
    result = extract_tags("")
    assert result == []


def test_extract_tags_no_tags_returns_empty_list():
    result = extract_tags("No hashtags here at all")
    assert result == []


def test_extract_tags_preserves_case():
    # Tag names are returned exactly as written (case is preserved).
    result = extract_tags("#Urgent #FOLLOWUP #mixedCase")
    assert result == ["Urgent", "FOLLOWUP", "mixedCase"]


def test_extract_tags_supports_digits_and_underscores():
    # Tags may contain digits and underscores per the word-character rule.
    result = extract_tags("#tag_1 #item2 #under_score")
    assert result == ["tag_1", "item2", "under_score"]
