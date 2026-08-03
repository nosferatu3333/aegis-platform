# Governed Runtime API v1

`POST /governed-runtime` exposes the end-to-end governed Platform pipeline as an additive API surface.

The caller must provide an explicit canonical `CapabilitySelection`. Platform does not select a capability, infer authority, create approval grants, or treat a simulated result as proof of a real-world effect.

The endpoint supports two modes:

- `execute: false` returns the canonical bounded plan and stops before authority evaluation.
- `execute: true` evaluates authority and either pauses, denies, or performs simulated execution followed by conformance validation and result reconciliation.

Approval-required selections without a matching grant remain paused. The initial API surface intentionally does not mint grants or bypass the two-stage approval lifecycle.

The dashboard includes a clearly labeled demonstration control. It creates an explicit browser-side demo selection from the visible analysis result and submits it to the strict governed endpoint. This is a demonstration adapter, not a replacement for the OPS capability-selection boundary.
