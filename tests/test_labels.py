from capacium_models.labels import (
    RESOURCE_KIND_LABELS,
    OPERATOR_TYPE_LABELS,
    INSTALL_STATUS_LABELS,
    TRUST_BADGES,
    get_kind_label,
    get_operator_type_label,
    get_install_status_label,
    get_trust_badge,
)
from capacium_models import (
    TRUST_BADGES as PUBLIC_TRUST_BADGES,
    get_trust_badge as get_public_trust_badge,
)


class TestResourceKindLabels:
    def test_all_twelve_kinds_have_labels(self):
        expected_kinds = {
            "skill",
            "mcp-server",
            "bundle",
            "tool",
            "prompt",
            "template",
            "workflow",
            "connector-pack",
            "operator",
            "checkpoint",
            "policy",
            "resource",
        }
        assert set(RESOURCE_KIND_LABELS.keys()) == expected_kinds

    def test_known_kind_returns_label(self):
        assert get_kind_label("skill") == "Skill"
        assert get_kind_label("mcp-server") == "MCP Server"
        assert get_kind_label("bundle") == "Bundle"
        assert get_kind_label("tool") == "Tool"
        assert get_kind_label("prompt") == "Prompt"
        assert get_kind_label("template") == "Template"
        assert get_kind_label("workflow") == "Workflow"
        assert get_kind_label("connector-pack") == "Connector Pack"
        assert get_kind_label("operator") == "Operator"
        assert get_kind_label("checkpoint") == "Checkpoint"
        assert get_kind_label("policy") == "Policy"
        assert get_kind_label("resource") == "Resource"

    def test_unknown_kind_falls_back_to_key(self):
        assert get_kind_label("gizmo") == "gizmo"
        assert get_kind_label("") == ""
        assert get_kind_label("NONEXISTENT") == "NONEXISTENT"


class TestOperatorTypeLabels:
    def test_all_operator_types_have_labels(self):
        expected = {"ai", "human", "hybrid"}
        assert set(OPERATOR_TYPE_LABELS.keys()) == expected

    def test_known_operator_types(self):
        assert get_operator_type_label("ai") == "AI"
        assert get_operator_type_label("human") == "Human"
        assert get_operator_type_label("hybrid") == "Hybrid"

    def test_unknown_operator_type_falls_back_to_key(self):
        assert get_operator_type_label("robot") == "robot"
        assert get_operator_type_label("") == ""


class TestInstallStatusLabels:
    def test_all_statuses_have_labels(self):
        expected = {
            "not_installed",
            "installing",
            "installed",
            "failed",
            "update_available",
            "removed",
        }
        assert set(INSTALL_STATUS_LABELS.keys()) == expected

    def test_known_statuses(self):
        assert get_install_status_label("not_installed") == "Not Installed"
        assert get_install_status_label("installing") == "Installing"
        assert get_install_status_label("installed") == "Installed"
        assert get_install_status_label("failed") == "Failed"
        assert get_install_status_label("update_available") == "Update Available"
        assert get_install_status_label("removed") == "Removed"

    def test_unknown_status_falls_back_to_key(self):
        assert get_install_status_label("pending") == "pending"
        assert get_install_status_label("") == ""


class TestTrustBadges:
    def test_all_badges_present(self):
        expected = {"discovered", "pending_review", "verified", "signed", "deprecated"}
        assert set(TRUST_BADGES.keys()) == expected

    def test_known_badges(self):
        assert get_trust_badge("discovered") == "Discovered"
        assert get_trust_badge("pending_review") == "Pending Review"
        assert get_trust_badge("verified") == "Verified"
        assert get_trust_badge("signed") == "Signed"
        assert get_trust_badge("deprecated") == "Deprecated"

    def test_unknown_badge_falls_back_to_key(self):
        assert get_trust_badge("super_trusted") == "super_trusted"
        assert get_trust_badge("") == ""

    def test_top_level_api_keeps_rich_badge_metadata(self):
        assert PUBLIC_TRUST_BADGES["verified"]["label"] == "Verified"
        assert PUBLIC_TRUST_BADGES["verified"]["symbol"] == "✓"
        assert get_public_trust_badge("verified") == PUBLIC_TRUST_BADGES["verified"]

    def test_top_level_api_keeps_legacy_normalization(self):
        assert get_public_trust_badge("audited") == PUBLIC_TRUST_BADGES["pending_review"]
