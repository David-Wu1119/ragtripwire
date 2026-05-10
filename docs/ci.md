# CI Integration

RAGTripwire is designed to fail builds when a RAG endpoint starts obeying seeded prompt-injection documents.

## Minimal Workflow

```yaml
name: ragtripwire
on: [pull_request]
jobs:
  injection-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: python -m pip install ragtripwire
      - run: |
          ragtripwire eval \
            --endpoint "${{ secrets.STAGING_ENDPOINT }}" \
            --header "Authorization: Bearer ${{ secrets.STAGING_TOKEN }}" \
            --out ragtripwire-report.json
      - uses: actions/upload-artifact@v4
        if: always()
        with:
          name: ragtripwire-report
          path: ragtripwire-report.json
```

Exit codes:

- `0`: all attacks resisted
- `1`: medium or low severity injection succeeded, or at least one attack errored
- `2`: high severity injection succeeded

Use a staging endpoint with the RAG index rebuilt from fixtures planted by `ragtripwire attack`.
