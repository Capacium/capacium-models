"""Shared domain models for the Capacium ecosystem.

Usage:
    from capacium_models import Listing, TrustState, TrustMachine
"""

from .models import (
    MCPClient,
    MCPMetadata,
    TrustTransition,
    Listing,
    Publisher,
    Category,
    Subcategory,
    TagCount,
    Collection,
    ClaimRequest,
    VerificationRecord,
    SearchQuery,
)
from .trust import TrustState, TrustMachine, TRUST_BADGES, get_trust_badge
from .keys import (
    LICENSE_PUBLIC_KEYS,
    UnknownLicenseKid,
    get_license_public_key,
    known_kids,
)
from .labels import (
    RESOURCE_KIND_LABELS,
    OPERATOR_TYPE_LABELS,
    INSTALL_STATUS_LABELS,
    get_kind_label,
    get_operator_type_label,
    get_install_status_label,
)
from .search import ExchangeSearch

__all__ = [
    "MCPClient",
    "MCPMetadata",
    "TrustState",
    "TrustTransition",
    "TrustMachine",
    "Listing",
    "Publisher",
    "Category",
    "Subcategory",
    "TagCount",
    "Collection",
    "ClaimRequest",
    "VerificationRecord",
    "SearchQuery",
    "ExchangeSearch",
    "TRUST_BADGES",
    "get_trust_badge",
    "RESOURCE_KIND_LABELS",
    "OPERATOR_TYPE_LABELS",
    "INSTALL_STATUS_LABELS",
    "get_kind_label",
    "get_operator_type_label",
    "get_install_status_label",
    "LICENSE_PUBLIC_KEYS",
    "UnknownLicenseKid",
    "get_license_public_key",
    "known_kids",
]
