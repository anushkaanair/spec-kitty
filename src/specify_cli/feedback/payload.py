"""Allowlisted Feedback Submission payload builder.

The only place raw survey input becomes a wire payload. Emits exactly the
keys named in ``contracts/feedback-submission.schema.json`` and never
includes repository, mission, branch, user, host, or credential data.
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from typing import Literal

from specify_cli.distribution.profile import resolve_distribution_profile
from specify_cli.feedback.models import Harness, Rating, SurveyAnswers, SurveyTrigger
from specify_cli.version_utils import get_version

__all__ = [
    "ALLOWED_KEYS",
    "COMMENT_MAX_LENGTH",
    "ContextFields",
    "EMAIL_MAX_LENGTH",
    "OsFamily",
    "SUBMISSION_FORMAT_VERSION",
    "build_submission",
    "collect_context",
    "normalize_comment",
    "parse_email",
    "parse_rating",
]

SUBMISSION_FORMAT_VERSION = 1
COMMENT_MAX_LENGTH = 2000
EMAIL_MAX_LENGTH = 254

ALLOWED_KEYS: frozenset[str] = frozenset(
    {
        "submission_format_version",
        "rating",
        "comment",
        "email",
        "spec_kitty_version",
        "distribution",
        "trigger",
        "harness",
        "os",
        "mission_type",
    }
)

OsFamily = Literal["linux", "darwin", "windows", "other"]

_EMAIL_SHAPE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_DIGIT_RATING = re.compile(r"^[1-5]$")


@dataclass(frozen=True)
class ContextFields:
    """Non-answer context attached to every Feedback Submission."""

    spec_kitty_version: str
    distribution: str
    trigger: SurveyTrigger
    harness: Harness
    os: OsFamily
    mission_type: str | None


def parse_rating(raw: str | int) -> Rating | None:
    """Parse a 1–5 rating from a string or int. Rejects bools and floats."""
    if isinstance(raw, bool):
        return None
    if isinstance(raw, int):
        try:
            return Rating(raw)
        except ValueError:
            return None
    if isinstance(raw, str) and _DIGIT_RATING.fullmatch(raw):
        return Rating(int(raw))
    return None


def normalize_comment(raw: str | None) -> tuple[str | None, bool]:
    """Strip and cap a comment at :data:`COMMENT_MAX_LENGTH` characters.

    Returns ``(text, truncated)``. Blank input becomes ``(None, False)``.
    """
    if raw is None:
        return None, False
    text = raw.strip()
    if not text:
        return None, False
    if len(text) <= COMMENT_MAX_LENGTH:
        return text, False
    return text[:COMMENT_MAX_LENGTH], True


def parse_email(raw: str | None) -> tuple[str | None, bool]:
    """Validate an optional email.

    Returns ``(value, ok)``:

    * blank / ``None`` → ``(None, True)`` (omit the field)
    * valid shape and length → ``(value, True)``
    * malformed → ``(None, False)`` (caller should re-ask)
    """
    if raw is None:
        return None, True
    value = raw.strip()
    if not value:
        return None, True
    if len(value) > EMAIL_MAX_LENGTH:
        return None, False
    if _EMAIL_SHAPE.fullmatch(value) is None:
        return None, False
    return value, True


def collect_context(
    trigger: SurveyTrigger,
    harness: Harness,
    mission_type: str | None,
) -> ContextFields:
    """Assemble context from the installed CLI version and distribution profile."""
    profile = resolve_distribution_profile()
    return ContextFields(
        spec_kitty_version=get_version(),
        distribution=profile.package_name,
        trigger=trigger,
        harness=harness,
        os=_os_family(sys.platform),
        mission_type=mission_type,
    )


def build_submission(answers: SurveyAnswers, context: ContextFields) -> dict[str, object]:
    """Build the allowlisted wire payload. Omits ``email`` when ``None``."""
    result: dict[str, object] = {
        "submission_format_version": SUBMISSION_FORMAT_VERSION,
        "rating": int(answers.rating),
        "comment": answers.comment,
        "spec_kitty_version": context.spec_kitty_version,
        "distribution": context.distribution,
        "trigger": context.trigger.value,
        "harness": str(context.harness),
        "os": context.os,
        "mission_type": context.mission_type,
    }
    if answers.email is not None:
        result["email"] = answers.email
    assert set(result) <= ALLOWED_KEYS, f"payload keys outside allowlist: {set(result) - ALLOWED_KEYS}"
    return result


def _os_family(platform: str) -> OsFamily:
    if platform.startswith("linux"):
        return "linux"
    if platform == "darwin":
        return "darwin"
    if platform.startswith("win"):
        return "windows"
    return "other"
