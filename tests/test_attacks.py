from ragtripwire.attacks import ATTACKS, CANARY, get_attack, list_ids

ZERO_WIDTH = dict.fromkeys(map(ord, "\u200b\u200c\u200d"), None)


def test_attack_ids_are_unique_and_stable():
    ids = list_ids()

    assert len(ids) == len(set(ids))
    assert ids == [
        "direct-instruction-override",
        "hidden-html-comment",
        "zero-width-unicode",
        "markdown-link-exfiltration",
        "tool-use-manipulation",
        "persona-hijack",
        "citation-laundering",
    ]


def test_every_attack_has_required_metadata_and_canary():
    valid_severities = {"high", "medium", "low"}

    for attack in ATTACKS:
        assert attack.id
        assert attack.title
        assert attack.query
        assert attack.document
        assert attack.description
        assert attack.severity in valid_severities
        assert attack.canaries
        normalized_document = attack.document.translate(ZERO_WIDTH)
        assert any(canary in normalized_document for canary in attack.canaries)


def test_get_attack_returns_exact_attack_or_raises():
    attack = get_attack("direct-instruction-override")

    assert attack.id == "direct-instruction-override"
    assert CANARY in attack.document

    try:
        get_attack("missing")
    except KeyError as exc:
        assert exc.args == ("missing",)
    else:
        raise AssertionError("missing attack id should raise KeyError")
