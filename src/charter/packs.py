"""Charter facade for the charter pack model and tooling.

The public door for ``specify_cli`` to the pack model and tooling that live in
:mod:`charter.offering.packs` (mission ``charter-pack-cutover-01M491G6``, FR-010 /
OD-9). Object-identity re-exports only: every name here *is* the offering
object, so no wrapper, alias or shim can drift from it
(``tests/architectural/test_charter_facades_reexport_doctrine.py``).

``specify_cli`` modules import these names from here, never from
``charter.offering.packs.*`` directly, so the runtime -> charter -> offering
boundary (``tests/architectural/test_runtime_charter_doctrine_boundary.py``)
holds without growing its lazy-import baseline (NFR-002).
"""

from __future__ import annotations

from charter.offering.packs.builtin_manifest import (
    builtin_manifest_is_fresh,
    generate_builtin_manifest,
)
from charter.offering.packs.pack_manifest import (
    RECOGNISED_ARTIFACT_DIRS,
    count_snapshot_artifacts,
    safe_urlsplit,
    snapshot_sha256,
    source_fingerprint,
    strip_source_credentials,
    write_pack_manifest,
)

__all__ = [
    "RECOGNISED_ARTIFACT_DIRS",
    "builtin_manifest_is_fresh",
    "count_snapshot_artifacts",
    "generate_builtin_manifest",
    "safe_urlsplit",
    "snapshot_sha256",
    "source_fingerprint",
    "strip_source_credentials",
    "write_pack_manifest",
]
