# AEGIS Main-Branch Protection Governance Amendment — Minimal Active Enforcement

**Amendment decision:** APPROVED — MINIMAL ACTIVE ENFORCEMENT
**Date recorded:** 2026-07-31
**Decision authority:** Product Owner / Founder
**Governance owner:** Documentation & Governance
**Original governance decision:** `d6beb6422a45de8036f19ede375eab3295e4bcb9`
**Evaluate implementation verdict:** CAPABILITY BLOCKED — HTTP 422; NO MUTATION
**Implementation owner:** Infrastructure Engineer, under separate bounded implementation authority only
**Settings changed by Governance:** NONE
**WO-004 status:** NOT ACTIVATED

---

## Amendment Purpose

This amendment records the failed attempt to create the originally approved `Evaluate`-mode ruleset, the Product Owner / Founder's proportionality decision, and the sole policy change from `Evaluate` to `Active` enforcement.

It authorizes Infrastructure Engineering to become the implementation owner only through a separate bounded assignment. It does not create the ruleset or change any GitHub setting, repository file, permission, reference, or remote state.

## Original Governance Policy

The original governance decision established:

```text
Canonical integration identity: EXACT COMMIT SHA
Ruleset name: AEGIS main integrity
Ruleset target: refs/heads/main
Exclusions: NONE
Initial enforcement: EVALUATE
Block force pushes / non-fast-forward updates: ENABLED
Restrict deletion: ENABLED
Bypass actors: NONE
```

It excluded all pull-request, reviewer, status-check, merge, tag, direct-update, and other enforcement rules. It also required a separate bounded Infrastructure assignment and granted no standing push authority.

## Evaluate-Mode Failure Evidence

Infrastructure attempted the exact authorized `Evaluate`-mode ruleset creation. GitHub rejected the request atomically:

```text
HTTP 422
Enforcement evaluate option is not supported on this plan.
Please upgrade to Enterprise to enable it.
```

The attempt created no ruleset. No setting, Git reference, repository file, permission, or repository state changed.

The implementation verdict is **CAPABILITY BLOCKED — NO MUTATION**. This is a GitHub plan limitation, not a defect in the authorized ruleset content.

## Product Owner Decision and Proportionality

The Product Owner / Founder rejected a GitHub Enterprise upgrade as disproportionate to the present requirement and approved the same minimal ruleset directly in `Active` enforcement.

Only the enforcement value changes. The two active rules protect destructive history operations: deletion of `main` and non-fast-forward updates. They do not add pull-request, CI, reviewer, merge, deployment, signature, linear-history, tag, or direct-update requirements, and they do not prevent an otherwise authorized strict fast-forward publication.

## Exact Active Ruleset Configuration

| Control | Required value |
|---|---|
| Ruleset name | `AEGIS main integrity` |
| Target | `refs/heads/main` |
| Exclusions | **NONE** |
| Enforcement | **ACTIVE** |
| Block force pushes / non-fast-forward updates | **ENABLED** |
| Restrict deletion | **ENABLED** |
| Bypass actors | **NONE** |

The following rules must remain absent:

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

No default, inferred, adjacent, or convenience control is authorized.

## Compensating Controls

The separate bounded implementation assignment must require Infrastructure Engineering to:

1. Immediately verify the exact repository, authenticated actor, current ruleset inventory, `main`, its tree, and all remote references.
2. Capture the exact authenticated creation payload before submission.
3. Atomically create exactly one ruleset.
4. Immediately read back the complete resulting ruleset.
5. Verify that deletion restriction and non-fast-forward blocking are the only rules present.
6. Verify that no bypass actor or additional rule exists.
7. Verify that only `refs/heads/main` is targeted and exclusions are empty.
8. Verify that `main`, its tree, and all remote references remain unchanged.
9. Confirm that no push, destructive or test push, repository-file mutation, permission change, or other setting change occurred.
10. Stop and escalate without corrective mutation for any mismatch.

Infrastructure must not simulate protection by attempting a destructive or test push.

## Emergency Policy

There is no standing bypass, automatic settings rollback, or ruleset-deletion authority.

Any emergency suspension requires separate explicit authorization. Authorized recovery may temporarily change enforcement from `Active` to `Disabled`, must preserve `main`, must resolve the identified incident without history rewrite, and must restore the recorded configuration. The ruleset must not be deleted or replaced.

## Implementation Authority and Limits

Infrastructure Engineering is the next eligible owner. It may create exactly the configured `AEGIS main integrity` ruleset only after receiving a separate bounded active-ruleset implementation assignment.

This amendment does not authorize:

- A GitHub plan upgrade.
- Classic branch protection.
- Any additional rules or bypass actors.
- Repository-file changes.
- Permission or collaborator changes.
- Push, force push, or Git-reference mutation.
- A destructive or test push.
- Ruleset deletion or replacement.
- Release publication or deployment.
- WO-004 activation.

## Required Implementation Report

Infrastructure Engineering must return an **AEGIS Main-Branch Protection Ruleset Implementation Report** containing the governing authorization, exact repository and actor identity, before state, authenticated payload, atomic creation response, complete read-back, exact rules and bypass inventory, `main` and reference preservation evidence, confirmation of no other mutation, and any discrepancy or risk.

Any mismatch must be reported as a stopped implementation. No corrective expansion, alternate protection mechanism, destructive test, or retry with changed semantics is authorized.

```text
Amendment decision: APPROVED — MINIMAL ACTIVE ENFORCEMENT
Original governance decision: d6beb6422a45de8036f19ede375eab3295e4bcb9
Evaluate implementation verdict: CAPABILITY BLOCKED — HTTP 422; NO MUTATION
Enterprise upgrade: REJECTED — DISPROPORTIONATE FOR CURRENT REQUIREMENT
Ruleset name: AEGIS main integrity
Ruleset target: refs/heads/main
Enforcement: ACTIVE
Force-push blocking: ENABLED
Deletion restriction: ENABLED
Bypass actors: NONE
Additional rules: NONE
Emergency suspension authority: SEPARATE EXPLICIT AUTHORIZATION — TEMPORARY ACTIVE-TO-DISABLED ONLY; NEVER DELETE RULESET
Settings changed by Governance: NO
Push authorized: NO
WO-004 authorized: NO
Next eligible owner: INFRASTRUCTURE ENGINEER
Required next authorization: SEPARATE BOUNDED ACTIVE-RULESET IMPLEMENTATION ASSIGNMENT
Required next report: AEGIS MAIN-BRANCH PROTECTION RULESET IMPLEMENTATION REPORT
```
