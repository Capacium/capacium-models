"""Faceted search engine for Exchange listings.

Builds dynamic SQL WHERE clauses from SearchQuery facets.
Supports text search, type/category/trust/tag/publisher/mcp-client filtering,
sorting, and pagination.
"""

import sqlite3
from pathlib import Path
from typing import List, Optional, Tuple

from .models import Listing, SearchQuery
from .trust import TrustState


class ExchangeSearch:

    def __init__(self, db_path: Optional[Path] = None):
        if db_path is None:
            db_path = Path.home() / ".capacium" / "registry.db"
        self.db_path = db_path

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def search(self, query: SearchQuery) -> Tuple[List[Listing], int]:
        conditions = []
        params = []

        if query.text:
            conditions.append(
                "(canonical_name LIKE ? OR short_description LIKE ? OR long_description LIKE ?)"
            )
            like = f"%{query.text}%"
            params.extend([like, like, like])

        if query.kind:
            conditions.append("package_type = ?")
            params.append(query.kind)

        if query.category:
            conditions.append("primary_category = ?")
            params.append(query.category)

        if query.subcategory:
            conditions.append("subcategory = ?")
            params.append(query.subcategory)

        if query.trust_state:
            conditions.append("trust_state = ?")
            params.append(query.trust_state)

        if query.min_trust_state:
            try:
                from .trust import normalize_legacy_state, LEGACY_STATE_MAP
                normalized = normalize_legacy_state(query.min_trust_state)
                min_state = TrustState(normalized)
                valid_states = [
                    s.value for s in TrustState.ordering()
                    if s >= min_state
                ]
                # Include legacy aliases that map to valid states
                for legacy, modern in LEGACY_STATE_MAP.items():
                    if modern in valid_states and legacy not in valid_states:
                        valid_states.append(legacy)
                if valid_states:
                    placeholders = ", ".join("?" for _ in valid_states)
                    conditions.append(f"trust_state IN ({placeholders})")
                    params.extend(valid_states)
            except ValueError:
                pass

        if query.publisher_id:
            conditions.append("publisher_id = ?")
            params.append(query.publisher_id)

        if query.installability:
            conditions.append("installability = ?")
            params.append(query.installability)

        if query.license:
            conditions.append("license = ?")
            params.append(query.license)

        if query.maturity:
            conditions.append("maturity = ?")
            params.append(query.maturity)

        if query.tags:
            for tag in query.tags:
                conditions.append("tags LIKE ?")
                params.append(f'%"{tag}"%')

        if query.mcp_client:
            conditions.append("mcp_metadata LIKE ?")
            params.append(f'%"{query.mcp_client}"%')

        if query.mcp_transport:
            conditions.append("mcp_metadata LIKE ?")
            params.append(f'%"transport": "{query.mcp_transport}"%')

        if query.mcp_hosted is not None:
            hosted_str = "true" if query.mcp_hosted else "false"
            conditions.append("mcp_metadata LIKE ?")
            params.append(f'%"hosted": {hosted_str}%')

        where = ""
        if conditions:
            where = " WHERE " + " AND ".join(conditions)

        conn = self._connect()
        try:
            count_row = conn.execute(
                f"SELECT count(*) FROM listings{where}", params
            ).fetchone()
            total_count = count_row[0] if count_row else 0

            sort_map = {
                "name": "canonical_name ASC",
                "trust": "trust_state ASC",
                "updated": "updated_at DESC",
                "relevance": "updated_at DESC",
            }
            order_by = sort_map.get(query.sort_by, "updated_at DESC")

            full_query = f"SELECT * FROM listings{where} ORDER BY {order_by} LIMIT ? OFFSET ?"
            params.extend([query.limit, query.offset])

            rows = conn.execute(full_query, params).fetchall()
            listings = [Listing.from_dict(dict(row)) for row in rows]

            return listings, total_count
        finally:
            conn.close()

    def search_simple(self, text: str, limit: int = 50) -> List[Listing]:
        q = SearchQuery(text=text, limit=limit)
        listings, _ = self.search(q)
        return listings
