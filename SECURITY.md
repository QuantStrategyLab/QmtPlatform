# Security Policy

## Reporting a Vulnerability

If you find a security issue in `QmtPlatform`, please report it privately to `@Pigbibi` instead of opening a public issue. Include what you found, the affected file or endpoint, and steps to reproduce if possible.

## Secret and Credential Exposure

This repository must never contain real broker credentials, account identifiers, API tokens, or other secrets in source, configuration samples, test fixtures, or workflow logs. `.env.example` and the fixtures under `data/` hold placeholder values only.

If you discover a committed secret or a real account identifier, report it the same way as a vulnerability (do not open a public issue describing it) so it can be rotated and removed.

## Scope Notes

- Current scope is **offline dry-run only**. `QmtPlatform` evaluates strategy targets and previews orders; it does not hold a live or paper broker connection, and any non-dry-run order request is rejected as `blocked`, never reported as `submitted`.
- The offline `--paper-admission` gate (see `README.md`) is a local configuration check, not a miniQMT/QMT paper account connection — it does not call a QMT SDK/provider or read credentials.
- Despite the dry-run-only scope, the code paths here still model order construction, strategy profile selection, and QMT/miniQMT integration points, so changes to those paths are treated as security-relevant and should be reviewed with that in mind.
- The scheduled `Runtime Target Lifecycle` workflow runs against a disabled target with no broker runtime configured; it does not expose or require live credentials.
