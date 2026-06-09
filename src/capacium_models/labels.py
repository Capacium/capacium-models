"""Canonical label registries for all Capacium surfaces.

These dicts serve as single sources of truth — all UIs, badges, APIs, and CLI
surfaces derive their display labels from these exactly maps.
"""

RESOURCE_KIND_LABELS = {
    "skill": "Skill",
    "mcp-server": "MCP Server",
    "bundle": "Bundle",
    "tool": "Tool",
    "prompt": "Prompt",
    "template": "Template",
    "workflow": "Workflow",
    "connector-pack": "Connector Pack",
    "operator": "Operator",
    "checkpoint": "Checkpoint",
    "policy": "Policy",
    "resource": "Resource",
}

OPERATOR_TYPE_LABELS = {
    "ai": "AI",
    "human": "Human",
    "hybrid": "Hybrid",
}

INSTALL_STATUS_LABELS = {
    "not_installed": "Not Installed",
    "installing": "Installing",
    "installed": "Installed",
    "failed": "Failed",
    "update_available": "Update Available",
    "removed": "Removed",
}

TRUST_BADGES = {
    "discovered": "Discovered",
    "pending_review": "Pending Review",
    "verified": "Verified",
    "signed": "Signed",
    "deprecated": "Deprecated",
}


def get_kind_label(kind: str) -> str:
    """Return the human-readable label for a capability kind.

    Falls back to the raw string if the kind is unknown.
    """
    return RESOURCE_KIND_LABELS.get(kind, kind)


def get_operator_type_label(op_type: str) -> str:
    """Return the human-readable label for an operator type.

    Falls back to the raw string if the type is unknown.
    """
    return OPERATOR_TYPE_LABELS.get(op_type, op_type)


def get_install_status_label(status: str) -> str:
    """Return the human-readable label for an install status.

    Falls back to the raw string if the status is unknown.
    """
    return INSTALL_STATUS_LABELS.get(status, status)


def get_trust_badge(state: str) -> str:
    """Return the human-readable trust badge label for a trust state.

    Falls back to the raw string if the state is unknown.
    """
    return TRUST_BADGES.get(state, state)
