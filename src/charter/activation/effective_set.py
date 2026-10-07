"""The one public effective-set seam (FR-015, #4400, C-007).

Answers a single question: *what is effective for an activation key while that
key is absent?* Every absent-key reasoner asks it here — the interview
promotion, the org-charter ``required_*`` union, the ``m_unify_charter_activation``
upgrade step, the resynthesis preflight and ``ActiveCharterManager.activate`` —
instead of reading a shipped id list, which is a strict subset of the offering
and would narrow the set on promotion.

The answer spans the whole offering:

* the built-in layer;
* **every** declared org pack (``layer_roots["org"]`` from
  :func:`charter.activation.layer_roots.resolve_layer_roots` is pack #1 only, a
  back-compat contract of that map; this module scans once per declared root);
* the project pack root;
* for every kind except ``directive``, the keys of the activation-aware
  service's own mapping, so an artifact whose declared ``id:`` differs from its
  file stem is emitted in the spelling the activation filter compares against.
  Directives stay in config-stem spelling: the directive getter resolves stems
  through the shared vocabulary, and emitting ``DIRECTIVE_NNN`` would rewrite a
  project's ``activated_directives`` into a second spelling.

It **fails closed**: when the org-pack registry is malformed, a declared org
pack root is missing or cannot be scanned, or the service cannot be built, the
result is ``resolved=False`` with the reason, never a partial set. The same
holds for an empty set while built-in artifacts of the kind ship. Callers leave
such a key absent and report it. ``skill`` (absent key means "org-required
only") is never resolvable here, so a careless caller cannot seed the whole
skill catalogue; ``mission-type`` is an activation ledger, not a corpus, and is
refused with :class:`ValueError`.

Import direction: this module imports :mod:`charter.activation.pack_manager` at
module scope; ``pack_manager`` imports this module lazily inside
``ActiveCharterManager.activate`` (one direction only). The result type,
:class:`~charter.activation.activation_engine.EffectiveSet`, lives in the engine
that consumes it, so this module exposes exactly one public function.
"""

from __future__ import annotations

import logging
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from charter.activation.activation_engine import EffectiveSet
from charter.activation.invocation_context import ProjectContext
from charter.activation.layer_roots import resolve_layer_roots
from charter.activation.pack_manager import YAML_KEY_MAP, ActiveCharterManager
from charter.offering.artifact_kinds import MISSION_TYPE_TOKEN, ArtifactKind
from charter.offering.drg.org_pack_config import load_pack_registry
from charter.offering.pack_paths import built_in_dir

__all__ = ["resolve_effective_sets"]

logger = logging.getLogger(__name__)

_DIRECTIVE = ArtifactKind.DIRECTIVE.operator_token
_REQUIRED_ONLY = "kind is required-only: an absent key puts only org-required entries in force"


class _UnresolvableError(Exception):
    """The offering for this repository cannot be determined (fail closed)."""


@dataclass(frozen=True)
class _Offering:
    """The layer roots and service one resolution pass reads, loaded once."""

    layer_roots: dict[str, Path]
    org_roots: tuple[Path, ...]
    service: Any


def _token_for(yaml_key: str) -> str:
    """Return the kind operator token for *yaml_key*; refuse unknown keys and ``mission-type``."""
    for token, key in YAML_KEY_MAP.items():
        if key == yaml_key:
            if token == MISSION_TYPE_TOKEN:
                raise ValueError(f"{yaml_key!r} is an activation ledger, not a corpus; it has no effective set.")
            return token
    raise ValueError(f"Unknown activation key {yaml_key!r}. Valid keys: {sorted(YAML_KEY_MAP.values())}")


def _declared_org_roots(repo_root: Path) -> tuple[Path, ...]:
    """Every declared org pack root, in declaration order; a missing one is unresolvable."""
    try:
        packs = load_pack_registry(repo_root, quiet=True, strict=True).packs
        roots = tuple(pack.effective_root(repo_root) for pack in packs)
    except ValueError as exc:
        raise _UnresolvableError(f"the org pack registry cannot be read: {exc}") from exc
    for root in roots:
        if not root.is_dir():
            raise _UnresolvableError(f"declared org pack root {root} is not a directory")
    return roots


