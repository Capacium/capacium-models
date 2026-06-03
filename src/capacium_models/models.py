"""Exchange Core domain models.

Defines the central data structures for the Capacium Exchange:
Listing, MCPMetadata, Publisher, Category, Subcategory, TagCount,
Collection, ClaimRequest, VerificationRecord, TrustTransition, SearchQuery.
"""

import json
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


class MCPClient(Enum):
    CLAUDE_DESKTOP = "claude-desktop"
    CLAUDE_CODE = "claude-code"
    CURSOR = "cursor"
    OPENCODE = "opencode"
    CODEX = "codex"
    CONTINUE = "continue"
    WINDSURF = "windsurf"
    GENERIC = "generic-mcp-client"


@dataclass
class MCPMetadata:
    supported_clients: List[str] = field(default_factory=list)
    transport: str = "stdio"
    runtime: Optional[str] = None
    hosted: bool = False
    auth_model: Optional[str] = None
    required_env_vars: List[str] = field(default_factory=list)
    permission_scopes: List[str] = field(default_factory=list)
    health_endpoint: Optional[str] = None
    health_status: Optional[str] = None
    last_health_check: Optional[str] = None
    setup_command: Optional[str] = None
    documentation_url: Optional[str] = None
    command_examples: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MCPMetadata":
        if data is None:
            return cls()
        known = {f.name for f in cls.__dataclass_fields__.values()}
        filtered = {k: v for k, v in data.items() if k in known}
        return cls(**filtered)

    def to_json(self) -> str:
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, text: str) -> "MCPMetadata":
        if not text:
            return cls()
        return cls.from_dict(json.loads(text))


@dataclass
class TrustTransition:
    from_state: str
    to_state: str
    reason: str = ""
    triggered_by: str = "system"
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TrustTransition":
        return cls(**{k: v for k, v in data.items() if k in {
            "from_state", "to_state", "reason", "triggered_by", "timestamp"
        }})


@dataclass
class Listing:
    id: str = ""
    canonical_name: str = ""
    package_type: str = "skill"

    canonical_source_url: str = ""
    source_urls: List[str] = field(default_factory=list)

    short_description: str = ""
    long_description: str = ""

    trust_state: str = "discovered"
    trust_history: List[Dict[str, Any]] = field(default_factory=list)

    primary_category: str = "developer-tools"
    subcategory: Optional[str] = None
    tags: List[str] = field(default_factory=list)

    publisher_id: Optional[str] = None

    target_frameworks: List[str] = field(default_factory=list)

    installability: str = "local-install"
    install_reference: Optional[str] = None

    license: Optional[str] = None

    maturity: str = "experimental"

    discovered_at: str = ""
    indexed_at: Optional[str] = None
    updated_at: str = ""

    mcp_metadata: Optional[Dict[str, Any]] = None

    installed_capability_id: Optional[int] = None

    # -- GitHub Enrichment --
    github_owner: Optional[str] = None
    github_repo: Optional[str] = None
    github_stars: int = 0
    github_forks: int = 0
    github_watchers: int = 0
    github_license: Optional[str] = None
    github_topics: List[str] = field(default_factory=list)
    github_language: Optional[str] = None
    github_description: Optional[str] = None
    github_homepage: Optional[str] = None
    github_default_branch: Optional[str] = None
    github_created_at: Optional[str] = None
    github_pushed_at: Optional[str] = None
    github_updated_at: Optional[str] = None

    # -- Document Model v2 --
    source_repo: Optional[str] = None      # e.g. "anthropics/skills"
    source_path: str = "/"                  # e.g. "skills/ai-ml/3d-cv-labeling"
    repo_type: str = "unknown"             # single_skill | multi_skill | collection | mcp_server | unknown
    skill_path: Optional[str] = None       # path to SKILL.md within repo
    skill_name: Optional[str] = None       # parsed from SKILL.md frontmatter
    skill_compatibility: Optional[Dict[str, Any]] = None  # from SKILL.md
    skill_metadata: Optional[Dict[str, Any]] = None       # from SKILL.md

    # -- Manifest --
    manifest_raw: Optional[str] = None     # raw capability.yaml content
    manifest_version: Optional[str] = None

    # -- Capability IR --
    capability_ir: Optional[Dict[str, Any]] = None   # framework-agnostic IR (JSONB)
    adaptation_targets: List[str] = field(default_factory=list)  # ["mcp-server", "a2a-agent"]

    # -- Capacium Trust --
    fingerprint: Optional[str] = None
    signature_value: Optional[str] = None
    signature_public_key: Optional[str] = None

    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        if not self.discovered_at:
            self.discovered_at = now
        if not self.updated_at:
            self.updated_at = now

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Listing":
        known = {f.name for f in cls.__dataclass_fields__.values()}
        filtered = {k: v for k, v in data.items() if k in known}
        for list_field in ("source_urls", "tags", "target_frameworks", "trust_history", "github_topics", "adaptation_targets"):
            if list_field in filtered and isinstance(filtered[list_field], str):
                try:
                    filtered[list_field] = json.loads(filtered[list_field])
                except (json.JSONDecodeError, TypeError):
                    filtered[list_field] = []
        for dict_field in ("mcp_metadata", "skill_compatibility", "skill_metadata", "capability_ir"):
            if dict_field in filtered and isinstance(filtered[dict_field], str):
                try:
                    filtered[dict_field] = json.loads(filtered[dict_field])
                except (json.JSONDecodeError, TypeError):
                    filtered[dict_field] = None
        return cls(**filtered)

    def get_mcp_metadata_obj(self) -> Optional[MCPMetadata]:
        if self.mcp_metadata:
            return MCPMetadata.from_dict(self.mcp_metadata)
        return None


