---
name: se-agent run request
about: Ask the instructor to run your team's prompts on the class OpenAI account
title: "Run request: <team> – <sprint>"
labels: run-request
---

**Team / sprint:**

**Branch and brief file:** (e.g., `main`, `docs/brief.md`)

**Prompts to run:** (files in `prompts/`)

**Why now / what we expect to get:**

**Checks done (tick all):**
- [ ] `uv run pytest` passes on this branch
- [ ] `uv run python cost_estimate.py` read; expected cost: ____
- [ ] Brief re-read by someone other than the author
- [ ] All prompts follow the 8-section template and are committed
- [ ] No keys or secrets in any committed file

**Model requested:** cheap (`gpt-6-luna`) / stronger (planned demo only — explain)

**Instructor fills in after the run:** output location ____ ; tokens ____ ; cost ____
