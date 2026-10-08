"""``spec-kitty doctrine`` command group (deprecated; WP16 deletes it).

Every leaf has a ``charter`` home (mission charter-pack-cutover-01M491G6,
FR-006) and this module only re-registers the same handler objects:

* ``fetch`` / ``new`` / ``validate`` — :mod:`specify_cli.cli.commands.charter.authoring`
* ``org init`` / ``org validate`` — :mod:`specify_cli.cli.commands.charter.org`
* ``pack validate`` / ``pack assemble`` / ``regenerate-graph`` —
  :mod:`specify_cli.cli.commands.charter.pack_tooling`
  (``spec-kitty charter pack validate|assemble|regenerate-graph``)
* ``asset list`` / ``asset path`` — :mod:`specify_cli.cli.commands.charter.pack_asset`
  (``spec-kitty charter pack asset``)
* ``mission-type list`` — replaced by
  ``spec-kitty charter mission-type list --include-inactive``.
"""

from __future__ import annotations

import json
from pathlib import Path

import typer
from rich.table import Table

from specify_cli.cli.commands.charter.authoring import fetch, new, validate
from specify_cli.cli.commands.charter.org import org_app
from specify_cli.cli.commands.charter.pack_asset import asset_app
from specify_cli.cli.commands.charter.pack_tooling import pack_assemble, pack_validate, regenerate_graph
from specify_cli.cli.console import console

__all__ = ["app"]

#: CR-02 (mission ``charter-code-topology-01M152G1`` S4): the deprecation
#: notice printed once per invocation of the ``spec-kitty doctrine`` group
#: (any subcommand). Unlike the CR-01/CR-03/CR-04/CR-07 config/URN-reader
#: shims -- which warn-once *per process* because a hot read path may call
#: the same function many times in one invocation -- a CLI group's own
#: ``@app.callback()`` fires at most once per process by construction (typer
#: invokes it a single time before dispatching to exactly one subcommand),
#: so no additional de-dup gate is needed here.
_DEPRECATION_NOTICE = (
    "`spec-kitty doctrine` is deprecated; use `spec-kitty charter` instead "
    "(mission charter-code-topology-01M152G1, CR-02). This command still "
    "works and delegates to the same implementation. Every command has a "
    "`spec-kitty charter` home: `charter pack regenerate-graph`, "
    "`charter pack validate`, `charter pack assemble`, `charter pack asset` "
    "and `charter mission-type list --include-inactive`."
)


app = typer.Typer(
    name="doctrine",
    help="[DEPRECATED — use `spec-kitty charter`] Manage org-layer doctrine packs (fetch, validate, assemble).",
    no_args_is_help=True,
)


@app.callback()
def _deprecation_warning() -> None:
    """CR-02: emit a one-shot stderr deprecation notice, then delegate.

    Typer/Click always runs a Typer app's own ``@app.callback()`` before
    dispatching to whichever subcommand the operator invoked, so this fires
    for every ``spec-kitty doctrine <anything>`` invocation -- the "callback
    that emits a one-shot stderr deprecation then delegates" CR-02 asks for.
    Prints (not raises): the legacy group must keep working exactly as
    before, it only gains a warning banner.
    """
    typer.secho(_DEPRECATION_NOTICE, fg=typer.colors.YELLOW, err=True)

pack_app = typer.Typer(
    name="pack",
    help="Validate or assemble doctrine packs.",
    no_args_is_help=True,
)
app.add_typer(pack_app, name="pack")

app.add_typer(org_app, name="org")

mission_type_app = typer.Typer(
    name="mission-type",
    help="Mission type commands.",
    no_args_is_help=True,
)
app.add_typer(mission_type_app, name="mission-type")

# WP05 — asset operator surface. Read-only ``asset list`` / ``asset path``
# commands resolve shipped and overlay doctrine assets through
# ``DoctrineService.assets`` (no install — C-002). ``asset_app`` is imported at
# the top of the module; registered here at the WP03 anchor.
app.add_typer(asset_app, name="asset")

# Mission charter-pack-cutover-01M491G6 (FR-006): the handlers live in their
# ``charter`` homes; this group re-registers the same objects until WP16
# deletes it (the #4836 guidance gate compares handler identity).
app.command(name="fetch")(fetch)
app.command(name="regenerate-graph")(regenerate_graph)
pack_app.command(name="validate")(pack_validate)
pack_app.command(name="assemble")(pack_assemble)
app.command(name="new")(new)
app.command(name="validate")(validate)


# ----------------------------------------------------------------------
# mission-type list — enumerate all doctrine-layer mission types (FR-013)
# ----------------------------------------------------------------------

#: Dataclass-free record type for a mission-type row.
class _MissionTypeRow:
    """Lightweight row value object for mission-type list output."""

    __slots__ = ("id", "source_layer", "display_name")

    def __init__(self, id: str, source_layer: str, display_name: str) -> None:  # noqa: A002
        self.id = id
        self.source_layer = source_layer
        self.display_name = display_name


@mission_type_app.command("list")
def mission_type_list(
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Output as JSON.",
    ),
) -> None:
    """List all mission types in the doctrine layer (FR-013).

    Enumerates built-in, org, and project mission types regardless of
    activation state.  The DRG resolution chain applies: built-in →
    org → project.  An org type with the same id shadows the built-in
    type; a project type shadows the org type.

    Use ``spec-kitty charter mission-type list`` to see only types that
    are currently activated for this project.
    """
    # FR-008 (WP07/T018): the full layered roster (built-in -> org ->
    # project, full per-id replacement) IS the built-in -> org -> project
    # shadow chain this docstring already promises -- reach it directly
    # instead of the built-in-only collector, so an id merely *registered*
    # (not activated) in an org/project layer still appears here with its
    # real layer, matching this command's own contract (activation-scoped
    # listing is `charter mission-type list`'s job, not this one's).
    from specify_cli.cli.commands.charter.mission_type import (  # noqa: PLC0415
        mission_type_error_boundary,
        resolve_layered_roster,
        resolve_mission_type_source_layer,
    )

    repo_root = Path.cwd()

    with mission_type_error_boundary(json_output):
        roster = resolve_layered_roster(repo_root)
        rows: list[_MissionTypeRow] = [
            _MissionTypeRow(
                id=mt_id,
                source_layer=resolve_mission_type_source_layer(mt_id, repo_root),
                display_name=mission_type.display_name,
            )
            for mt_id, mission_type in roster.items()
        ]

    # Sort: built-in first (already the case), then by id within each layer.
    rows.sort(key=lambda r: (r.source_layer != "built-in", r.id))

    if json_output:
        data = [
            {"id": r.id, "source_layer": r.source_layer, "display_name": r.display_name}
            for r in rows
        ]
        console.print_json(json.dumps(data))
        return

    if not rows:
        console.print("[yellow]No mission types found.[/yellow]")
        raise typer.Exit(0)

    table = Table(show_header=True, header_style="bold")
    table.add_column("ID", style="cyan")
    table.add_column("SOURCE", style="green")
    table.add_column("DISPLAY NAME")

    for row in rows:
        table.add_row(row.id, row.source_layer, row.display_name)

    console.print(table)
    raise typer.Exit(0)