@dataclass
class Publisher:
    id: str = ""
    display_name: str = ""
    slug: str = ""
    primary_proof_type: str = "account"
    primary_proof_value: str = ""
    verified: bool = False
    verified_at: Optional[str] = None
    verification_method: Optional[str] = None
    contact_url: Optional[str] = None
    created_at: str = ""
    updated_at: str = ""

    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        if not self.created_at:
            self.created_at = now
        if not self.updated_at:
            self.updated_at = now

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Publisher":
        known = {f.name for f in cls.__dataclass_fields__.values()}
        return cls(**{k: v for k, v in data.items() if k in known})


@dataclass
class Category:
    slug: str = ""
    display_name: str = ""
    description: str = ""
    sort_order: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Category":
        known = {f.name for f in cls.__dataclass_fields__.values()}
        return cls(**{k: v for k, v in data.items() if k in known})


@dataclass
class Subcategory:
    slug: str = ""
    category_slug: str = ""
    display_name: str = ""
    sort_order: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Subcategory":
        known = {f.name for f in cls.__dataclass_fields__.values()}
        return cls(**{k: v for k, v in data.items() if k in known})


@dataclass
class TagCount:
    tag: str = ""
    count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TagCount":
        return cls(tag=data.get("tag", ""), count=data.get("count", 0))


@dataclass
class Collection:
    id: str = ""
    slug: str = ""
    display_name: str = ""
    description: str = ""
    listing_ids: List[str] = field(default_factory=list)
    curated_by: Optional[str] = None
    created_at: str = ""
    updated_at: str = ""

    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        if not self.created_at:
            self.created_at = now
        if not self.updated_at:
            self.updated_at = now

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Collection":
        known = {f.name for f in cls.__dataclass_fields__.values()}
        filtered = {k: v for k, v in data.items() if k in known}
        if "listing_ids" in filtered and isinstance(filtered["listing_ids"], str):
            try:
                filtered["listing_ids"] = json.loads(filtered["listing_ids"])
            except (json.JSONDecodeError, TypeError):
                filtered["listing_ids"] = []
        return cls(**filtered)


@dataclass
class ClaimRequest:
    id: str = ""
    listing_id: str = ""
    publisher_id: str = ""
    proof_type: str = "repo-file"
    proof_value: str = ""
    status: str = "pending"
    submitted_at: str = ""
    reviewed_at: Optional[str] = None
    reviewed_by: Optional[str] = None

    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())
        if not self.submitted_at:
            self.submitted_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ClaimRequest":
        known = {f.name for f in cls.__dataclass_fields__.values()}
        return cls(**{k: v for k, v in data.items() if k in known})


@dataclass
class VerificationRecord:
    id: str = ""
    listing_id: str = ""
    method: str = "repo-token-file"
    result: str = "pass"
    details: str = ""
    verified_at: str = ""
    expires_at: Optional[str] = None
    verifier: str = "system"

    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())
        if not self.verified_at:
            self.verified_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "VerificationRecord":
        known = {f.name for f in cls.__dataclass_fields__.values()}
        return cls(**{k: v for k, v in data.items() if k in known})


@dataclass
class SearchQuery:
    text: Optional[str] = None
    package_type: Optional[str] = None
    category: Optional[str] = None
    subcategory: Optional[str] = None
    tags: Optional[List[str]] = None
    trust_state: Optional[str] = None
    min_trust_state: Optional[str] = None
    publisher_id: Optional[str] = None
    installability: Optional[str] = None
    license: Optional[str] = None
    maturity: Optional[str] = None
    mcp_client: Optional[str] = None
    mcp_transport: Optional[str] = None
    mcp_hosted: Optional[bool] = None
    limit: int = 50
    offset: int = 0
    sort_by: str = "relevance"

    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in asdict(self).items() if v is not None}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SearchQuery":
        known = {f.name for f in cls.__dataclass_fields__.values()}
        return cls(**{k: v for k, v in data.items() if k in known})
