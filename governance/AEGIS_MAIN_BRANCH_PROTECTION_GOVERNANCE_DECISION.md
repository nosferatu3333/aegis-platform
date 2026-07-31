# AEGIS Main-Branch Protection Governance Decision

**Governance decision:** APPROVED — MINIMAL ACTIVE MAIN-INTEGRITY RULESET POLICY
**Date recorded:** 2026-07-31
**Decision authority:** Product Owner / Founder
**Governance owner:** Documentation & Governance
**Implementation owner:** Infrastructure Engineer, under separate bounded implementation authority only
**Repository:** `https://github.com/nosferatu3333/aegis-platform.git`
**Canonical branch:** `refs/heads/main`
**Original policy commit:** `d6beb6422a45de8036f19ede375eab3295e4bcb9`
**Current amendment:** [`AEGIS Main-Branch Protection Governance Amendment — Minimal Active Enforcement`](AEGIS_MAIN_BRANCH_PROTECTION_ACTIVE_ENFORCEMENT_AMENDMENT.md)
**Settings changed by Governance:** NONE
**WO-004 status:** NOT ACTIVATED

---

## Purpose

This decision establishes the canonical policy for protecting AEGIS remote `main`. It converts the previously recorded unprotected-main risk into an approved governance direction while preserving a separate Infrastructure implementation boundary.

The original policy selected a minimal ruleset in `Evaluate` mode. GitHub rejected that configuration atomically because `Evaluate` enforcement is unavailable on the current plan. The Product Owner / Founder rejected an Enterprise upgrade as disproportionate and amended only the enforcement mode to `Active`. The authorized rules remain limited to deletion restriction and non-fast-forward blocking.

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
| Enforcement | **ACTIVE** |
| Block force pushes / non-fast-forward updates | **ENABLED** |
| Restrict deletion | **ENABLED** |
| Bypass actors | **NONE** |

The ruleset must target only `refs/heads/main`. It must not target tags, other branches, repository-wide patterns, or additional references.

`Active` is the authorized enforcement mode because the current GitHub plan does not support `Evaluate`. No other policy control changed.

## Controls Not Enabled

The ruleset must not enable:

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

Direct update is not restricted by this minimal GitHub ruleset, but governance continues to require one-time explicit authorization tied to an exact commit SHA. The absence of a platform-enforced direct-update restriction is not standing permission to update `main`.

The two active rules protect only against deletion and non-fast-forward updates. They do not prohibit an otherwise authorized strict fast-forward publication.

Every future direct publication, if any, requires a separately approved, exact-object, bounded authorization with identity, ancestry, validation, remote-state, and preservation gates.

## Evaluate-Mode Capability Record

Infrastructure attempted the exact previously authorized `Evaluate`-mode creation. GitHub rejected the request atomically with HTTP 422 and reported that `Evaluate` enforcement requires an Enterprise plan.

The failed request created no ruleset and changed no setting, Git reference, file, permission, or repository state. The failure is a platform-plan capability limit, not an implementation defect.

The Product Owner / Founder rejected a GitHub Enterprise upgrade as disproportionate to the present requirement. Minimal `Active` enforcement provides the approved destructive-history protections without adding pull-request, CI, reviewer, merge, or direct-update requirements.

## Compensating Controls

Because `Evaluate` is unavailable, the separately authorized implementation must require all of the following:

1. Immediately verify the repository, authenticated actor, current ruleset inventory, `main`, its tree, and remote-reference inventory.
2. Capture the exact authenticated request payload before submission.
3. Atomically create exactly one ruleset.
4. Immediately perform a complete read-back of the resulting ruleset.
5. Verify that deletion restriction and non-fast-forward blocking are the only rules present.
6. Verify that no bypass actor or additional rule exists.
7. Verify that only `refs/heads/main` is targeted and that exclusions are empty.
8. Verify that `main`, its tree, and every remote reference remain unchanged.
9. Confirm that no push, destructive or test push, repository-file mutation, permission change, or other setting change occurred.
10. Stop and escalate without corrective mutation if any identity, payload, response, read-back, or preservation check differs from the authorization.

