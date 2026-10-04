# Design decisions — implement-degod-01M44488

Running log of design choices and their rationale (1-3 sentences per dated entry). Seeded at
planning; the authoritative table is research/code-grounding.md §2 (D1–D10).

- 2026-10-04 — D4: the existing tasks patch-liveness gate is widened to the implement family. No new
  gate is added (operator ruling: no new size or ratchet gates; a liveness gate is a correctness
  check, and widening reuses the #5684 precedent).
- 2026-10-04 — D5 / DM 01M4455PBFDASHQ7R9DN5ZQRMW: #5232 is delivered through the write-shaped
  placement seam (option B), following the `mission_record_analysis` precedent. It does not fail
  closed on every context error (option A), which would newly refuse flat missions (INV-7) and the
  unmaterialized-coordination window. Escalation guard: spec C-007.
- 2026-10-04 — D6: #5673 is shaped (pure claim-commit path bundle) but not fixed, because changing
  the claim commit's content is a behaviour change. #5676 lives in `mission_creation.py` and is owned
  by the sibling mission #5634.