def _load_offering(repo_root: Path, *, with_service: bool) -> _Offering:
    """Load the roots (and, when needed, the service) once for every requested key."""
    org_roots = _declared_org_roots(repo_root)
    try:
        layer_roots = resolve_layer_roots(repo_root)
    except Exception as exc:
        raise _UnresolvableError(f"the layer roots cannot be resolved: {exc}") from exc
    service: Any = None
    if with_service:
        from charter.activation.doctrine_service_builder import build_activation_aware_doctrine_service

        try:
            service = build_activation_aware_doctrine_service(repo_root)
        except Exception as exc:
            raise _UnresolvableError(f"the doctrine service cannot be built: {exc}") from exc
    return _Offering(layer_roots=layer_roots, org_roots=org_roots, service=service)


def _scanned_ids(offering: _Offering, ctx: ProjectContext, token: str) -> set[str]:
    """``list_available`` over the built-in and project layers and each declared org root."""
    manager = ActiveCharterManager()
    base = {layer: root for layer, root in offering.layer_roots.items() if layer != "org"}
    ids = set(manager.list_available(ctx, token, layer_roots=base))
    for org_root in offering.org_roots:
        ids.update(manager.list_available(ctx, token, layer_roots={**base, "org": org_root}))
    return ids


def _service_ids(offering: _Offering, yaml_key: str) -> set[str]:
    """The keys of the service mapping for *yaml_key* (the filter's own spelling)."""
    mapping = getattr(offering.service, yaml_key.removeprefix("activated_"), None)
    if not isinstance(mapping, Mapping):
        return set()
    return {str(key) for key in mapping}


def _built_in_ships(kind: ArtifactKind) -> bool:
    """Whether the built-in pack ships any artifact file of *kind*."""
    if not kind.has_built_in_content_dir:
        return False
    directory = built_in_dir(kind)
    return directory.is_dir() and any(path.is_file() for path in directory.rglob("*.yaml"))


def _resolve_one(offering: _Offering, ctx: ProjectContext, token: str, yaml_key: str) -> EffectiveSet:
    """Resolve one key against an already loaded offering."""
    try:
        ids = _scanned_ids(offering, ctx, token)
        if token != _DIRECTIVE:
            ids.update(_service_ids(offering, yaml_key))
    except Exception as exc:
        logger.debug("effective set for %r unresolved: %s", yaml_key, exc)
        return EffectiveSet(kind=token, yaml_key=yaml_key, resolved=False, reason=f"an artifact layer cannot be scanned: {exc}")
    kind = ArtifactKind.from_operator_token(token)
    if not ids and _built_in_ships(kind):
        return EffectiveSet(kind=token, yaml_key=yaml_key, resolved=False, reason=f"empty effective set while built-in artifacts of {token} ship")
    return EffectiveSet(kind=token, yaml_key=yaml_key, ids=frozenset(ids))


def resolve_effective_sets(repo_root: Path, yaml_keys: Iterable[str]) -> dict[str, EffectiveSet]:
    """Return what is effective for each of *yaml_keys* while that key is absent.

    Parameters
    ----------
    repo_root:
        The repository root (contains ``.kittify/``).
    yaml_keys:
        Activation keys such as ``"activated_procedures"``. Duplicates are
        resolved once. The roots and the doctrine service are loaded once for
        all keys.

    Returns
    -------
    dict[str, EffectiveSet]
        One entry per key. ``resolved=False`` (with ``reason``) means the caller
        must leave the key absent and report it; never write a bare list.

    Raises
    ------
    ValueError
        For an unknown key or ``mission_type_activations`` (not a corpus).
    """
    tokens = {key: _token_for(key) for key in dict.fromkeys(yaml_keys)}
    results: dict[str, EffectiveSet] = {}
    pending: dict[str, str] = {}
    for key, token in tokens.items():
        if ArtifactKind.from_operator_token(token).effective_when_absent == "required":
            results[key] = EffectiveSet(kind=token, yaml_key=key, resolved=False, reason=_REQUIRED_ONLY)
        else:
            pending[key] = token
    if not pending:
        return results
    try:
        offering = _load_offering(repo_root, with_service=any(token != _DIRECTIVE for token in pending.values()))
    except _UnresolvableError as exc:
        logger.debug("effective sets for %s unresolved: %s", sorted(pending), exc)
        results.update({key: EffectiveSet(kind=token, yaml_key=key, resolved=False, reason=str(exc)) for key, token in pending.items()})
        return results
    ctx = ProjectContext(repo_root=repo_root)
    results.update({key: _resolve_one(offering, ctx, token, key) for key, token in pending.items()})
    return results
