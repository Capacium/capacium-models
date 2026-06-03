# Changelog

All notable changes to this project will be documented in this file.

## capacium-models v0.4.0 — 5-State Trust Model + TRUST_BADGES (2026-06-03)

### Breaking Changes

- **Trust model migrated from 4 states to 5 states**: `TrustState` enum is
  now `discovered → pending_review → verified → signed → deprecated`. The
  `AUDITED` state has been **removed** and renamed to `PENDING_REVIEW`.
  Legacy values continue to be mapped via `LEGACY_STATE_MAP` (`"audited"`
  → `"pending_review"`). Downstream code referencing `TrustState.AUDITED`
  directly must be updated to `TrustState.PENDING_REVIEW`. Database rows
  with `trust_state = 'audited'` are normalized transparently by
  `normalize_legacy_state()`.

- **`VALID_TRANSITIONS` updated** to reflect the 5-state graph:
  `discovered → pending_review`, `pending_review → {verified, discovered}`,
  `verified → {signed, pending_review}`, `signed → {verified, deprecated}`,
  `deprecated → pending_review`. The new `DEPRECATED` end-of-life state
  supports superseded or abandoned listings.

### New Features

- **`TRUST_BADGES`** (`src/capacium_models/trust.py`): single source of
  truth dict mapping each v2 state to its display label, symbol, color,
  description, and ordering. Eliminates vocabulary drift across surfaces
  (CLI, MCP, WP bridge, Exchange) (FIX-F-001).

- **`get_trust_badge(trust_state: str)`** helper: returns the badge
  definition for any trust state, applying legacy normalization on the
  way (`audited`/`indexed` → `pending_review` badge; `claimed` → `verified`
  badge). Unknown states fall back to `discovered` badge.

### Bug Fixes

- **`datetime.utcnow()` removed**: replaced 6 occurrences in
  `src/capacium_models/models.py` (lines 74, 165, 215, 289, 326, 352) with
  `datetime.now(timezone.utc)`. Closes the FIX-G-004 completion gap that
  was missed in the original Stream G codemod (the Fix-PRD claimed
  zero `utcnow()` across all 6 repos, but capacium-models was overlooked).
  Eliminates `DeprecationWarning` noise under Python 3.12+ and prevents
  the future Python release that removes `utcnow()` from breaking the
  package.

- **Migration 0014 trust-state remap docs** (FIX-F-002): the
  `migrations/0014_trust_5state.sql` in capacium-exchange now carries a
  pre/post distribution comment block documenting the legacy state remap
  (`audited → pending_review`, `claimed → verified`). Verified idempotent
  and reversible. Tracked in capacium-exchange — included here as the
  cross-repo context for this release.

### Test Migration

- `tests/test_models.py` migrated from v1 4-state vocabulary to v2
  5-state vocabulary (19 `TrustState.AUDITED` references → `PENDING_REVIEW`;
  10 string `"audited"` → `"pending_review"`; ordering test length
  4 → 5; method names renamed for clarity). All 55 tests pass.

### Process Notes

- The 5-state migration commit (`62670bd`) landed on `main` without a
  PR (direct push). This release is the first tag covering those changes;
  the migration is captured in this CHANGELOG entry rather than a
  separate v0.3.0 to keep the release trail aligned with shipped tags.

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
