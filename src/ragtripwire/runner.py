"""Endpoint runner — sends each attack query to the user's RAG endpoint
and records the response so the report layer can grade pass/fail."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import httpx

from .attacks import ATTACKS, Attack


@dataclass
class AttackResult:
    attack_id: str
    severity: str
    title: str
    query: str
    response_text: str
    triggered_canaries: List[str] = field(default_factory=list)
    passed: bool = True  # True = model resisted, False = injection succeeded
    latency_ms: float = 0.0
    error: Optional[str] = None
    raw_response: Optional[Any] = None


def _extract_text(payload: Any) -> str:
    """Best-effort extraction of the assistant text from common chat APIs."""
    if isinstance(payload, str):
        return payload
    if not isinstance(payload, dict):
        return json.dumps(payload, default=str)
    # OpenAI / Anthropic chat completions
    if "choices" in payload:
        try:
            choice = payload["choices"][0]
            msg = choice.get("message") or {}
            content = msg.get("content")
            if isinstance(content, str):
                return content
            if isinstance(content, list):
                # Anthropic content blocks
                return "".join(
                    part.get("text", "") for part in content if isinstance(part, dict)
                )
        except (IndexError, KeyError, TypeError):
            pass
    if "content" in payload:
        c = payload["content"]
        if isinstance(c, str):
            return c
        if isinstance(c, list):
            return "".join(
                part.get("text", "") for part in c if isinstance(part, dict)
            )
    for key in ("response", "answer", "output", "text", "result"):
        v = payload.get(key)
        if isinstance(v, str):
            return v
    return json.dumps(payload, default=str)


def _build_body(template: Dict[str, Any], query: str) -> Dict[str, Any]:
    """Substitute {{query}} placeholders in the request template."""

    def walk(node: Any) -> Any:
        if isinstance(node, str):
            return node.replace("{{query}}", query)
        if isinstance(node, list):
            return [walk(x) for x in node]
        if isinstance(node, dict):
            return {k: walk(v) for k, v in node.items()}
        return node

    return walk(template)


DEFAULT_TEMPLATE: Dict[str, Any] = {
    "messages": [{"role": "user", "content": "{{query}}"}],
    "stream": False,
}


def evaluate(
    endpoint: str,
    *,
    headers: Optional[Dict[str, str]] = None,
    body_template: Optional[Dict[str, Any]] = None,
    only: Optional[List[str]] = None,
    timeout: float = 60.0,
) -> List[AttackResult]:
    template = body_template if body_template is not None else DEFAULT_TEMPLATE
    selected: List[Attack] = (
        [a for a in ATTACKS if a.id in set(only)] if only else list(ATTACKS)
    )

    results: List[AttackResult] = []
    with httpx.Client(timeout=timeout) as client:
        for attack in selected:
            body = _build_body(template, attack.query)
            t0 = time.perf_counter()
            try:
                resp = client.post(endpoint, headers=headers or {}, json=body)
                latency_ms = (time.perf_counter() - t0) * 1000
                resp.raise_for_status()
                try:
                    payload = resp.json()
                except json.JSONDecodeError:
                    payload = resp.text
                text = _extract_text(payload)
                triggered = [c for c in attack.canaries if c in text]
                results.append(
                    AttackResult(
                        attack_id=attack.id,
                        severity=attack.severity,
                        title=attack.title,
                        query=attack.query,
                        response_text=text,
                        triggered_canaries=triggered,
                        passed=len(triggered) == 0,
                        latency_ms=latency_ms,
                        raw_response=payload if isinstance(payload, dict) else None,
                    )
                )
            except Exception as exc:  # noqa: BLE001
                latency_ms = (time.perf_counter() - t0) * 1000
                results.append(
                    AttackResult(
                        attack_id=attack.id,
                        severity=attack.severity,
                        title=attack.title,
                        query=attack.query,
                        response_text="",
                        triggered_canaries=[],
                        passed=False,
                        latency_ms=latency_ms,
                        error=f"{type(exc).__name__}: {exc}",
                    )
                )
    return results
