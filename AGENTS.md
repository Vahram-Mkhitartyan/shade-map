# Working on shade app

Read README.md and docs/STATUS.md first, then the relevant architecture and decisions.

- Product name: **shade app**. Repository slug: `shade-map`; Python package: `shadeapp`.
- Preserve separate solar, geometry, data, routing, and presentation responsibilities.
- Keep geometry in local metric East/North/Up coordinates. Never pass geographic
  latitude/longitude into geometric functions. Document units and vector directions.
- Require timezone-aware timestamps. Never silently interpret naive local times.
- Model sunlight as parallel rays with one observer-to-Sun direction vector.
- No Unity, persistent rendered city, or frontend geometry engine is required.
- Test physical invariants and failure cases before increasing geometric complexity.
- Favor deterministic functions. Add spatial indexing only after profiling.
- Missing building heights must eventually have explicit provenance and uncertainty.
- Time-dependent routing must account for arrival time. Do not assume one cheapest
  label per node is sufficient for exposure-dependent objectives.
- Treat route stability and reasonable detours as correctness requirements.
- Keep docs/STATUS.md honest: distinguish implemented, tested, planned, and unknown.
- Update docs/DECISIONS.md when changing a meaningful architectural choice.
- Run `python -m pytest` for core changes. Report checks that could not run.
- Do not add credentials, downloaded city datasets, or environment artifacts to Git.

## Python readability

- Follow PEP 8 formatting and naming, PEP 257 docstrings, and PEP 484 type hints.
- Use four-space indentation, grouped imports, and a 79-character line limit.
- Prefer descriptive names and explicit steps over compressed expressions.
- Explain physical assumptions, units, and non-obvious algorithms in docstrings
  or brief comments. Avoid comments that only repeat the code.
- Document public classes/functions and annotate production function signatures.
- Keep tests readable with descriptive scenario names and simple fixtures.
- Run `python -m ruff format --check .`, `python -m ruff check .`, and
  `python -m pytest` before reporting a Python change complete.
