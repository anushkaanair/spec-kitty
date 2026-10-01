---
title: Give Feedback on Spec Kitty
description: 'How to answer, skip, or turn off the optional Spec Kitty feedback survey, give feedback on demand, see exactly what is sent, and check or override where it goes.'
doc_status: active
updated: '2026-10-01'
type: how-to
audience: docs/context/audience/external/project-owner.md
related:
- docs/context/feedback.md
- docs/api/environment-variables.md
- docs/api/configuration.md
---
# Give Feedback on Spec Kitty

This guide is for you, the person using Spec Kitty, if you want to know when it
may ask for feedback, how to say no, and what happens to your answer. The survey
is optional and anonymous. Nothing is sent unless you answer "Send feedback?"
with yes. The terms used here are defined in [Context: Feedback](../../../context/feedback.md).

## When you will see the survey

Spec Kitty may offer a short survey at three points:

- when planning is complete,
- when a mission ends (after lanes are consolidated),
- when an Op is closed.

Rules that always apply:

- At most one offer per week, across all three points.
- Never in CI and never in a non-interactive terminal.
- Never at all unless a feedback endpoint is configured. The upstream build
  ships none, so the automatic survey is dormant until you or your
  distribution configure one (see [Where it goes](#where-it-goes)).

**Known limitation.** Spec Kitty cannot tell whether an agent session has a
person watching. In agent harnesses, it relies on the agent to offer the survey
only when a human is in the loop. If your agent offers the survey when you did
not expect it, choose "skip" or "don't ask again", or run
`spec-kitty feedback --prompts off`.

## Answer, skip, or turn it off

The survey asks, in order: a rating from 1 to 5, "What would you change?"
(optional), an email (optional), and "Send feedback?".

- **Skip**: leave the rating empty (press Enter). Nothing is sent, and you may be
  asked again after the weekly limit.
- **Don't ask again**: type `never` at the rating (or choose it in your agent).
  Automatic prompts stop.
- **Turn automatic prompts off or on** at any time:

  ```bash
  spec-kitty feedback --prompts off
  spec-kitty feedback --prompts on
  ```

## Give feedback any time

```bash
spec-kitty feedback
```

This works in a terminal whenever a feedback endpoint is configured, and
ignores the weekly limit. It asks the same questions. In a non-interactive
terminal, or with no endpoint configured, it asks nothing and tells you why.

## What is sent

Only after you confirm, one message is sent with these fields:

- `submission_format_version`
- `rating` (1 to 5)
- `comment` (up to 2000 characters, only if you typed one)
- `email` (only if you typed one)
- `spec_kitty_version`
- `distribution`
- `trigger` (`planning_complete`, `mission_end`, `op_close`, or `on_demand`)
- `harness` (`cli`, a supported agent key, or `other`)
- `os` (`linux`, `darwin`, `windows`, or `other`)
- `mission_type` (the kind of mission, such as `software-dev`, never its name; `null` when there is none)

**Never sent:** repository, mission name, branch, user or host identity, file
paths, or credentials. No credentials header is attached to the request. The
email is included only if you type it.

## Where it goes

See the effective destination, the exact field list, the last-shown date, and
whether automatic prompts are on:

```bash
spec-kitty feedback --status
```

To override the destination, use either of these (the environment variable wins):

- Set `SPEC_KITTY_FEEDBACK_URL` in your shell.
- Set `endpoint_override` in `feedback.json` in your user config directory.

The address must use HTTPS. The one exception is a loopback address such as
`http://127.0.0.1:8765/feedback`, useful for testing. A rejected value does not
fall back to a lower-priority one; `--status` tells you which value was rejected
and why. See the [environment variable reference](../../../api/environment-variables.md#spec_kitty_feedback_url)
and the [`feedback.json` reference](../../../api/configuration.md#feedbackjson-feedback-survey-preferences).

## If the service is down

Nothing visible happens. The survey makes one attempt, never retries, and never
affects your command or its exit status. You still see the thank-you message.
