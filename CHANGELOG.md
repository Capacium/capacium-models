# Changelog

All notable changes to this project will be documented in this file.

## capacium-models v1.1.0 — Work 5.0 metadata (2026-11-15)

### New Features

- Added the Work 5.0 metadata fields `operator_meta`, `checkpoint_meta`,
  `policy_meta` and `resource_identity` (optional objects), and `replaces` and
  `previous_identities` (lists of strings), to the package model. They
  round-trip through `to_dict` and `from_dict`.

### Changed

- The package model field `package_type` is renamed `kind`. `to_dict` still
  emits `package_type` next to `kind`, and `from_dict` accepts either key, so
  stored records and existing consumers of the dictionary form keep working.
- The search query field `package_type` is renamed `kind`. Callers that build a
  search query with `package_type=` must pass `kind=` instead.

## capacium-models v0.5.0 — Canonical UI Labels (2026-07-16)

### New Features

- Added `capacium_models.labels` as the canonical source for resource-kind,
  operator-type, install-status, and string-only trust badge labels used across
  Capacium surfaces.
- Exported resource-kind, operator-type, and install-status label registries and
  lookup helpers from the package root.
- Added Python 3.13 and 3.14 package classifiers.

### Compatibility

- Preserved the v0.4.x package-level `TRUST_BADGES` and
  `get_trust_badge()` contract. They continue to expose rich badge metadata
  and legacy trust-state normalization from `capacium_models.trust`.
- String-only trust labels remain available from `capacium_models.labels`.

### Packaging

- Added project URLs and SPDX-form license metadata.
- Added a tag-triggered GitHub Actions trusted-publishing workflow for PyPI.

## capacium-models v0.4.1 — License Public-Key Registry (2026-06-03)

### New Features

- **`capacium_models.keys` module** — license public-key registry for
  Ed25519 token verification. Holds 64-char hex public keys indexed by
  `kid`. Matching private keys live ONLY in envctl on prod
  (`CAPACIUM_LICENSE_SIGNING_KEY` on capacium-exchange).

  Exports:
  - `LICENSE_PUBLIC_KEYS: Dict[str, str]` — the registry itself.
  - `get_license_public_key(kid: str) -> str` — lookup with validated
    return; raises `UnknownLicenseKid` if kid is missing or its value is
    malformed (e.g., still a placeholder).
  - `known_kids() -> List[str]` — registry keys sorted newest-first.
  - `UnknownLicenseKid` — dedicated `KeyError` subclass for consumers.

  Initial entry: `lic-2026-q2-01`. Future kids append; old kids stay
  active until their tokens expire. See module docstring for rotation
  lifecycle.

  DECISION-001 reference: license-signing keypair is DISTINCT from
  capability-signing keypair; `lic-` namespace enforced.

### Consumer integration

- `capacium-exchange.marketplace.licensing.LicenseKeyManager` (FIX-A-002)
  imports `get_license_public_key` from this module to verify tokens
  locally — no round-trip to Exchange needed for signature verification.

### No breaking changes

- Additive only. All v0.4.0 consumers continue to work unchanged.

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
