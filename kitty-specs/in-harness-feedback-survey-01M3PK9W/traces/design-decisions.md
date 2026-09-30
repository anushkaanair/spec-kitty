# Design Decisions — in-harness-feedback-survey-01M3PK9W

Decisions already made (see `research.md` R-01…R-09 and `decisions/`):

- Consent on every submission; the consent step reads only "Send feedback?" (no URL).
- Weekly throttle across all automatic triggers; "shown" is recorded at offer time under a non-blocking machine lock.
- Endpoint precedence: env var > user override > `DistributionProfile.feedback_endpoint` > none (dormant).
- Trigger commands' JSON contracts stay unchanged; agent guidance is appended via the renderer seam.
- Detached child sender with the payload on stdin (never argv or disk); 5 s cap; always silent.
- Preferences live in one hardened `feedback.json` in the user config dir (not the cache dir), built on kernel primitives rather than copies of `NagCache` internals.
- Inline terminal form's first question auto-skips after 30 s, so a pseudo-terminal agent run cannot stall.
