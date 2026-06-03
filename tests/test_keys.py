"""Tests for license public-key registry (`capacium_models.keys`).

CI design: these tests are SUPPOSED to fail until the placeholder in
`keys.py` is replaced with a real Ed25519 public key hex. This is the
gate that prevents a placeholder from being shipped.
"""

import pytest

from capacium_models.keys import (
    LICENSE_PUBLIC_KEYS,
    UnknownLicenseKid,
    get_license_public_key,
    known_kids,
)


class TestRegistry:
    def test_lic_2026_q2_01_kid_registered(self):
        """The first v2 kid must be in the registry."""
        assert "lic-2026-q2-01" in LICENSE_PUBLIC_KEYS

    def test_kid_namespace_starts_with_lic(self):
        """Per DECISION-001: license kids MUST use the 'lic-' prefix
        (distinct from capability-signing kids)."""
        for kid in LICENSE_PUBLIC_KEYS:
            assert kid.startswith("lic-"), (
                f"kid {kid!r} doesn't follow lic- namespace; "
                f"would conflate with capability-signing kid namespace"
            )


class TestGetPublicKey:
    def test_returns_64_char_hex(self):
        """A registered kid MUST resolve to a 64-char lowercase hex string.

        This test fails if the registry still contains a placeholder.
        """
        pubkey = get_license_public_key("lic-2026-q2-01")
        assert isinstance(pubkey, str), f"expected str, got {type(pubkey).__name__}"
        assert len(pubkey) == 64, (
            f"expected 64 chars, got {len(pubkey)}: {pubkey!r}. "
            f"Placeholder likely still in keys.py — replace with real hex."
        )
        # Must parse as hex
        int(pubkey, 16)

    def test_unknown_kid_raises(self):
        """Unknown kids raise UnknownLicenseKid (NOT KeyError directly)
        so consumers have a single exception type to catch."""
        with pytest.raises(UnknownLicenseKid, match="lic-fake-99"):
            get_license_public_key("lic-fake-99")

    def test_unknown_kid_lists_known_kids(self):
        """Error message must include the set of currently-known kids so
        consumers can debug version mismatches."""
        with pytest.raises(UnknownLicenseKid) as exc_info:
            get_license_public_key("lic-fake-99")
        for kid in LICENSE_PUBLIC_KEYS:
            assert kid in str(exc_info.value), (
                f"error message should mention {kid!r}"
            )


class TestKnownKids:
    def test_returns_all_kids(self):
        assert set(known_kids()) == set(LICENSE_PUBLIC_KEYS.keys())

    def test_sorted_reverse(self):
        """Newest kids first — under the lic-YYYY-qN-NN convention,
        lex reverse == chronological reverse."""
        kids = known_kids()
        assert kids == sorted(LICENSE_PUBLIC_KEYS.keys(), reverse=True)


class TestPlaceholderRejected:
    """Defensive: a future maintainer pasting an invalid value (placeholder,
    base64 instead of hex, truncated, etc.) gets a clear error."""

    def test_placeholder_string_raises(self):
        """Simulate registry corruption: temporarily put a placeholder
        in for a non-real kid and confirm we raise."""
        import capacium_models.keys as keys_mod

        original = keys_mod.LICENSE_PUBLIC_KEYS.copy()
        try:
            keys_mod.LICENSE_PUBLIC_KEYS["lic-test-placeholder"] = (
                "REPLACE_WITH_64_CHAR_HEX_PUBLIC_KEY"
            )
            with pytest.raises(UnknownLicenseKid, match="placeholder|not valid hex"):
                get_license_public_key("lic-test-placeholder")
        finally:
            keys_mod.LICENSE_PUBLIC_KEYS.clear()
            keys_mod.LICENSE_PUBLIC_KEYS.update(original)

    def test_wrong_length_raises(self):
        import capacium_models.keys as keys_mod

        original = keys_mod.LICENSE_PUBLIC_KEYS.copy()
        try:
            keys_mod.LICENSE_PUBLIC_KEYS["lic-test-short"] = "abcd1234" * 4  # 32 chars
            with pytest.raises(UnknownLicenseKid, match="length is 32"):
                get_license_public_key("lic-test-short")
        finally:
            keys_mod.LICENSE_PUBLIC_KEYS.clear()
            keys_mod.LICENSE_PUBLIC_KEYS.update(original)

    def test_non_hex_raises(self):
        import capacium_models.keys as keys_mod

        original = keys_mod.LICENSE_PUBLIC_KEYS.copy()
        try:
            # Right length but not valid hex
            keys_mod.LICENSE_PUBLIC_KEYS["lic-test-nothex"] = "z" * 64
            with pytest.raises(UnknownLicenseKid, match="not valid hex"):
                get_license_public_key("lic-test-nothex")
        finally:
            keys_mod.LICENSE_PUBLIC_KEYS.clear()
            keys_mod.LICENSE_PUBLIC_KEYS.update(original)
