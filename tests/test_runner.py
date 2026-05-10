from ragtripwire.attacks import CANARY
from ragtripwire.runner import DEFAULT_TEMPLATE, _build_body, _extract_text, select_attacks


def test_build_body_replaces_query_without_mutating_template():
    template = {
        "messages": [{"role": "user", "content": "{{query}}"}],
        "metadata": {"raw": "{{query}}", "unchanged": 3},
    }

    body = _build_body(template, "What is the policy?")

    assert body["messages"][0]["content"] == "What is the policy?"
    assert body["metadata"]["raw"] == "What is the policy?"
    assert body["metadata"]["unchanged"] == 3
    assert template["messages"][0]["content"] == "{{query}}"


def test_default_template_is_openai_style():
    body = _build_body(DEFAULT_TEMPLATE, "hello")

    assert body == {"messages": [{"role": "user", "content": "hello"}], "stream": False}


def test_extract_text_handles_common_response_shapes():
    assert _extract_text({"output_text": "from responses api"}) == "from responses api"
    assert _extract_text({"completion": "from anthropic legacy"}) == "from anthropic legacy"
    assert _extract_text({"message": {"content": "from message"}}) == "from message"
    assert _extract_text({"choices": [{"message": {"content": "from chat"}}]}) == "from chat"
    assert _extract_text({"content": [{"text": "hello"}, {"text": " world"}]}) == "hello world"
    assert _extract_text({"output": [{"content": [{"text": "from "}, {"text": "output"}]}]}) == "from output"
    assert _extract_text("plain text") == "plain text"


def test_select_attacks_rejects_unknown_ids():
    selected = select_attacks(["direct-instruction-override"])

    assert [attack.id for attack in selected] == ["direct-instruction-override"]

    try:
        select_attacks(["direct-instruction-override", "missing"])
    except ValueError as exc:
        assert "missing" in str(exc)
    else:
        raise AssertionError("unknown attack ids should raise ValueError")


def test_extract_text_preserves_canary_detection_surface():
    response_text = _extract_text({"choices": [{"message": {"content": f"leaked {CANARY}"}}]})

    assert CANARY in response_text
