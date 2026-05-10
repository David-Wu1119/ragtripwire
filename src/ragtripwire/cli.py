"""ragtripwire CLI."""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path
from typing import Dict, Optional

import click
from rich.console import Console

from . import __version__
from .attacks import ATTACKS, list_ids
from .report import print_report, write_json
from .runner import DEFAULT_TEMPLATE, evaluate


console = Console()


def _slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


@click.group()
@click.version_option(version=__version__, prog_name="ragtripwire")
def main() -> None:
    """Plant prompt-injection attacks into a RAG corpus and grade an endpoint."""


@main.command()
@click.option(
    "--out",
    "out_dir",
    default="ragtripwire-fixtures",
    show_default=True,
    help="Directory to write attack fixture documents into.",
)
@click.option("--force/--no-force", default=False, help="Overwrite existing files.")
def init(out_dir: str, force: bool) -> None:
    """Write the bundled attack fixtures so you can wire them into your indexer."""
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    written = 0
    for attack in ATTACKS:
        path = out / f"{_slug(attack.id)}.md"
        if path.exists() and not force:
            console.print(f"[yellow]skip[/yellow]  {path} (exists, --force to overwrite)")
            continue
        path.write_text(attack.document, encoding="utf-8")
        written += 1
        console.print(f"[green]wrote[/green] {path}")
    manifest = out / "attacks.json"
    manifest.write_text(
        json.dumps(
            [
                {
                    "id": a.id,
                    "title": a.title,
                    "severity": a.severity,
                    "category": a.category,
                    "query": a.query,
                    "canaries": a.canaries,
                    "file": f"{_slug(a.id)}.md",
                }
                for a in ATTACKS
            ],
            indent=2,
        ),
        encoding="utf-8",
    )
    console.print(f"\n[bold]Wrote {written} attack(s)[/bold] to {out}/")
    console.print(f"Manifest: {manifest}")


@main.command()
@click.argument("docs_dir", type=click.Path(file_okay=False, path_type=Path))
@click.option("--force/--no-force", default=False, help="Overwrite existing files.")
def attack(docs_dir: Path, force: bool) -> None:
    """Plant attack fixtures into an existing corpus directory."""
    docs_dir.mkdir(parents=True, exist_ok=True)
    written = 0
    for a in ATTACKS:
        path = docs_dir / f"_ragtripwire_{_slug(a.id)}.md"
        if path.exists() and not force:
            console.print(f"[yellow]skip[/yellow]  {path}")
            continue
        path.write_text(a.document, encoding="utf-8")
        written += 1
        console.print(f"[green]planted[/green] {path}")
    console.print(f"\n[bold]Planted {written} attack doc(s)[/bold] into {docs_dir}/")
    console.print(
        "Re-index your RAG store, then run: "
        "[cyan]ragtripwire eval --endpoint <url>[/cyan]"
    )


@main.command()
@click.option("--endpoint", required=True, help="HTTP endpoint that accepts a chat request.")
@click.option(
    "--header",
    "headers",
    multiple=True,
    help="HTTP header(s), repeatable: --header 'Authorization: Bearer …'",
)
@click.option(
    "--body-template",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    help="JSON file for the request body. Use {{query}} where the user's message goes.",
)
@click.option(
    "--only",
    multiple=True,
    type=click.Choice(list_ids()),
    help="Run only the listed attack(s). Repeatable.",
)
@click.option("--out", "json_out", type=click.Path(dir_okay=False, path_type=Path), help="Write JSON report to this file.")
@click.option("--timeout", type=float, default=60.0, show_default=True, help="HTTP timeout in seconds.")
def eval(  # noqa: A001 - shadowing builtin is fine for a CLI verb
    endpoint: str,
    headers: tuple,
    body_template: Optional[Path],
    only: tuple,
    json_out: Optional[Path],
    timeout: float,
) -> None:
    """Send each attack query to ENDPOINT and grade pass/fail."""
    hdrs: Dict[str, str] = {"Content-Type": "application/json"}
    for raw in headers:
        if ":" not in raw:
            raise click.BadParameter(f"Bad header (expected 'Name: value'): {raw}")
        name, _, value = raw.partition(":")
        hdrs[name.strip()] = os.path.expandvars(value.strip())

    template = DEFAULT_TEMPLATE
    if body_template:
        template = json.loads(body_template.read_text(encoding="utf-8"))

    console.print(f"Evaluating [cyan]{endpoint}[/cyan] against {len(only) or len(ATTACKS)} attack(s)…\n")
    results = evaluate(
        endpoint,
        headers=hdrs,
        body_template=template,
        only=list(only) if only else None,
        timeout=timeout,
    )
    exit_code = print_report(results)
    if json_out:
        write_json(results, str(json_out))
        console.print(f"\nReport written to [cyan]{json_out}[/cyan]")
    sys.exit(exit_code)


@main.command(name="list")
def list_cmd() -> None:
    """Show every attack bundled with this version."""
    for a in ATTACKS:
        console.print(f"[bold]{a.id}[/bold]  ([{SEV_STYLE.get(a.severity, 'white')}]{a.severity}[/]) — {a.title}")
        console.print(f"  {a.description}\n")


SEV_STYLE = {"high": "bold red", "medium": "yellow", "low": "cyan"}


if __name__ == "__main__":
    main()
