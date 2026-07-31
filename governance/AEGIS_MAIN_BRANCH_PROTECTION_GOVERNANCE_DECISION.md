# AEGIS Main-Branch Protection Governance Decision

**Governance decision:** APPROVED — STAGED MAIN-INTEGRITY RULESET POLICY
**Date recorded:** 2026-07-31
**Decision authority:** Product Owner / Founder
**Governance owner:** Documentation & Governance
**Implementation owner:** Infrastructure Engineer, under separate bounded implementation authority only
**Repository:** `https://github.com/nosferatu3333/aegis-platform.git`
**Canonical branch:** `refs/heads/main`
**Settings changed by this decision:** NONE
**WO-004 status:** NOT ACTIVATED

---

## Purpose

This decision establishes the canonical staged policy for protecting AEGIS remote `main`. It converts the previously recorded unprotected-main risk into an approved governance direction while preserving a separate implementation boundary.

The policy begins with a minimal ruleset in `Evaluate` mode. It records force-push and deletion protections for observation without prematurely imposing pull-request, reviewer, status-check, or other controls that the current repository and team model cannot yet support reliably.

This document is policy authority. It is not a GitHub settings mutation, standing push authority, release authorization, or Infrastructure implementation assignment.

## Canonical Integration Identity

The canonical integration identity is:

```text
EXACT COMMIT SHA
```

Branches, tags, worktree state, abbreviated names, mutable aliases, and inferred ancestry are not sufficient identities for an authorized integration or publication target.

The current canonical project commit remains:

```text
f727d9f9f2b82b55f79e31008bb79b71477fbc84
```

Current exact-SHA publication was authorized through a one-time explicit governance record. That event does not establish standing direct-push authority.

## Approved Ruleset Policy

| Control | Canonical value |
|---|---|
| Ruleset name | `AEGIS main integrity` |
| Ruleset target | `refs/heads/main` |
| Exclusions | **NONE** |
| Initial enforcement | **EVALUATE** |
| Block force pushes | **ENABLED** |
| Restrict deletion | **ENABLED** |
| Bypass actors | **NONE APPROVED** |

The ruleset must target only `refs/heads/main`. It must not target tags, other branches, repository-wide patterns, or additional references.

`Evaluate` is the only authorized initial enforcement mode. Transition to `Active` is not authorized by this decision.

## Controls Not Initially Enabled

The initial ruleset must not enable:

```text
Required pull requests
Required approvals
Required status checks
Required branch updates
CODEOWNERS approval
Conversation resolution
Signed commits
Linear history
Required deployments
Merge queue
Tag protection
Direct-update restriction
```

No omitted control may be inferred, defaulted into authority, or enabled for convenience during implementation.

## Direct-Update and Bypass Policy

No permanent direct-push bypass is approved.

No permanent force-push bypass is approved.

Direct update is not initially restricted by the GitHub ruleset, but governance continues to require one-time explicit authorization tied to an exact commit SHA. The absence of a platform-enforced direct-update restriction is not standing permission to update `main`.

Every future direct publication, if any, requires a separately approved, exact-object, bounded authorization with identity, ancestry, validation, remote-state, and preservation gates.

## Emergency Suspension Policy

Emergency response requires explicit, incident-specific authorization.

If the ruleset is later `Active`, an authorized emergency suspension may change its enforcement temporarily to `Evaluate` or `Disabled` only. The ruleset must not be deleted.

Emergency suspension:

- Does not authorize history rewrite.
- Does not authorize force push.
- Does not create a standing bypass.
- Does not authorize deletion of the ruleset.
- Must identify the incident, accountable owner, reason, duration, affected operation, and recovery conditions.
- Must preserve before-and-after settings evidence.
- Requires separately authorized restoration to the approved enforcement state after the emergency condition ends.

Because initial enforcement is `Evaluate`, no emergency transition is presently required or authorized.

## Personal-Repository Policy

The current personal-account repository is acceptable for the present phase.

Organization migration is deferred until one or more of the following becomes necessary:

- Persistent maintainers.
- Teams.
- Role-based repository access.
- Organization-level policies or controls.
- Durable separation between personal identity and platform ownership.

