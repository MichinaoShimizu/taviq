> **Historical / experimental.** This document describes an earlier Collector/Analytics design and is not the current Taviq Basic architecture. Current Basic is zero-server and records minimal provenance through Git trailers and GitHub Actions. See [README](../README.md), [Basic](basic.md), and [Roadmap](ROADMAP.md).

# Self-hosted Relay MVP

The relay is a narrow transport service for minimal provenance envelopes.

## Security boundary

- Bearer token is required.
- Default bind address is localhost.
- Maximum request body is 64 KiB.
- Only the envelope allow-list is accepted.
- Raw events and unexpected fields are rejected.
- Prompt, response, source, diff, usage, cost and identity are not valid relay fields.

## Run

```bash
export TAVIQ_RELAY_TOKEN='replace-me'
python3 src/taviq_relay.py --host 127.0.0.1 --port 8787
```

## API

POST `/v1/envelopes` stores one minimal envelope.

GET `/v1/envelopes?repository=<repo>&commit_sha=<sha>` returns envelopes correlated to that commit.

This is an MVP transport, not an internet-facing production service. TLS termination, token rotation, organization scoping, rate limiting, audit logging and durable database storage are required before exposing it outside a trusted environment.
