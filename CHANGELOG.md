# Changelog

All notable changes to this project will be documented in this file.

## capacium-models v0.2.0 — Trust Model v2 (2026-05-24)

### Breaking Changes

- **Trust model unified to 4 states**: `TrustState` enum reduced from 6
  states to 4: `discovered`, `audited`, `verified`, `signed`. Legacy states
  `indexed` and `claimed` are mapped automatically via `LEGACY_STATE_MAP`.

### New Features

- **TrustMachine state machine**: New `TrustMachine` class with `transition()`
  method enforcing valid trust state transitions. Supports `promote()` and
  `demote()` with reason tracking and timestamp history.

- **Legacy state normalization**: `normalize_legacy_state()` function
  transparently maps `indexed` → `audited` and `claimed` → `verified` for
  backward compatibility with existing database records.

- **Trust ordering**: `TrustState.ordering()` returns states in promotion
  order with comparison support (`>=`, `<=`).

### Bug Fixes

- **Search min_trust_state filter** (355cded): Fixed `min_trust_state` filter
  to normalize legacy states before comparison. Legacy aliases (e.g.
  `indexed`) are now included in the SQL `IN` clause so database rows with
  old state values still match correctly.

- **Trust model completeness** (e57b2cd): Fixed incomplete v2 trust model
  implementation — added missing `LEGACY_STATE_MAP` export and
  `normalize_legacy_state()` function.

## capacium-models v0.1.0 — Initial Release (2026-05-11)

- `Listing` dataclass with `from_dict()` / `to_dict()` roundtrip
- `SearchQuery` with faceted filtering (text, type, category, trust, tags)
- `ExchangeSearch` with dynamic SQL WHERE clause builder
- `TrustState` enum (original 6-state model)
