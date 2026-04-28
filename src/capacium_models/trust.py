"""TrustState machine for Exchange listings.

Enforces valid state transitions, records history, and validates entry criteria.
"""

from datetime import datetime
from enum import Enum
from typing import List

from .models import Listing, TrustTransition


class TrustState(str, Enum):
    DISCOVERED = "discovered"
    INDEXED = "indexed"
    CLAIMED = "claimed"
    VERIFIED = "verified"
    AUDITED = "audited"

    @classmethod
    def ordering(cls) -> List["TrustState"]:
        return [
            cls.DISCOVERED,
            cls.INDEXED,
            cls.CLAIMED,
            cls.VERIFIED,
            cls.AUDITED,
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


class TrustTransitionError(Exception):
    pass


VALID_TRANSITIONS = {
    TrustState.DISCOVERED: {TrustState.INDEXED},
    TrustState.INDEXED: {TrustState.CLAIMED},
    TrustState.CLAIMED: {TrustState.VERIFIED},
    TrustState.VERIFIED: {TrustState.AUDITED, TrustState.CLAIMED},
    TrustState.AUDITED: {TrustState.VERIFIED},
}


class TrustMachine:

    @staticmethod
    def can_transition(from_state: TrustState, to_state: TrustState) -> bool:
        allowed = VALID_TRANSITIONS.get(from_state, set())
        return to_state in allowed

    @staticmethod
    def validate_entry_criteria(listing: Listing, target_state: TrustState) -> list:
        errors = []

        if target_state == TrustState.INDEXED:
            if not listing.canonical_name:
                errors.append("Indexed state requires canonical_name")
            if not listing.short_description:
                errors.append("Indexed state requires short_description")
            if not listing.canonical_source_url:
                errors.append("Indexed state requires canonical_source_url")
            if not listing.primary_category:
                errors.append("Indexed state requires primary_category")

        elif target_state == TrustState.CLAIMED:
            if not listing.publisher_id:
                errors.append("Claimed state requires publisher_id")

        elif target_state == TrustState.VERIFIED:
            if not listing.publisher_id:
                errors.append("Verified state requires publisher_id")

        elif target_state == TrustState.AUDITED:
            if not listing.publisher_id:
                errors.append("Audited state requires a verified publisher")

        return errors

    @classmethod
    def transition(
        cls,
        listing: Listing,
        to_state: TrustState,
        reason: str = "",
        triggered_by: str = "system",
    ) -> Listing:
        from_state = TrustState(listing.trust_state)

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

        if to_state == TrustState.INDEXED and not listing.indexed_at:
            listing.indexed_at = datetime.utcnow().isoformat()

        return listing
