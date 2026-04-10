<!--
SYNC IMPACT REPORT
==================
Version change: N/A (initial) → 1.0.0
Modified principles: none (initial population from template)
Added sections:
  - Core Principles (5 principles defined)
  - Technology Stack
  - Development Workflow
  - Governance
Removed sections: none
Templates reviewed:
  - .specify/templates/plan-template.md  ✅ Constitution Check section present; no updates needed
  - .specify/templates/spec-template.md  ✅ User stories, requirements, success criteria aligned
  - .specify/templates/tasks-template.md ✅ Phase structure compatible with principles
  - .specify/extensions.yml              ✅ Hook configuration compatible
Deferred TODOs:
  - TODO(RATIFICATION_DATE): Set to project initialization date 2026-04-10 (today);
    update if an earlier governance decision date is established.
-->

# Piekarnia Constitution

## Core Principles

### I. Domain-Driven Design

All features MUST be modeled around core bakery business concepts:
products, recipes, orders, inventory, and customers.
Business rules live in the domain layer and MUST NOT leak into infrastructure
or presentation layers. Every new model or service MUST have a clear bakery
domain justification — no purely technical entities without a domain counterpart.

**Rationale**: A bakery management system's complexity comes from the business
domain (perishable inventory, time-sensitive production schedules, custom orders).
Centering design on the domain prevents ad-hoc coupling and keeps the codebase
aligned with stakeholder language.

### II. API-First

Every feature MUST expose its capabilities through a well-defined API contract
(REST or equivalent) before UI or CLI layers are built.
Contracts MUST be documented (OpenAPI or equivalent) and versioned.
Breaking changes to existing contracts require a major version bump and a
migration path for consumers.

**Rationale**: An API-first approach ensures the system can serve multiple
clients (web, mobile, POS terminals) without re-architecting the backend.
It also enables contract-based testing from day one.

### III. Test-First (NON-NEGOTIABLE)

TDD is mandatory for all production code:
1. Write tests → obtain stakeholder/peer approval → confirm tests fail → implement.
2. Red-Green-Refactor cycle MUST be strictly followed.
3. Unit tests MUST cover all domain logic; integration tests MUST cover all
   API contracts and inter-service boundaries.

**Rationale**: Bakery operations involve financial transactions and perishable
goods. Regressions carry real business cost. A strict test-first discipline
catches contract violations before they reach production.

### IV. Data Integrity & Auditability

All mutations to inventory, orders, recipes, and pricing MUST be:
- Persisted atomically (no partial writes).
- Accompanied by an audit trail (who, what, when).
- Validated at the domain boundary before persistence.

Soft-deletes MUST be used for business entities (products, recipes, customers);
hard-deletes are prohibited without explicit data-retention policy approval.

**Rationale**: Bakery operations depend on accurate stock counts and order
histories for planning, compliance, and customer trust. Silent data loss or
corruption is unacceptable.

### V. Simplicity & Incremental Delivery

Start with the simplest implementation that satisfies the acceptance criteria.
YAGNI (You Aren't Gonna Need It) applies: no speculative abstractions,
no premature generalization.
Each feature MUST be deliverable and demonstrable as an independent,
working slice before the next slice begins.

**Rationale**: Over-engineering a bakery management system creates maintenance
burden without business value. Incremental delivery allows real-world feedback
to shape design before investment compounds.

## Technology Stack

The following constraints apply to all implementation work:

- **Language/Runtime**: To be confirmed per feature spec (default: Python 3.11+
  for backend services; TypeScript for any frontend).
- **Storage**: Relational database required for transactional data
  (PostgreSQL preferred); cache layer only when profiling identifies need.
- **API Style**: RESTful HTTP with JSON; OpenAPI 3.x specification mandatory.
- **Testing**: pytest (Python) or Jest (TypeScript); contract tests via
  Pact or equivalent; integration tests MUST run against a real database.
- **Deployment Target**: Containerized (Docker); cloud-agnostic by default.
- **Dependencies**: Every new dependency MUST be justified in the feature plan;
  transitive dependency count SHOULD be minimized.

## Development Workflow

1. **Branch per feature**: All work happens on a numbered feature branch
   (`###-short-description`). No direct commits to `main`.
2. **Spec before code**: A feature spec (`spec.md`) MUST be approved before
   any implementation begins.
3. **Plan before tasks**: An implementation plan (`plan.md`) MUST exist before
   task generation.
4. **Constitution check**: Every plan MUST include a Constitution Check gate
   that verifies compliance with all five Core Principles before Phase 0.
5. **Review required**: All PRs require at least one peer review verifying
   both functional correctness and principle compliance.
6. **Commit discipline**: Commits MUST be atomic and reference the task ID
   (e.g., `feat(T014): implement order placement endpoint`).

## Governance

This Constitution supersedes all other project-level practices.
Any conflict between a team convention and this document MUST be resolved
in favor of this document or via a formal amendment.

**Amendment procedure**:
1. Propose the amendment with rationale in a dedicated PR or issue.
2. Obtain approval from the project lead and at least one senior contributor.
3. Update this file, increment the version following semantic versioning,
   and record the amendment in the Sync Impact Report comment block.
4. Communicate the change to all active contributors before merging.

**Versioning policy**:
- MAJOR: Removal or redefinition of a Core Principle; backward-incompatible
  governance change.
- MINOR: New principle, new mandatory section, or materially expanded guidance.
- PATCH: Clarifications, wording improvements, typo fixes.

**Compliance review**: Constitution Check gates in plan.md serve as the
primary compliance mechanism. A quarterly review of principle adherence is
RECOMMENDED as the project grows.

**Version**: 1.0.0 | **Ratified**: 2026-04-10 | **Last Amended**: 2026-04-10
