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


class TestTrustState:
    def test_values(self):
        assert TrustState.DISCOVERED.value == "discovered"
        assert TrustState.INDEXED.value == "indexed"
        assert TrustState.CLAIMED.value == "claimed"
        assert TrustState.VERIFIED.value == "verified"
        assert TrustState.AUDITED.value == "audited"

    def test_ordering(self):
        ordering = TrustState.ordering()
        assert len(ordering) == 5
        assert ordering[0] == TrustState.DISCOVERED
        assert ordering[-1] == TrustState.AUDITED

    def test_from_string(self):
        assert TrustState("discovered") == TrustState.DISCOVERED
        assert TrustState("verified") == TrustState.VERIFIED

    def test_comparison(self):
        assert TrustState.DISCOVERED < TrustState.INDEXED
        assert TrustState.INDEXED < TrustState.CLAIMED
        assert TrustState.CLAIMED < TrustState.VERIFIED
        assert TrustState.VERIFIED < TrustState.AUDITED
        assert TrustState.VERIFIED >= TrustState.VERIFIED
        assert TrustState.AUDITED >= TrustState.INDEXED


class TestTrustMachine:
    def setup_method(self):
        self.listing = Listing(
            canonical_name="org/test",
            canonical_source_url="https://github.com/org/test",
            short_description="A test",
            primary_category="developer-tools",
            package_type="tool",
        )

    def test_can_transition_valid(self):
        assert TrustMachine.can_transition(TrustState.DISCOVERED, TrustState.INDEXED) is True
        assert TrustMachine.can_transition(TrustState.INDEXED, TrustState.CLAIMED) is True
        assert TrustMachine.can_transition(TrustState.CLAIMED, TrustState.VERIFIED) is True
        assert TrustMachine.can_transition(TrustState.VERIFIED, TrustState.AUDITED) is True

    def test_can_transition_invalid(self):
        assert TrustMachine.can_transition(TrustState.DISCOVERED, TrustState.CLAIMED) is False
        assert TrustMachine.can_transition(TrustState.DISCOVERED, TrustState.VERIFIED) is False
        assert TrustMachine.can_transition(TrustState.CLAIMED, TrustState.INDEXED) is False

    def test_transition_discovered_to_indexed(self):
        result = TrustMachine.transition(
            self.listing, TrustState.INDEXED, "Validated metadata"
        )
        assert result.trust_state == "indexed"
        assert len(result.trust_history) == 1
        assert result.trust_history[0]["from_state"] == "discovered"
        assert result.trust_history[0]["to_state"] == "indexed"
        assert result.indexed_at is not None

    def test_transition_no_publisher(self):
        listing = Listing(
            canonical_name="org/test",
            canonical_source_url="https://github.com/org/test",
            short_description="test",
            primary_category="tools",
        )
        TrustMachine.transition(listing, TrustState.INDEXED, "ok")
        with pytest.raises(Exception):
            TrustMachine.transition(listing, TrustState.CLAIMED, "no publisher")

    def test_transition_with_publisher(self):
        listing = Listing(
            canonical_name="org/test",
            canonical_source_url="https://github.com/org/test",
            short_description="test",
            primary_category="tools",
            publisher_id="pub-1",
        )
        TrustMachine.transition(listing, TrustState.INDEXED, "ok")
        result = TrustMachine.transition(listing, TrustState.CLAIMED, "claimed by publisher")
        assert result.trust_state == "claimed"

    def test_transition_same_state_raises(self):
        with pytest.raises(Exception):
            TrustMachine.transition(self.listing, TrustState.DISCOVERED, "nop")

    def test_transition_invalid_raises(self):
        with pytest.raises(Exception):
            TrustMachine.transition(self.listing, TrustState.VERIFIED, "skip steps")


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
        t = TrustTransition(from_state="discovered", to_state="indexed")
        assert t.timestamp != ""
        assert t.triggered_by == "system"
        assert t.reason == ""

    def test_roundtrip(self):
        t = TrustTransition(
            from_state="discovered",
            to_state="indexed",
            reason="Validated",
            triggered_by="crawler",
        )
        d = t.to_dict()
        t2 = TrustTransition.from_dict(d)
        assert t2.from_state == "discovered"
        assert t2.to_state == "indexed"
        assert t2.reason == "Validated"
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
