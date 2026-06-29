# capacium-models

> [!NOTE]
> **Public mirror.** The canonical repository is hosted on our self-hosted git.
> This GitHub copy is a read-only mirror kept in sync for visibility and
> installation. Bug reports are welcome via Issues; pull requests are applied
> upstream and synced back here.

Shared domain models for the Capacium ecosystem. Used by `capacium-exchange` and `capacium-crawler`.

## Installation

```bash
pip install capacium-models
```

## Models

| Model | Description |
|-------|-------------|
| `TrustState` | Enum: DISCOVERED → INDEXED → CLAIMED → VERIFIED → AUDITED |
| `TrustMachine` | State machine with VALID_TRANSITIONS, can_transition(), transition() |
| `Listing` | Full listing model (24 fields, auto-UUID, auto-timestamps) |
| `Publisher` | Publisher profile with verification support |
| `MCPClient` | Enum of supported MCP clients |
| `MCPMetadata` | MCP-specific metadata (transport, runtime, auth_model, etc.) |
| `Category` / `Subcategory` / `TagCount` | Taxonomy models |
| `Collection` | Curated collection of listing IDs |
| `ClaimRequest` / `VerificationRecord` | Trust workflow models |
| `SearchQuery` | Faceted search query model (16 fields) |
| `ExchangeSearch` | Faceted search SQL engine |

## Usage

```python
from capacium_models import Listing, TrustState, TrustMachine

# Create a discovered listing
listing = Listing(
    canonical_name="org/my-mcp-server",
    package_type="mcp-server",
    canonical_source_url="https://github.com/org/my-mcp-server",
    short_description="A cool MCP server",
    trust_state=TrustState.DISCOVERED,
)

# Transition through trust states
machine = TrustMachine()
if machine.can_transition(listing.trust_state, TrustState.INDEXED):
    listing = machine.transition(listing, TrustState.INDEXED, "Validated metadata")
```

## Dependencies

Zero runtime dependencies — stdlib only (`dataclasses`, `enum`, `uuid`, `datetime`, `json`, `typing`).

## License

MIT

## Development

Canonical repository: **self-hosted Forgejo** — `git.langevc.com/capacium/capacium-models`
(`git clone git@git.langevc.com:capacium/capacium-models.git`). Develop against the Forgejo
clone and open pull requests there. The GitHub copy is a read-only mirror.
