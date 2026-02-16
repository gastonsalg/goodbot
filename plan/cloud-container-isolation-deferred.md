# Deferred Cloud Container Isolation Strategy for goodbot

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This plan is intentionally deferred. It defines how to evaluate cloud container isolation for `goodbot` later, without committing implementation work now.

## Purpose / Big Picture

When this plan is eventually executed, `goodbot` will gain an explicit isolation model for cloud deployment: trusted control-plane components (channel adapters, policy, routing, scheduling) will remain outside untrusted execution sandboxes, and agent/tool execution will run in ephemeral isolated runtimes with strict filesystem, network, and identity boundaries. The immediate value of this deferred plan is decision readiness, not new runtime behavior.

Today, the expected user-visible result is only governance clarity: contributors can see exactly when to resume this work, what options must be evaluated, and what evidence is required before any implementation begins.

## Progress

- [x] (2026-02-16 10:49Z) Created a separate follow-up ExecPlan under `plan/` and marked it deferred.
- [x] (2026-02-16 10:49Z) Documented explicit trigger conditions and a not-before rule to prevent accidental scope creep.
- [x] (2026-02-16 10:49Z) Captured cloud isolation architecture options and decision criteria for future execution.
- [ ] Resume this plan only after all trigger conditions in `Validation and Acceptance` are satisfied.
- [ ] Run architecture option evaluation and produce a signed go/no-go decision.
- [ ] Implement an approved sandbox execution path behind a feature flag and validate behavior with tests and an end-to-end scenario.

## Surprises & Discoveries

