"""Tests for shared domain models."""

import json
import pytest

from capacium_models.models import (
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
from capacium_models import TrustState, TrustMachine
from capacium_models.trust import TrustTransitionError


class TestTrustState:
    def test_values(self):
        assert TrustState.DISCOVERED.value == "discovered"
        assert TrustState.AUDITED.value == "audited"
        assert TrustState.VERIFIED.value == "verified"
        assert TrustState.SIGNED.value == "signed"

    def test_ordering(self):
        ordering = TrustState.ordering()
        assert len(ordering) == 4
        assert ordering[0] == TrustState.DISCOVERED
        assert ordering[-1] == TrustState.SIGNED

    def test_from_string(self):
        assert TrustState("discovered") == TrustState.DISCOVERED
        assert TrustState("verified") == TrustState.VERIFIED
        assert TrustState("signed") == TrustState.SIGNED

    def test_comparison(self):
        assert TrustState.DISCOVERED < TrustState.AUDITED
        assert TrustState.AUDITED < TrustState.VERIFIED
        assert TrustState.VERIFIED < TrustState.SIGNED
        assert TrustState.VERIFIED >= TrustState.VERIFIED
        assert TrustState.SIGNED >= TrustState.AUDITED


class TestTrustMachine:
    def setup_method(self):
        self.listing = Listing(
            canonical_name="org/test",
            canonical_source_url="https://github.com/org/test",
            short_description="A test",
            primary_category="developer-tools",
            package_type="tool",
        )

    # -- Valid transitions --

    def test_can_transition_valid_forward(self):
        assert TrustMachine.can_transition(TrustState.DISCOVERED, TrustState.AUDITED) is True
        assert TrustMachine.can_transition(TrustState.AUDITED, TrustState.VERIFIED) is True
        assert TrustMachine.can_transition(TrustState.VERIFIED, TrustState.SIGNED) is True

    def test_can_transition_valid_downgrade(self):
        assert TrustMachine.can_transition(TrustState.AUDITED, TrustState.DISCOVERED) is True
        assert TrustMachine.can_transition(TrustState.VERIFIED, TrustState.AUDITED) is True
        assert TrustMachine.can_transition(TrustState.SIGNED, TrustState.VERIFIED) is True

    # -- Invalid transitions --

    def test_can_transition_invalid(self):
        assert TrustMachine.can_transition(TrustState.DISCOVERED, TrustState.VERIFIED) is False
        assert TrustMachine.can_transition(TrustState.DISCOVERED, TrustState.SIGNED) is False
        assert TrustMachine.can_transition(TrustState.AUDITED, TrustState.SIGNED) is False

    # -- Transition execution --

    def test_transition_discovered_to_audited(self):
        result = TrustMachine.transition(
            self.listing, TrustState.AUDITED, "Schema validated"
        )
        assert result.trust_state == "audited"
        assert len(result.trust_history) == 1
        assert result.trust_history[0]["from_state"] == "discovered"
        assert result.trust_history[0]["to_state"] == "audited"
        # indexed_at no longer set in v2 trust model (indexed state removed)

    def test_transition_audited_to_verified_requires_publisher(self):
        listing = Listing(
            canonical_name="org/test",
            canonical_source_url="https://github.com/org/test",
            short_description="test",
            primary_category="tools",
        )
        TrustMachine.transition(listing, TrustState.AUDITED, "ok")
        with pytest.raises(TrustTransitionError, match="publisher_id"):
            TrustMachine.transition(listing, TrustState.VERIFIED, "no publisher")

    def test_transition_audited_to_verified_with_publisher(self):
        listing = Listing(
            canonical_name="org/test",
            canonical_source_url="https://github.com/org/test",
            short_description="test",
            primary_category="tools",
            publisher_id="pub-1",
        )
        TrustMachine.transition(listing, TrustState.AUDITED, "ok")
        result = TrustMachine.transition(listing, TrustState.VERIFIED, "publisher verified")
        assert result.trust_state == "verified"

    def test_transition_verified_to_signed_requires_signature(self):
        listing = Listing(
            canonical_name="org/test",
            canonical_source_url="https://github.com/org/test",
            short_description="test",
            primary_category="tools",
            publisher_id="pub-1",
        )
        TrustMachine.transition(listing, TrustState.AUDITED, "ok")
        TrustMachine.transition(listing, TrustState.VERIFIED, "ok")
        with pytest.raises(TrustTransitionError, match="fingerprint"):
            TrustMachine.transition(listing, TrustState.SIGNED, "no signature")

    def test_transition_verified_to_signed_with_signature(self):
        listing = Listing(
            canonical_name="org/test",
            canonical_source_url="https://github.com/org/test",
            short_description="test",
            primary_category="tools",
            publisher_id="pub-1",
            fingerprint="sha256:abc123",
            signature_value="sig-xyz",
        )
        TrustMachine.transition(listing, TrustState.AUDITED, "ok")
        TrustMachine.transition(listing, TrustState.VERIFIED, "ok")
        result = TrustMachine.transition(listing, TrustState.SIGNED, "signed")
        assert result.trust_state == "signed"

    def test_transition_same_state_raises(self):
        with pytest.raises(TrustTransitionError, match="already in state"):
            TrustMachine.transition(self.listing, TrustState.DISCOVERED, "nop")

    def test_transition_invalid_raises(self):
        with pytest.raises(TrustTransitionError, match="Cannot transition"):
            TrustMachine.transition(self.listing, TrustState.VERIFIED, "skip steps")

    # -- Downgrade transitions --

    def test_downgrade_verified_to_audited(self):
        listing = Listing(
            canonical_name="org/test",
            canonical_source_url="https://github.com/org/test",
            short_description="test",
            primary_category="tools",
            publisher_id="pub-1",
        )
        TrustMachine.transition(listing, TrustState.AUDITED, "ok")
        TrustMachine.transition(listing, TrustState.VERIFIED, "ok")
        result = TrustMachine.transition(listing, TrustState.AUDITED, "revoked")
        assert result.trust_state == "audited"

    def test_downgrade_audited_to_discovered(self):
        TrustMachine.transition(self.listing, TrustState.AUDITED, "ok")
        result = TrustMachine.transition(self.listing, TrustState.DISCOVERED, "invalidated")
        assert result.trust_state == "discovered"

    # -- Full lifecycle --

    def test_full_lifecycle(self):
        listing = Listing(
            canonical_name="org/test",
            canonical_source_url="https://github.com/org/test",
            short_description="test lifecycle",
            primary_category="tools",
            publisher_id="pub-1",
            fingerprint="sha256:abc",
            signature_value="sig-abc",
        )
        TrustMachine.transition(listing, TrustState.AUDITED, "schema ok")
        TrustMachine.transition(listing, TrustState.VERIFIED, "publisher verified")
        TrustMachine.transition(listing, TrustState.SIGNED, "cryptographic sig")
        assert listing.trust_state == "signed"
        assert len(listing.trust_history) == 3

    # -- Entry criteria --

    def test_entry_criteria_audited(self):
        lst = Listing(canonical_name="", trust_state="discovered")
        errors = TrustMachine.validate_entry_criteria(lst, TrustState.AUDITED)
        assert any("canonical_name" in e for e in errors)
        assert any("short_description" in e for e in errors)
        assert any("canonical_source_url" in e for e in errors)

    def test_entry_criteria_verified_requires_publisher(self):
        lst = Listing(trust_state="audited")
        errors = TrustMachine.validate_entry_criteria(lst, TrustState.VERIFIED)
        assert any("publisher_id" in e for e in errors)

    def test_entry_criteria_signed_requires_fingerprint_and_signature(self):
        lst = Listing(trust_state="verified")
        errors = TrustMachine.validate_entry_criteria(lst, TrustState.SIGNED)
        assert any("fingerprint" in e for e in errors)
        assert any("signature_value" in e for e in errors)

    # -- Backward compatibility --

    def test_normalize_legacy_state_indexed(self):
        assert TrustMachine.normalize_legacy_state("indexed") == "audited"

    def test_normalize_legacy_state_claimed(self):
        assert TrustMachine.normalize_legacy_state("claimed") == "verified"

    def test_normalize_legacy_state_passthrough(self):
        assert TrustMachine.normalize_legacy_state("discovered") == "discovered"
        assert TrustMachine.normalize_legacy_state("audited") == "audited"
        assert TrustMachine.normalize_legacy_state("verified") == "verified"
        assert TrustMachine.normalize_legacy_state("signed") == "signed"

    def test_transition_from_legacy_indexed_state(self):
        """A listing with legacy 'indexed' state can transition as if 'audited'."""
        listing = Listing(
            canonical_name="org/legacy",
            canonical_source_url="https://github.com/org/legacy",
            short_description="legacy test",
            primary_category="tools",
            publisher_id="pub-1",
            trust_state="indexed",  # legacy state
        )
        result = TrustMachine.transition(listing, TrustState.VERIFIED, "upgrade from legacy")
        assert result.trust_state == "verified"

    def test_transition_from_legacy_claimed_state(self):
        """A listing with legacy 'claimed' state can transition as if 'verified'."""
        listing = Listing(
            canonical_name="org/legacy2",
            canonical_source_url="https://github.com/org/legacy2",
            short_description="legacy test",
            primary_category="tools",
            publisher_id="pub-1",
            fingerprint="sha256:abc",
            signature_value="sig-xyz",
            trust_state="claimed",  # legacy state
        )
        result = TrustMachine.transition(listing, TrustState.SIGNED, "upgrade from legacy")
        assert result.trust_state == "signed"


class TestListing:
    def test_defaults(self):
        l = Listing()
        assert l.id != ""
        assert l.package_type == "skill"
        assert l.trust_state == "discovered"
        assert l.primary_category == "developer-tools"
        assert l.maturity == "experimental"
        assert l.discovered_at != ""
        assert l.updated_at != ""
        assert l.source_urls == []
        assert l.tags == []
        assert l.target_frameworks == []
        assert l.trust_history == []

    def test_auto_uuid(self):
        l1 = Listing()
        l2 = Listing()
        assert l1.id != l2.id

    def test_to_dict(self):
        l = Listing(canonical_name="a/b", package_type="tool")
        d = l.to_dict()
        assert d["canonical_name"] == "a/b"
        assert d["package_type"] == "tool"
        assert d["trust_state"] == "discovered"

    def test_roundtrip(self):
        l = Listing(
            canonical_name="org/mcp-server",
            package_type="mcp-server",
            canonical_source_url="https://github.com/org/mcp-server",
            short_description="An MCP server",
            tags=["mcp", "server"],
            source_urls=["https://github.com/org/mcp-server"],
            target_frameworks=["opencode"],
        )
        d = l.to_dict()
        l2 = Listing.from_dict(d)
        assert l2.canonical_name == "org/mcp-server"
        assert l2.package_type == "mcp-server"
        assert l2.tags == ["mcp", "server"]
        assert l2.source_urls == ["https://github.com/org/mcp-server"]
        assert l2.target_frameworks == ["opencode"]

    def test_from_dict_json_fields(self):
        data = {
            "id": "abc-123",
            "canonical_name": "x/y",
            "tags": '["tag1", "tag2"]',
            "source_urls": '["https://gh.com/x/y"]',
            "target_frameworks": "[]",
            "trust_history": "[]",
            "mcp_metadata": '{"transport": "stdio"}',
        }
        l = Listing.from_dict(data)
        assert l.tags == ["tag1", "tag2"]
        assert l.source_urls == ["https://gh.com/x/y"]
        assert l.mcp_metadata == {"transport": "stdio"}

    def test_get_mcp_metadata_obj(self):
        l = Listing(mcp_metadata={"transport": "stdio", "runtime": "python"})
        m = l.get_mcp_metadata_obj()
        assert m is not None
        assert m.transport == "stdio"
        assert m.runtime == "python"

    def test_get_mcp_metadata_obj_none(self):
        l = Listing()
        assert l.get_mcp_metadata_obj() is None


class TestMCPClient:
    def test_values(self):
        assert MCPClient.CLAUDE_DESKTOP.value == "claude-desktop"
        assert MCPClient.OPENCODE.value == "opencode"
        assert MCPClient.GENERIC.value == "generic-mcp-client"


class TestMCPMetadata:
    def test_defaults(self):
        m = MCPMetadata()
        assert m.transport == "stdio"
        assert m.hosted is False
        assert m.supported_clients == []

    def test_roundtrip(self):
        m = MCPMetadata(
            transport="http",
            runtime="python",
            supported_clients=["opencode", "cursor"],
        )
        d = m.to_dict()
        m2 = MCPMetadata.from_dict(d)
        assert m2.transport == "http"
        assert m2.supported_clients == ["opencode", "cursor"]

    def test_from_dict_none(self):
        m = MCPMetadata.from_dict(None)
        assert m.transport == "stdio"

    def test_to_json(self):
        m = MCPMetadata(transport="sse")
        j = m.to_json()
        assert '"transport": "sse"' in j

    def test_from_json(self):
        m = MCPMetadata.from_json('{"transport": "sse", "runtime": "node"}')
        assert m.transport == "sse"
        assert m.runtime == "node"

    def test_from_json_empty(self):
        m = MCPMetadata.from_json("")
        assert m.transport == "stdio"


class TestTrustTransition:
    def test_defaults(self):
        t = TrustTransition(from_state="discovered", to_state="audited")
        assert t.timestamp != ""
        assert t.triggered_by == "system"
        assert t.reason == ""

    def test_roundtrip(self):
        t = TrustTransition(
            from_state="discovered",
            to_state="audited",
            reason="Schema validated",
            triggered_by="crawler",
        )
        d = t.to_dict()
        t2 = TrustTransition.from_dict(d)
        assert t2.from_state == "discovered"
        assert t2.to_state == "audited"
        assert t2.reason == "Schema validated"
        assert t2.triggered_by == "crawler"


class TestPublisher:
    def test_defaults(self):
        p = Publisher()
        assert p.id != ""
        assert p.verified is False
        assert p.primary_proof_type == "account"

    def test_roundtrip(self):
        p = Publisher(
            display_name="Test Corp",
            slug="test-corp",
            verified=True,
            verification_method="dns",
        )
        d = p.to_dict()
        p2 = Publisher.from_dict(d)
        assert p2.display_name == "Test Corp"
        assert p2.verified is True


class TestCategory:
    def test_roundtrip(self):
        c = Category(slug="ai-ml", display_name="AI & ML", sort_order=5)
        d = c.to_dict()
        c2 = Category.from_dict(d)
        assert c2.slug == "ai-ml"
        assert c2.display_name == "AI & ML"
        assert c2.sort_order == 5


class TestSubcategory:
    def test_roundtrip(self):
        s = Subcategory(slug="llm-tools", category_slug="ai-ml", display_name="LLM Tools")
        d = s.to_dict()
        s2 = Subcategory.from_dict(d)
        assert s2.slug == "llm-tools"
        assert s2.category_slug == "ai-ml"


class TestTagCount:
    def test_roundtrip(self):
        t = TagCount(tag="mcp", count=42)
        d = t.to_dict()
        t2 = TagCount.from_dict(d)
        assert t2.tag == "mcp"
        assert t2.count == 42


class TestCollection:
    def test_roundtrip(self):
        c = Collection(
            slug="featured-mcp",
            display_name="Featured MCP Servers",
            listing_ids=["id-1", "id-2"],
        )
        d = c.to_dict()
        c2 = Collection.from_dict(d)
        assert c2.listing_ids == ["id-1", "id-2"]

    def test_from_dict_json(self):
        c = Collection.from_dict({
            "slug": "test",
            "display_name": "Test",
            "listing_ids": '["a", "b"]',
        })
        assert c.listing_ids == ["a", "b"]


class TestClaimRequest:
    def test_defaults(self):
        c = ClaimRequest(listing_id="l-1", publisher_id="p-1")
        assert c.id != ""
        assert c.status == "pending"
        assert c.submitted_at != ""

    def test_roundtrip(self):
        c = ClaimRequest(
            listing_id="l-1",
            publisher_id="p-1",
            proof_type="dns",
            proof_value="token-abc",
        )
        d = c.to_dict()
        c2 = ClaimRequest.from_dict(d)
        assert c2.proof_type == "dns"


class TestVerificationRecord:
    def test_defaults(self):
        v = VerificationRecord(listing_id="l-1")
        assert v.id != ""
        assert v.result == "pass"
        assert v.verified_at != ""

    def test_roundtrip(self):
        v = VerificationRecord(listing_id="l-1", method="dns-txt")
        d = v.to_dict()
        v2 = VerificationRecord.from_dict(d)
        assert v2.method == "dns-txt"


class TestSearchQuery:
    def test_defaults(self):
        q = SearchQuery()
        assert q.limit == 50
        assert q.offset == 0
        assert q.sort_by == "relevance"

    def test_to_dict_filters_none(self):
        q = SearchQuery(text="mcp", limit=10)
        d = q.to_dict()
        assert d["text"] == "mcp"
        assert d["limit"] == 10
        assert "package_type" not in d

    def test_from_dict(self):
        q = SearchQuery.from_dict({"text": "mcp", "limit": 10})
        assert q.text == "mcp"
        assert q.limit == 10
        assert q.package_type is None
