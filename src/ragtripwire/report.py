"""Pretty terminal + JSON reporting for evaluation runs."""

from __future__ import annotations

import json
from dataclasses import asdict
from typing import Dict, List

from rich.console import Console
from rich.table import Table

from .runner import AttackResult


SEV_STYLE = {
    "high": "bold red",
    "medium": "yellow",
    "low": "cyan",
}


def print_report(results: List[AttackResult]) -> int:
    console = Console()
    table = Table(title="RAGTripwire — attack results", show_lines=False)
    table.add_column("Attack")
    table.add_column("Severity")
    table.add_column("Result")
    table.add_column("Triggered")
    table.add_column("Latency")

    failed_high = 0
    failed_any = 0

    for r in results:
        sev_style = SEV_STYLE.get(r.severity, "white")
        if r.error:
            verdict = f"[bold magenta]ERROR[/bold magenta]"
        elif r.passed:
            verdict = "[green]✓ resisted[/green]"
        else:
            verdict = "[bold red]✗ injected[/bold red]"
            failed_any += 1
            if r.severity == "high":
                failed_high += 1
        triggered = (
            ", ".join(c[:24] + ("…" if len(c) > 24 else "") for c in r.triggered_canaries)
            or "—"
        )
        table.add_row(
            r.attack_id,
            f"[{sev_style}]{r.severity}[/{sev_style}]",
            verdict,
            triggered,
            f"{r.latency_ms:.0f}ms",
        )

    console.print(table)

    total = len(results)
    resisted = sum(1 for r in results if r.passed and not r.error)
    errors = sum(1 for r in results if r.error)

    summary = f"\n{resisted}/{total} attacks resisted"
    if errors:
        summary += f"  ·  {errors} errored"
    console.print(summary)

    if failed_high:
        console.print(
            f"[bold red]✗ {failed_high} HIGH-severity injection(s) succeeded.[/bold red]"
        )
        return 2
    if failed_any:
        console.print(
            f"[yellow]⚠ {failed_any} injection(s) succeeded.[/yellow]"
        )
        return 1
    if errors:
        console.print("[yellow]⚠ Some attacks errored — review above.[/yellow]")
        return 1
    console.print("[green]✓ Endpoint resisted every attack in the suite.[/green]")
    return 0


def write_json(results: List[AttackResult], path: str) -> None:
    payload: Dict = {
        "results": [
            {
                **asdict(r),
                # raw_response can be huge; truncate
                "raw_response": None,
                "response_text": r.response_text[:4000],
            }
            for r in results
        ],
        "summary": {
            "total": len(results),
            "resisted": sum(1 for r in results if r.passed and not r.error),
            "injected": sum(1 for r in results if not r.passed and not r.error),
            "errored": sum(1 for r in results if r.error),
        },
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
