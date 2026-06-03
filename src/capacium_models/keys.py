"""License public-key registry for capacium-models consumers.

Consumers verify license tokens (issued by capacium-exchange `LicenseService`)
using Ed25519. The matching PRIVATE key lives ONLY in envctl on prod, under:

    envctl get capacium-exchange CAPACIUM_LICENSE_SIGNING_KEY    # 64-hex private
    envctl get capacium-exchange CAPACIUM_LICENSE_SIGNING_KID    # current kid

This module holds the corresponding PUBLIC keys, indexed by `kid` (key
identifier as embedded in license token payloads). Consumers use these to
verify signatures locally without round-tripping to the Exchange.

Key rotation lifecycle for a given kid:
  - Active:     issues new tokens; PRIVATE held in envctl
  - Retired:    no longer issues NEW tokens; OLD tokens still validate
                (entry stays in this registry until last token expires)
  - Removed:    entry deleted from registry; OLD tokens fail validation

To add a new kid: append to LICENSE_PUBLIC_KEYS, bump the package version
(minor bump — additive); ship as a new capacium-models release. NEVER
remove an entry whose tokens may still be in circulation.

DECISION-001 reference: license-signing keypair is DISTINCT from
capability-signing keypair. kid namespace MUST start with `lic-`.
"""

from __future__ import annotations

from typing import Dict, List


# ── License public-key registry ───────────────────────────────────────────
#
# Format: dict[kid -> 64-char lowercase hex] (32 bytes Ed25519 public key)
#
# Each entry MUST match the private key currently set as
# CAPACIUM_LICENSE_SIGNING_KEY in envctl on capacium-prod, under the
# matching kid CAPACIUM_LICENSE_SIGNING_KID.

LICENSE_PUBLIC_KEYS: Dict[str, str] = {
    # ──────────────────────────────────────────────────────────────────────
    # kid: lic-2026-q2-01
    # Added: 2026-06-03 (initial v2 launch — corresponds to the FIRST
    # Ed25519 keypair generated on maintainer workstation, private uploaded
    # to envctl on capacium-prod)
    # ──────────────────────────────────────────────────────────────────────
    "lic-2026-q2-01": "8e5e33e1ab3676d239a1f89cded6afca9aca0e8ba24c3b4b50ad4b71ef84e978",
}


# ── Public API ────────────────────────────────────────────────────────────


class UnknownLicenseKid(KeyError):
    """Raised when a license token's `kid` is not in the public-key registry.

    Consumers MUST reject the token in this case (treat as invalid signature).
    Receiving this exception is the signal to upgrade `capacium-models` to a
    newer version that includes the missing kid.
    """


def get_license_public_key(kid: str) -> str:
    """Return the 64-char hex public key for a license kid.

    Args:
        kid: Key identifier as embedded in license token payload.

    Returns:
        64-char lowercase hex string representing the Ed25519 public key.

    Raises:
        UnknownLicenseKid: when `kid` is not in `LICENSE_PUBLIC_KEYS`, OR
            when its registered value is not a valid 64-char hex string
            (e.g., still a placeholder, malformed registry entry).
            Consumer code MUST reject the token in this case.
    """
    try:
        pubkey = LICENSE_PUBLIC_KEYS[kid]
    except KeyError as e:
        raise UnknownLicenseKid(
            f"kid={kid!r} not in LICENSE_PUBLIC_KEYS. "
            f"Known kids: {known_kids()}. "
            f"Upgrade capacium-models to support newer kids."
        ) from e
    _validate_hex(kid, pubkey)
    return pubkey


def known_kids() -> List[str]:
    """Return all registered kids, sorted newest-first (lexicographic reverse).

    Naming convention `lic-YYYY-qN-NN` makes lex reverse equal to
    chronological reverse.
    """
    return sorted(LICENSE_PUBLIC_KEYS.keys(), reverse=True)


# ── Internal helpers ──────────────────────────────────────────────────────


def _validate_hex(kid: str, pubkey: str) -> None:
    """Validate that `pubkey` is a 64-char lowercase hex string.

    Raises UnknownLicenseKid (not ValueError) so consumers handling kid
    lookup errors have a single exception type to catch.
    """
    if not isinstance(pubkey, str):
        raise UnknownLicenseKid(
            f"kid={kid!r} has non-string pubkey of type {type(pubkey).__name__}"
        )
    if len(pubkey) != 64:
        raise UnknownLicenseKid(
            f"kid={kid!r} pubkey length is {len(pubkey)}, expected 64 hex chars. "
            f"Likely placeholder — registry entry must be filled in before release."
        )
    try:
        int(pubkey, 16)
    except ValueError as e:
        raise UnknownLicenseKid(
            f"kid={kid!r} pubkey is not valid hex: {e}. "
            f"Registry entry may still contain a placeholder."
        ) from e
