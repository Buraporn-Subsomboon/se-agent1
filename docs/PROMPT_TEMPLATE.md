# Structured Prompt Template (8 sections)

Save each prompt as its own `.md` file in `prompts/`. The router discovers it automatically. Use these
exact headings (numbers optional). The router picks an agent by reading its **Role** and **Task/Objective**,
so write those two clearly. Agents don't know other agents exist: don't reference them.

Placeholders the router fills:
- `[PROJECT_DESCRIPTION]` (or any name containing DESCRIPTION) → your brief
- `[INTERACTION_MODE]` → "autonomous"
- any other `[NAME]` → "UNKNOWN" unless an earlier agent produced it; earlier outputs are passed in as prior work.
  Prefer to ask for the information in **Context** in words rather than relying on many placeholders.

````markdown
## 1. Role
You are a <specific expert>. You prioritize, in order: (1) <...> (2) <...> (3) <...>.

## 2. Context
Project description:
[PROJECT_DESCRIPTION]

<What the agent needs to know: the course phase, the Sommerville chapter it draws on, the audience.>

## 3. Task/Objective
<One paragraph: exactly what to produce, and what "done" looks like.>

## 4. Requirements
- <What the output MUST contain, as a checklist>

## 5. Constraints
- <What it must NOT do: length limits, no invented facts, no extra features, technology limits>

## 6. Process
1. <Step the agent follows>
2. <...>

## 7. Output Format
<Headings/tables/files. If you want code files, say: "one fenced block per file, first line a comment with the file name, e.g. // app.js". >

## 8. Verification
Before finishing, check: <list of self-checks, e.g., every requirement traced to a test; no contradictions; nothing outside scope>. State any assumptions.
````

## Review checklist for your prompts (Prompt engineer)
- [ ] Role and Task are specific enough that the Router can tell this prompt from the others.
- [ ] The Output Format can be checked by a human in five minutes.
- [ ] Constraints explicitly stop scope creep ("do not add features not in the brief").
- [ ] Verification asks the agent to list assumptions and gaps, not just say "done".
- [ ] No secrets, personal data, or instructor-only material inside.
- [ ] Tested on `examples/water-tracker.md` with the cheap model before the team uses it on the real brief.

## Suggested team prompt set (write your own; these are topics, not text)
| File (suggested) | Sommerville | Produces |
|---|---|---|
| `requirements_engineer.md` | Ch 4 | numbered, testable requirements + ambiguity list |
| `system_modeler.md` | Ch 5 | context, use-case, class, sequence/state models |
| `architect.md` | Ch 6 | pattern choice, decisions log, NFR trade-offs |
| `implementer.md` | Ch 7 | code files, design-pattern notes |
| `tester.md` | Ch 8 | test plan, tests mapped to requirements |
| `evolution_planner.md` | Ch 9 | change impact analysis |
| `assembler.md` (optional) | Ch 7 | combine earlier work into one working deliverable |

Tip: a model that "finishes" every step can still hand back pieces that don't fit together. The optional
assembler agent exists to produce one runnable result, and your human integration step checks it.
