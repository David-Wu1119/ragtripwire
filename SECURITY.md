# Security Policy

RAGTripwire is security testing software. Do not publish exploit details for unfixed vulnerabilities in public issues.

## Supported Versions

During the `0.x` phase, only the latest `main` branch and latest published package are supported.

## Reporting a Vulnerability

Use GitHub Security Advisories when available. If private reporting is unavailable, open a minimal public issue asking for a disclosure channel without including exploit details.

A useful report includes:

- RAGTripwire version or commit
- Minimal reproduction
- Expected pass/fail result
- Actual pass/fail result
- Endpoint response shape, with secrets removed
- Whether the issue is false pass, false fail, crash, or report leakage

## Scope

RAGTripwire grades whether configured canaries appear in endpoint responses. It does not prove that a model is safe against every prompt-injection technique, and it does not inspect private tool telemetry unless the endpoint returns it.
