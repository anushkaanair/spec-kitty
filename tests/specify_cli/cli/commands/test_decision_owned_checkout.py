"""#5874: real decision lifecycle retains validated owned-checkout authority."""
from __future__ import annotations

import contextlib
import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from specify_cli.cli.commands.agent import app as agent_app
from tests.integration.conftest import OwnedCheckouts, make_owned_checkouts, owned_checkouts, stale_root_copy  # noqa: F401

pytestmark = [pytest.mark.integration, pytest.mark.git_repo]
runner = CliRunner()


def invoke(checkouts: OwnedCheckouts, verb: str, *args: str, explicit: bool = True, handle: str | None = None):
    command = ['decision', verb, *args, '--mission', handle or checkouts.mission_slug]
    if explicit:
        command += ['--owned-checkout', str(checkouts.owned_root)]
    with contextlib.chdir(checkouts.owned_root):
        result = runner.invoke(agent_app, command)
    assert result.exit_code == 0, (result.output, result.exception)
    return json.loads(result.output.strip().splitlines()[-1])


def open_args(key: str):
    return ['--flow', 'specify', '--slot-key', 'specify.discovery', '--input-key', key, '--question', 'Which?', '--actor', 'test']


@pytest.mark.parametrize('explicit', [True, False])
def test_owned_complete_lifecycle(owned_checkouts, explicit):
    c = owned_checkouts
    opened = invoke(c, 'open', *open_args('answer'), explicit=explicit, handle=c.mid8)
    decision_id = opened['decision_id']
    assert invoke(c, 'open', *open_args('answer'), explicit=explicit)['decision_id'] == decision_id
    assert invoke(c, 'list', explicit=explicit)['count'] == 1
    invoke(c, 'resolve', decision_id, '--final-answer', 'yes', explicit=explicit)
    assert invoke(c, 'resolve', decision_id, '--final-answer', 'yes', explicit=explicit)['idempotent']
    assert invoke(c, 'list', explicit=explicit)['decisions'][0]['status'] == 'resolved'
    assert invoke(c, 'verify', explicit=explicit)['status'] == 'clean'
    events = (c.mission_dir / 'status.events.jsonl').read_text().splitlines()
    decisions = [json.loads(line) for line in events if json.loads(line).get('event_type', '').startswith('DecisionPoint')]
    assert len(decisions) == 2
    assert not (c.repository_root / 'kitty-specs' / c.mission_slug).exists()
    assert not list(c.repository_root.glob('.worktrees/*'))


@pytest.mark.parametrize('verb', ['defer', 'cancel'])
def test_owned_terminal_verbs(owned_checkouts, verb):
    c = owned_checkouts
    decision_id = invoke(c, 'open', *open_args(verb))['decision_id']
    result = invoke(c, verb, decision_id, '--rationale', 'later')
    assert result['status'] == {'defer': 'deferred', 'cancel': 'canceled'}[verb]
    assert invoke(c, 'list')['decisions'][0]['status'] == result['status']


def test_owned_dry_run_and_stale_primary(owned_checkouts, stale_root_copy):
    c = owned_checkouts
    root_mission = stale_root_copy()
    sentinel = root_mission / 'spec.md'
    sentinel.write_text('STALE_SENTINEL')
    before = {p.relative_to(root_mission): p.read_bytes() for p in root_mission.rglob('*') if p.is_file()}
    assert invoke(c, 'open', *open_args('dry'), '--dry-run')['decision_id'] == 'DRY_RUN'
    assert not (c.mission_dir / 'decisions').exists()
    invoke(c, 'open', *open_args('actual'))
    assert invoke(c, 'list')['count'] == 1
    assert invoke(c, 'verify')['status'] == 'clean'
    after = {p.relative_to(root_mission): p.read_bytes() for p in root_mission.rglob('*') if p.is_file()}
    assert before == after


@pytest.mark.parametrize('claim', ['repository_root', 'sibling'])
def test_wrong_owned_checkout_refuses_before_writes(owned_checkouts, claim):
    c = owned_checkouts
    with contextlib.chdir(c.owned_root):
        result = runner.invoke(agent_app, ['decision', 'open', *open_args('refuse'), '--mission', c.mission_slug, '--owned-checkout', str(getattr(c, claim))])
    assert result.exit_code != 0
    payload = json.loads(result.output.strip().splitlines()[-1])
    assert payload['code'].startswith('OWNED_') or payload['code'] == 'FEATURE_CONTEXT_UNRESOLVED'
    assert not (c.mission_dir / 'decisions').exists()


@pytest.fixture(scope='session', autouse=True)
def test_venv():
    """These in-process CLI regressions use the synced test environment directly."""
    yield