Protection must not be simulated or tested by attempting a destructive or non-fast-forward push.

## Emergency Suspension Policy

Emergency response requires explicit, incident-specific authorization.

An authorized emergency suspension may change enforcement temporarily from `Active` to `Disabled` only. The ruleset must remain present and must not be deleted.

Emergency suspension:

- Does not authorize history rewrite.
- Does not authorize force push.
- Does not create a standing bypass.
- Does not authorize deletion or replacement of the ruleset.
- Must preserve `main` and all references.
- Must identify the incident, accountable owner, reason, duration, affected operation, and recovery conditions.
- Must preserve before-and-after settings evidence.
- Must restore the recorded configuration after the incident under explicit recovery authority.

No automatic suspension or settings rollback is authorized.

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

Meeting these prerequisites does not activate any additional control automatically. Any expansion requires a separate governance decision and bounded Infrastructure implementation authorization.

## Infrastructure Implementation Boundary

Infrastructure Engineering is the next eligible implementation role, but it may act only under a separate bounded implementation assignment.

That assignment may authorize creation of exactly one ruleset with:

```text
Name: AEGIS main integrity
Target: refs/heads/main
Exclusions: NONE
Enforcement: ACTIVE
Block force pushes / non-fast-forward updates: ENABLED
Restrict deletion: ENABLED
All other rules: ABSENT
Bypass actors: NONE
```

The bounded assignment must require all compensating controls in this decision. Any ambiguity, unsupported capability, conflicting existing rule, unexpected default, additional setting, identity mismatch, or preservation failure is a stop condition requiring governance review.

## Explicit Non-Authority

This decision does not authorize:

- Creating or changing the ruleset without the separate bounded assignment.
- A GitHub plan upgrade.
- Classic branch protection.
- Enabling any deferred or additional control.
- Adding bypass actors.
- Direct push, force push, merge, tag publication, or remote-reference modification.
- Branch, tag, worktree, or ruleset deletion.
- Repository-file, permission, or collaborator changes.
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
- Exact authenticated request payload.
- Exact ruleset ID, name, target, exclusions, and `Active` enforcement mode.
- Exact enabled-rule inventory showing only deletion restriction and non-fast-forward blocking.
- Exact absent-rule and bypass-actor inventory.
- Complete API response and independently read-back configuration.
- Before-and-after `main` commit, tree, and complete remote-reference evidence.
- Confirmation that exactly one ruleset was created.
- Confirmation that no push, destructive test, repository-file mutation, permission change, release, or unrelated setting change occurred.
- Any limitations, discrepancies, or follow-up risk.
- Handoff to Documentation & Governance for implementation disposition.

```text
Governance decision: APPROVED — MINIMAL ACTIVE MAIN-INTEGRITY RULESET POLICY
Canonical integration identity: EXACT COMMIT SHA
Ruleset name: AEGIS main integrity
Ruleset target: refs/heads/main
Initial enforcement: ACTIVE
Force-push blocking: ENABLED
Deletion restriction: ENABLED
Required PR: DISABLED
Required approvals: DISABLED
Required status checks: DISABLED
Standing direct-push bypass: NONE
Emergency suspension policy: SEPARATE EXPLICIT AUTHORIZATION; TEMPORARY ACTIVE-TO-DISABLED ONLY; NEVER DELETE RULESET
Personal repository retained: YES — CURRENT PHASE
Organization migration: DEFERRED UNTIL OPERATING-MODEL TRIGGERS REQUIRE IT
WO-004 activated: NO
Settings changed by Governance: NO
Next eligible owner: INFRASTRUCTURE ENGINEER
Required next authorization: SEPARATE BOUNDED ACTIVE-RULESET IMPLEMENTATION ASSIGNMENT
Required next report: AEGIS MAIN-BRANCH PROTECTION RULESET IMPLEMENTATION REPORT
```
