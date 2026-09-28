# Documentation Rules

## Required location

Create project documentation under `docs/`. Do not add scattered design notes to source directories or the repository root unless a tool requires a root-level file.

## Endpoint documentation

Document every endpoint with:

- method and URL;
- authentication and required headers;
- tenant and branch scope;
- permission required;
- request and response examples;
- validation and error codes;
- side effects, audit events, and asynchronous work;
- idempotency and retry behavior.

## Model documentation

Document the owning module, tenant scope, lifecycle, deletion policy, important constraints, and relationships for every business model.

## Architecture decisions

Use an ADR in `docs/adr/` when a decision affects multiple modules, data correctness, security, deployment, or client compatibility. Each ADR should state the context, decision, consequences, and alternatives considered.

## Change rule

Every pull request that changes behavior must update its affected documentation or explain why no documentation change is needed.
