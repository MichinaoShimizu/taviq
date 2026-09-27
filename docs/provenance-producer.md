# Provenance Producer / Outbox

The collector and network transport are separate.

1. Collector/session correlation builds a minimal envelope.
2. Producer queues it in the local Taviq outbox.
3. A transport exports envelopes to an explicitly configured destination.
4. Successful delivery/acknowledgement may later remove the local envelope according to retention policy.

Default local path:

```text
~/.taviq/outbox/<session-ref>.json
```

The MVP implements a directory transport only. This deliberately avoids silently sending engineering metadata over the network before a Self-hosted or Taviq Cloud endpoint, authentication model, consent flow, and deletion semantics are defined.

A future transport interface can add:

- GitHub artifact producer
- self-hosted HTTPS endpoint
- Taviq Cloud HTTPS endpoint

without changing the collector's privacy boundary.