- Observation: the researched upstream `nanoclaw` project (`qwibitai/nanoclaw`) demonstrates strong local isolation ideas, but includes enterprise constraints that are unsuitable as-is for this fork.
  Evidence: upstream [`src/container-runner.ts`](https://github.com/qwibitai/nanoclaw/blob/main/src/container-runner.ts) uses the Apple `container` CLI directly, and upstream [`docs/SECURITY.md`](https://github.com/qwibitai/nanoclaw/blob/main/docs/SECURITY.md) explicitly states unrestricted network access and credential exposure tradeoffs.

- Observation: this fork (`goodbot`) already has meaningful policy controls that reduce immediate pressure to implement cloud sandboxing now.
  Evidence: `nanobot/config/profile.py` enforces `enterprise_minimal` constraints, and `nanobot/config/schema.py` defaults high-risk tools to blocked.

## Decision Log

- Decision: create a dedicated deferred ExecPlan instead of adding cloud isolation implementation to the current active milestones.
  Rationale: this preserves delivery focus on the current minimum showable product while avoiding architecture churn without deployment prerequisites.
  Date/Author: 2026-02-16 / Codex

- Decision: treat this plan as design-and-gating until triggers are met; no code implementation is authorized by this document yet.
  Rationale: the user explicitly requested not to implement now, and cloud isolation cost/latency/security tradeoffs require environment decisions first.
  Date/Author: 2026-02-16 / Codex

## Outcomes & Retrospective

Current outcome (deferred planning stage): the repository now has an explicit, self-contained plan that can be resumed later without re-discovery work. No runtime behavior changed, and no production risk was introduced.

Future retrospective entries must summarize which isolation model was selected, what was rejected and why, and how observed behavior met acceptance criteria.

## Context and Orientation

`goodbot` currently runs as a Python-centric assistant framework in `nanobot/` with CLI and gateway modes driven by `nanobot/cli/commands.py`, channel management in `nanobot/channels/manager.py`, policy/profile constraints in `nanobot/config/`, and agent/tool orchestration in `nanobot/agent/`. Existing controls are primarily policy-level controls enforced in-process.

In this plan, "container isolation" means running agent execution in an isolated runtime instance that is not trusted with host-level privileges or broad credentials. "Control plane" means the trusted runtime that receives inbound messages, applies policy, and dispatches execution requests. "Sandbox plane" means the untrusted runtime where model/tool execution occurs with minimal scoped access and short lifetime.

This plan assumes future cloud deployment will require stronger isolation boundaries than local development defaults, but does not assume a specific cloud provider yet.

## Plan of Work

The first milestone is a gate, not implementation. Confirm operational prerequisites: selected deployment target, security ownership, acceptable latency budget, acceptable cost budget, and tenancy model. If any prerequisite is missing, stop and keep this plan deferred.

The second milestone is architecture evaluation. Compare three execution models using the same control-plane interface shape:

1. Hardened containers on Kubernetes (non-root, read-only root filesystem, dropped capabilities, strict seccomp/AppArmor, default-deny egress).
2. Sandboxed container runtimes (for example gVisor or Kata) with equivalent policy controls.
3. Managed ephemeral sandbox jobs (provider-managed short-lived jobs with network and identity controls).

The third milestone is a proof-of-concept path behind a feature flag. Implement only one narrow path first: remote sandbox execution for high-risk tools (`exec`, file mutation, web fetch/search), while preserving current in-process behavior as fallback. Persist sessions outside the sandbox and pass only scoped input snapshots.

The fourth milestone is full execution-path migration decision. If proof-of-concept meets security and performance targets, plan a controlled move of full agent execution into sandbox jobs. If it fails targets, record rejection and keep policy-only mode as default.

## Concrete Steps

When this plan is resumed, run these commands from the repository root:

    pwd
    rg -n "enterprise_minimal|blocked_tools|restrict_to_workspace" nanobot/config nanobot/agent
    rg -n "Milestone 5A|Milestone 5B|Milestone 6" plan/enterprise-adaptation-feasibility.md

Expected current behavior before implementation:

    - The plan file `plan/cloud-container-isolation-deferred.md` exists and states deferred status.
    - `plan/enterprise-adaptation-feasibility.md` still tracks active product milestones.
    - No sandbox execution service code exists yet in `nanobot/`.

At resume time, create a feature branch and add a design record update before code changes:

    git checkout -b feature/cloud-sandbox-isolation-spike

## Validation and Acceptance

Deferred acceptance criteria (must all be true before implementation starts):

1. Deployment target for cloud runtime is selected and documented.
2. Security owner confirms required isolation objectives (filesystem, network, identity, tenancy).
3. Performance target is defined (for example p95 response latency budget for interactive turns).
4. Cost guardrails are defined (per-message or per-task budget ceiling).
5. Current active milestones remain prioritized until explicitly re-ordered by user direction.

Implementation-phase acceptance criteria (for future execution):

1. A feature-flagged sandbox execution path exists and can be toggled on/off without breaking existing behavior.
2. At least one end-to-end scenario demonstrates that untrusted execution runs in an isolated runtime with scoped access only.
3. Automated tests cover both allowed and blocked behaviors for filesystem, network egress, and identity/token scoping.
4. Fallback behavior is documented and verified when sandbox execution is unavailable.

## Idempotence and Recovery

This deferred plan is safe to re-read and re-apply because it changes no runtime code by itself. If prerequisites are not met, the recovery action is to stop and keep the plan in deferred status. If implementation begins and fails mid-way later, preserve current default behavior behind a feature flag and revert to policy-only execution by configuration.

## Artifacts and Notes

Primary artifact introduced by this work item:

- `plan/cloud-container-isolation-deferred.md` (this file).

Related context artifacts:

- `plan/enterprise-adaptation-feasibility.md` for active milestones and sequencing.
- `docs/ARCHITECTURE.md` and `docs/OVERVIEW.md` for current runtime orientation.

## Interfaces and Dependencies

Future implementation should define a narrow execution interface before choosing runtime details. The interface should accept a scoped execution request (prompt, allowed mounts, allowed tools, identity scope, timeout) and return streamed and final results plus structured errors. The control plane in `nanobot/` should depend on this interface, not on provider-specific SDK calls.

Candidate dependencies to evaluate at resume time are limited to one runtime family first (Kubernetes-native hardened containers, sandboxed runtime class, or managed sandbox jobs). Do not commit to multiple execution backends in the initial proof-of-concept.

Plan creation note (2026-02-16): Created as a separate deferred follow-up ExecPlan at user request to capture cloud container isolation strategy without starting implementation now.
