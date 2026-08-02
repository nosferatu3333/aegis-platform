# WO-MVP-020 — Live OPS Capability Integration

Platform now discovers the authoritative sibling AEGIS OPS repository through `AEGIS_OPS_PATH` or the default sibling path, loads validated capability YAML modules with the live OPS loader and registry, invokes the live OPS selector, and exposes selection source, path, score, rationale, and workflow in the existing bounded pipeline.

The integration is isolated behind `OpsCapabilitySelectorAdapter`. Missing, malformed, or empty OPS installations do not bypass governance; the hybrid selector falls back to the existing bounded internal profiles.
