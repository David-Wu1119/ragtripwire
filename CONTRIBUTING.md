# Contributing

RAGTripwire should stay deterministic, CI-friendly, and explainable.

## Local Setup

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
pytest
python -m build
```

## Pull Request Expectations

- Add tests for new attacks, response parsers, and report behavior.
- Every bundled attack must have a stable ID, severity, query, document, description, and concrete canary.
- Do not replace deterministic canary checks with model-judged scoring in the default path.
- Document new CLI behavior in `README.md`.
- Keep reports free of raw endpoint payloads that may contain secrets.

## Release Checklist

```bash
pytest
python -m build
ragtripwire --help
```
