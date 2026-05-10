# Threat Model

RAGTripwire tests whether a RAG endpoint follows malicious instructions planted in retrieved documents.

## In Scope

- Direct prompt-injection documents
- Hidden HTML comment payloads
- Zero-width Unicode payloads
- Markdown link exfiltration prompts
- Tool-use manipulation prompts detectable through returned text
- Persona hijack prompts
- Citation laundering prompts
- Deterministic canary-based pass/fail grading

## Out of Scope

- Full proof that a RAG app is safe
- Attacks that require inspecting hidden tool-call telemetry unless the endpoint returns that telemetry
- Browser-side image fetching behavior outside endpoint text
- Endpoint authentication, authorization, or network security
- Model-judged qualitative scoring

## Failure Modes

- A model can comply with an attack without emitting the configured canary.
- An endpoint can filter canaries while still leaking other sensitive content.
- A retrieval system can fail to retrieve planted attack documents, producing a false sense of safety.
- Response templates can hide model output from RAGTripwire's parser.

Treat RAGTripwire as a regression test suite, not a certification.
