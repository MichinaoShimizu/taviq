# Target Architecture — Zero-touch Taviq

This document defines the intended end state for Taviq distribution and adoption.

## Product goal

Taviq Core is a single self-contained Go binary installed once per developer machine. Repositories contain no Taviq implementation code. In organization-managed environments, developers eventually need no manual Taviq setup.

## End-state architecture

Organization Policy → developer-machine `taviq` binary → Claude/Codex/Kiro → `taviq observe` → Git provenance → optional forge integration.

## Distribution

Target developer installation: `brew install taviq` followed by `taviq install`. Equivalent package-manager or organization-managed binary distribution is allowed.

`taviq install` is machine-level setup. It may configure Git integration, supported AI-tool integrations, and machine-level Taviq configuration. It must be reversible and preserve existing developer configuration.

## Repository state

Repositories contain no Taviq runtime implementation. Repository enablement requires at most a small declarative marker such as `.taviq.yml`. A future organization policy may make even this marker unnecessary.

Repository lifecycle remains `taviq init`, `taviq doctor`, and `taviq deinit`, but `init` ultimately writes only marker/config state.

## Git integration

The target is machine-level Git integration invoking the installed binary. Repository-local hooks are transitional. The integration records provenance only for repositories enabled by repository config or trusted organization policy; unrelated repositories remain unaffected.

## AI-tool integrations

Claude, Codex and Kiro integrations are installed once at machine level when supported. Their minimal responsibility is to call `taviq observe <tool> <mode> [model]`. Integrations never guess unavailable metadata.

## Organization rollout

Administrators distribute the same binary, organization policy, and optional forge integration using MDM, bootstrap tooling, dev images, managed workstations or equivalent fleet mechanisms.

Target developer experience: clone a repository, work with an AI tool, commit normally. Taviq records provenance automatically when policy enables that repository.

## GitHub and other forges

GitHub is not part of Taviq Core. PR aggregation and organization visibility are optional forge integrations such as reusable workflows, GitHub App, Rulesets, or equivalent GitLab/Bitbucket integrations. Commit provenance remains portable across forges.

## Privacy and governance

Organization rollout must not turn Taviq into developer surveillance. Core does not add developer productivity ranking, individual performance scores, prompt/response capture, source/diff capture, or token/cost capture in Git provenance.

## Completion criteria

- one binary provides Core
- machine-level install is reversible
- repositories contain no Taviq implementation
- repo marker/policy controls enablement
- machine-level Git integration respects enablement
- Claude/Codex/Kiro integrations call the global binary
- binary-only doctor verifies installation
- organization policy can enable repositories without developer setup
- GitHub Actions remain optional
- macOS/Linux/Windows distribution is supported
- upgrade/uninstall can be centrally managed
