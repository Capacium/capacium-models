"""Tests for ExchangeSearch."""

import sqlite3
import tempfile
from pathlib import Path

from capacium_models.search import ExchangeSearch
from capacium_models.models import Listing, SearchQuery


def _create_listings_table(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS listings (
            id TEXT PRIMARY KEY,
            canonical_name TEXT,
            package_type TEXT,
            canonical_source_url TEXT,
            source_urls TEXT,
            short_description TEXT,
            long_description TEXT,
            trust_state TEXT,
            trust_history TEXT,
            primary_category TEXT,
            subcategory TEXT,
            tags TEXT,
            publisher_id TEXT,
            target_frameworks TEXT,
            installability TEXT,
            install_reference TEXT,
            license TEXT,
            maturity TEXT,
            discovered_at TEXT,
            indexed_at TEXT,
            updated_at TEXT,
            mcp_metadata TEXT,
            installed_capability_id INTEGER
        )
    """)


def _insert_listing(conn, l: Listing):
    import json
    d = l.to_dict()
    conn.execute("""
        INSERT INTO listings (id, canonical_name, package_type, canonical_source_url,
            short_description, trust_state, primary_category, tags, updated_at, discovered_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        d["id"], d["canonical_name"], d["package_type"], d["canonical_source_url"],
        d["short_description"], d["trust_state"], d["primary_category"],
        json.dumps(d["tags"]) if d["tags"] else "[]",
        d["updated_at"], d["discovered_at"],
    ))
    conn.commit()


class TestExchangeSearch:
    def setup_method(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.tmp.close()
        self.db_path = Path(self.tmp.name)
        conn = sqlite3.connect(str(self.db_path))
        _create_listings_table(conn)
        self._seed(conn)
        conn.close()
        self.search = ExchangeSearch(db_path=self.db_path)

    def teardown_method(self):
        self.tmp.close()
        Path(self.tmp.name).unlink(missing_ok=True)

    def _seed(self, conn):
        listings = [
            Listing(
                canonical_name="org/mcp-server", kind="mcp-server",
                canonical_source_url="https://github.com/org/mcp-server",
                short_description="MCP filesystem server",
                primary_category="mcp-servers",
                trust_state="discovered",
                tags=["mcp", "filesystem"],
            ),
            Listing(
                canonical_name="org/code-review", kind="skill",
                canonical_source_url="https://github.com/org/code-review",
                short_description="AI code review",
                primary_category="developer-tools",
                trust_state="indexed",
                tags=["code-review"],
            ),
        ]
        for l in listings:
            _insert_listing(conn, l)

    def test_text_search(self):
        results, count = self.search.search(SearchQuery(text="MCP"))
        assert count == 1
        assert results[0].canonical_name == "org/mcp-server"

    def test_package_type_filter(self):
        results, count = self.search.search(SearchQuery(kind="skill"))
        assert count == 1
        assert results[0].kind == "skill"

    def test_tag_filter(self):
        results, count = self.search.search(SearchQuery(tags=["code-review"]))
        assert count == 1
        assert results[0].canonical_name == "org/code-review"

    def test_trust_state_filter(self):
        results, count = self.search.search(SearchQuery(trust_state="indexed"))
        assert count == 1
        assert results[0].trust_state == "indexed"

    def test_min_trust_state(self):
        results, count = self.search.search(SearchQuery(min_trust_state="indexed"))
        assert count == 1
        assert results[0].trust_state == "indexed"

    def test_category_filter(self):
        results, count = self.search.search(SearchQuery(category="mcp-servers"))
        assert count == 1
        assert results[0].primary_category == "mcp-servers"

    def test_no_results(self):
        results, count = self.search.search(SearchQuery(text="nonexistent"))
        assert count == 0
        assert results == []

    def test_search_simple(self):
        results = self.search.search_simple("review", limit=10)
        assert len(results) == 1
        assert results[0].canonical_name == "org/code-review"

    def test_pagination(self):
        results, count = self.search.search(SearchQuery(limit=1, offset=0))
        assert count == 2
        assert len(results) == 1
