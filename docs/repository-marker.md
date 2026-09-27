# Repository Enablement Marker

Taviq repository enablement is declarative.

## Marker

The initial marker is `.taviq.yml`. v1 intentionally supports only the minimum field:

    version: 1

Presence of a valid marker enables local Taviq provenance unless a future trusted organization policy defines otherwise.

## Rules

- marker contains configuration, never implementation code
- unknown marker versions fail closed
- missing marker means repository is not locally enabled
- `taviq init` creates the marker idempotently
- `taviq deinit` removes only the marker and transient Taviq runtime state
- machine-level integrations must check enablement before recording provenance

Organization policy and marker precedence will be defined before organization-policy rollout.