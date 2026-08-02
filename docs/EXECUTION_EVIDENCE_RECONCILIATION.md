# Execution Evidence and Result Reconciliation

WO-MVP-008 introduces the boundary that converts a terminal Platform execution
receipt into canonical Core evidence, per-step execution results, a result
record, and a complete cognitive trace.

The reconciler records observed execution facts. It does not infer real-world
success from simulation, erase failed or skipped steps, or manufacture missing
lineage. A receipt must be terminal and carry canonical request and plan IDs.

Canonical flow:

`ExecutionReceipt -> ExecutionResult[] -> EvidenceRecord[] -> ResultRecord -> CognitiveTrace`

Each evidence record contains a deterministic SHA-256 digest of the serialized
receipt or step, provenance, verification attribution, freshness, access, and
explicit simulation limitations. Complete results require evidence. Failed and
cancelled results preserve limitations and cannot be upgraded to completion.
