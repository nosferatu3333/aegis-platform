# WO-MVP-006 — Bounded Planning Adapter

Platform 0.2.0 accepts the canonical `CapabilitySelection` emitted by AEGIS
OPS and converts a normalized workflow into the canonical Core `BoundedPlan`.
The boundary is non-executing and preserves authority requirements, consequence
classification, completion criteria, expected evidence, limitations, and stop
conditions.

Validation baseline: 172 tests. Validation after implementation: 176 tests.
