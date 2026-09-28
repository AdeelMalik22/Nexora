# Nexora Documentation

All project documentation lives under this directory.

## Directory guide

- `api/` — endpoint contracts, authentication, headers, payloads, errors, permissions, and side effects
- `architecture/` — module boundaries, data ownership, tenancy, synchronization, and infrastructure design
- `development/` — local setup, coding rules, migrations, and contribution workflow
- `operations/` — deployment, monitoring, backups, recovery, and incident runbooks
- `security/` — threat model, access control, secrets, privacy, and review procedures
- `testing/` — test strategy, fixtures, isolation checks, and quality gates
- `adr/` — short records of decisions that affect multiple modules

## Documentation rule

If implementation changes behavior, the related documentation must be updated in the same change. Documentation is part of the feature definition of done.
