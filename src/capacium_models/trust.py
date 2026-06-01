"""TrustState machine for Exchange listings.
 
Enforces valid state transitions, records history, and validates entry criteria.
 
v2.1: Unified 5-state model (discovered → pending_review → verified → signed → deprecated).
Legacy states (indexed, claimed, audited) are mapped via normalize_legacy_state().
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List

from .models import Listing, TrustTransition


class TrustState(str, Enum):
    DISCOVERED = "discovered"          # Found by crawler, minimal validation
    PENDING_REVIEW = "pending_review"  # Schema validated, composite score computed (formerly "audited")
    VERIFIED = "verified"              # Publisher claimed and ownership verified
    SIGNED = "signed"                  # Cryptographic signature present and valid
    DEPRECATED = "deprecated"          # End-of-life, superseded, or abandoned

    @classmethod
    def ordering(cls) -> List["TrustState"]:
        return [
            cls.DISCOVERED,
            cls.PENDING_REVIEW,
            cls.VERIFIED,
            cls.SIGNED,
            cls.DEPRECATED,
        ]

    def __lt__(self, other):
        if self.__class__ is other.__class__:
            ordering = self.ordering()
            return ordering.index(self) < ordering.index(other)
        return NotImplemented

    def __gt__(self, other):
        if self.__class__ is other.__class__:
            ordering = self.ordering()
            return ordering.index(self) > ordering.index(other)
        return NotImplemented

    def __ge__(self, other):
        if self.__class__ is other.__class__:
            ordering = self.ordering()
            return ordering.index(self) >= ordering.index(other)
        return NotImplemented

    def __le__(self, other):
        if self.__class__ is other.__class__:
            ordering = self.ordering()
            return ordering.index(self) <= ordering.index(other)
        return NotImplemented


# Legacy state mapping for backward compatibility
LEGACY_STATE_MAP: Dict[str, str] = {
    "indexed": "pending_review",
    "claimed": "verified",
    "audited": "pending_review",  # v1.0 → v2.1 migration
}


def normalize_legacy_state(state: str) -> str:
    """Map old trust states to current model.

    indexed/audited → pending_review, claimed → verified.
    All other states pass through unchanged.
    """
    return LEGACY_STATE_MAP.get(state, state)


class TrustTransitionError(Exception):
    pass


VALID_TRANSITIONS = {
    TrustState.DISCOVERED: {TrustState.PENDING_REVIEW},
    TrustState.PENDING_REVIEW: {TrustState.VERIFIED, TrustState.DISCOVERED},
    TrustState.VERIFIED: {TrustState.SIGNED, TrustState.PENDING_REVIEW},
    TrustState.SIGNED: {TrustState.VERIFIED, TrustState.DEPRECATED},
    TrustState.DEPRECATED: {TrustState.PENDING_REVIEW},
}


class TrustMachine:

    @staticmethod
    def normalize_legacy_state(state: str) -> str:
        """Map old trust states to new ones (convenience wrapper)."""
        return normalize_legacy_state(state)

    @staticmethod
    def can_transition(from_state: TrustState, to_state: TrustState) -> bool:
        allowed = VALID_TRANSITIONS.get(from_state, set())
        return to_state in allowed

    @staticmethod
    def validate_entry_criteria(listing: Listing, target_state: TrustState) -> list:
        errors = []

        if target_state == TrustState.PENDING_REVIEW:
            if not listing.canonical_name:
                errors.append("Pending review state requires canonical_name")
            if not listing.short_description:
                errors.append("Pending review state requires short_description")
            if not listing.canonical_source_url:
                errors.append("Pending review state requires canonical_source_url")

        elif target_state == TrustState.VERIFIED:
            if not listing.publisher_id:
                errors.append("Verified state requires publisher_id")

        elif target_state == TrustState.SIGNED:
            if not listing.fingerprint:
                errors.append("Signed state requires fingerprint")
            if not listing.signature_value:
                errors.append("Signed state requires signature_value")

        return errors

    @classmethod
    def transition(
        cls,
        listing: Listing,
        to_state: TrustState,
        reason: str = "",
        triggered_by: str = "system",
    ) -> Listing:
        # Normalize legacy states before processing
        current_state_str = normalize_legacy_state(listing.trust_state)
        from_state = TrustState(current_state_str)

        if from_state == to_state:
            raise TrustTransitionError(
                f"Listing is already in state '{to_state.value}'"
            )

        if not cls.can_transition(from_state, to_state):
            raise TrustTransitionError(
                f"Cannot transition from '{from_state.value}' to '{to_state.value}'. "
                f"Valid targets: {[s.value for s in VALID_TRANSITIONS.get(from_state, set())]}"
            )

        criteria_errors = cls.validate_entry_criteria(listing, to_state)
        if criteria_errors:
            raise TrustTransitionError(
                f"Entry criteria not met for '{to_state.value}': {'; '.join(criteria_errors)}"
            )

        transition = TrustTransition(
            from_state=from_state.value,
            to_state=to_state.value,
            reason=reason,
            triggered_by=triggered_by,
        )

        listing.trust_state = to_state.value
        listing.trust_history.append(transition.to_dict())
        listing.updated_at = datetime.utcnow().isoformat()

        return listing