Deferral is not a permanent rejection of organization ownership. It is a phase-appropriate decision subject to review when the operating model changes.

## Deferred Full Enforcement

Full pull-request, reviewer, CODEOWNERS, and required-check enforcement remains deferred until all of the following are true:

1. The validation workflow exists on `main`.
2. Successful pull-request and `main` checks exist.
3. Stable check names are verified.
4. Independent reviewers are available.
5. GitHub identities or checks credibly represent the AEGIS engineering roles.
6. Permitted merge methods are verified.
7. A pull-request-compatible integration policy is approved.

Meeting these prerequisites does not activate the controls automatically. Any expansion or transition to `Active` requires a separate governance decision and bounded Infrastructure implementation authorization.

## Infrastructure Implementation Boundary

Infrastructure Engineering is the next eligible implementation role, but it may act only under a separate bounded implementation assignment.

That assignment may authorize creation of exactly one ruleset with:

```text
Name: AEGIS main integrity
Target: refs/heads/main
Exclusions: NONE
Enforcement: EVALUATE
Block force pushes: ENABLED
Restrict deletion: ENABLED
All other rules: DISABLED
Bypass actors: NONE
```

The bounded assignment must require read-only preflight verification of:

- Exact repository and owner identity.
- Exact current `main` identity.
- Existing branch-protection and ruleset state.
- GitHub plan and API capability for `Evaluate` enforcement.
- Authentication identity and administrative authority.
- Absence of a conflicting ruleset name or target.
- Exact proposed ruleset payload and its default behaviors.

Any ambiguity, unsupported capability, conflicting existing rule, or unavoidable additional setting is a stop condition requiring governance review.

## Explicit Non-Authority

This decision does not authorize:

- Creating or changing the ruleset without the separate bounded assignment.
- Transitioning the ruleset to `Active`.
- Enabling any deferred control.
- Adding bypass actors.
- Direct push, force push, merge, tag publication, or remote-reference modification.
- Branch, tag, worktree, or ruleset deletion.
- History rewrite.
- Release publication or deployment.
- Organization migration.
- WO-004 activation.
- Further product or Infrastructure engineering beyond the exact future assignment.

## Required Implementation Report

After separately authorized implementation, Infrastructure Engineering must return an **AEGIS Main-Branch Protection Ruleset Implementation Report** containing:

- Governing implementation authorization.
- Repository, owner, remote, and authenticated actor identities.
- Before-state branch-protection and ruleset inventory.
- Exact ruleset ID, name, target, exclusions, and enforcement mode.
- Exact enabled and disabled rule inventory.
- Bypass-actor inventory.
- API request or equivalent settings procedure used.
- Complete response and independently read-back configuration.
- Evidence that enforcement is `Evaluate`, not `Active`.
- Evidence that only force-push blocking and deletion restriction are enabled.
- Evidence that no tag, branch, commit, release, or unrelated repository setting changed.
- Any limitations, discrepancies, or follow-up risk.
- Handoff to Documentation & Governance for implementation disposition.

```text
Governance decision: APPROVED — STAGED MAIN-INTEGRITY RULESET POLICY
Canonical integration identity: EXACT COMMIT SHA
Ruleset name: AEGIS main integrity
Ruleset target: refs/heads/main
Initial enforcement: EVALUATE
Force-push blocking: ENABLED
Deletion restriction: ENABLED
Required PR: DISABLED
Required approvals: DISABLED
Required status checks: DISABLED
Standing direct-push bypass: NONE
Emergency suspension policy: EXPLICIT AUTHORIZATION; TEMPORARY ACTIVE-TO-EVALUATE OR DISABLED; NEVER DELETE RULESET
Personal repository retained: YES — CURRENT PHASE
Organization migration: DEFERRED UNTIL OPERATING-MODEL TRIGGERS REQUIRE IT
WO-004 activated: NO
Settings changed by Governance: NO
Next eligible owner: INFRASTRUCTURE ENGINEER
Required next authorization: SEPARATE BOUNDED RULESET IMPLEMENTATION ASSIGNMENT
Required next report: AEGIS MAIN-BRANCH PROTECTION RULESET IMPLEMENTATION REPORT
```
