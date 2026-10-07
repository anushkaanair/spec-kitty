"""Doctrine fetch/pack tooling for spec-kitty org doctrine layer.

This package provides the OrgDoctrineSource protocol and concrete fetch-source
implementations (git, HTTPS/Artifactory bundle, API) plus snapshot management
utilities.

Layer: ``specify_cli`` (depends on ``charter``, ``doctrine``, ``kernel``).

See mission ``layered-doctrine-org-layer-01KRNPEE`` and ADR
``2026-03-27-1`` for the architectural context.
"""

from __future__ import annotations

from .snapshot import fetch_pack, write_snapshot
from .sources import (
    ApiSource,
    FetchResult,
    GitSource,
    HttpsBundleSource,
    OrgDoctrineSource,
)

__all__ = [
    "ApiSource",
    "FetchResult",
    "GitSource",
    "HttpsBundleSource",
    "OrgDoctrineSource",
    "fetch_pack",
    "write_snapshot",
]
