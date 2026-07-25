# Platform Stabilization Phase 2.5

This stabilization repairs Platform's executable boundary while preserving its
role as the future product and operational control plane.

## Recovered

The current stabilization baseline was missing `evaluation`, `execution`,
`learning`, `memory`, and `planning`. These directories were restored from the
previous founder-supplied Platform worktree. All files common to both snapshots
were byte-identical before recovery.

## Corrected

- Capability input is normalized explicitly instead of iterating display-name
  strings character by character.
- Agents with zero capability matches are excluded from ranking.
- Unknown capabilities fail rather than falling through to the first agent.
- Agent output is structured and marked as simulated.
- Collaboration teams can execute their simulated members.
- Decision scoring identifies itself as a string-length heuristic.
- Generated plan tasks remain explicitly unexecuted and the plan is partial.
- Fixed evaluation values are labeled heuristic and unmeasured.
- Single-run pattern detection is not promoted as validated learning.
- Experience storage is no longer duplicated by two memory managers.
- Knowledge imports no longer execute a cognitive cycle as a side effect.
- `.gitignore` contains ignore rules rather than project documentation.
- Smoke scripts are executable `unittest` tests with assertions.

## Intentionally unchanged

- Platform does not execute every decomposed Plan task.
- Platform does not enforce governance or grant capabilities.
- Platform does not own canonical cognitive contracts or algorithms.
- No Platform result should be treated as a governed `CognitiveResult`.
- The stabilized behavior remains a simulation and migration reference.
