# Team Workbook — fill this in as you go

Copy this file into your fork (e.g. `docs/workbook.md`) and complete it. Each section = one Sommerville phase.
Date and initial every entry. Link to the file or Issue instead of pasting long text.

**Team name:** ______  **App:** ______  **Members & roles:** ______________________

---
## 0. Charter (Ch 2, 3)
- Process model chosen and **why** (2–3 sentences): 
- Agile practices we use: ☐ user stories ☐ sprints ☐ daily stand-up ☐ retrospective ☐ pair/peer review ☐ CI tests
- Definition of Done (checklist): 
- How we communicate / meeting times: 
- How we resolve disagreements: 
- AI-use rules we agree to (see Guide §5): 

## 1. Requirements (Ch 4)
| ID | Type (F/NF) | Requirement | Priority | Acceptance test | Owner |
|---|---|---|---|---|---|
| R1 | F | | | | |
| R2 | NF | | | | |
- Stakeholders & what each wants: 
- Ambiguities / questions for the customer: 
- Requirements removed as unnecessary and why: 
- AI contribution note (what the AI drafted, what we changed): 

## 2. Models (Ch 5)
- Context model (inside/outside the system): link
- Use cases / sequence models: link
- Class (structural) model: link
- State (behavioral) model, if any: link
- Inconsistencies found between models and requirements, and how resolved: 

## 3. Architecture (Ch 6)
- Chosen pattern(s): 
- Which non-functional requirements drove it: 
- Alternatives rejected and why: 
- Decisions log:
| # | Decision | Alternatives | Reason | Consequence |
|---|---|---|---|---|
| D1 | | | | |
- Where an AI model/service is used in the app (if at all), its failure fallback, and cost per use: 

## 4. Design & implementation (Ch 7)
- Modules and who owns each: 
- Patterns used and where: 
- Reused code / libraries and their licenses: 
- Branching & review rules (e.g., PR needs 1 approval, tests green): 
- Technical debt we knowingly took on: 

## 5. Testing (Ch 8)
| Requirement | Test (file::name) | Type (unit/component/system/user) | Passes? | Does it fail when code is broken? (tried it) |
|---|---|---|---|---|
| R1 | | | | |
- Test command: `________`   Coverage / what is NOT tested: 
- User testing: who (outside team), what they struggled with: 
- Bugs found after "done" and their cause: 

## 6. Evolution & retrospective (Ch 9)
- Most likely future changes: 
- Change request carried out: what, impact analysis, files touched, how long it took: 
- What would have made the change easier: 

## 7. AI & prompt log
| Run # | Date | Prompts used | Model | Tokens / cost | What was useful | What was wrong / rejected |
|---|---|---|---|---|---|---|
| 1 | | | | | | |
- Changes we made to our prompts after reviewing runs and why: 

## 8. Sprint retrospectives
| Sprint | Went well | Went badly | One improvement we will try |
|---|---|---|---|
| 1 | | | |

## 9. Final demo checklist
☐ App runs from the README steps on a clean machine ☐ Tests pass ☐ Each requirement traced to a test ☐ Every team member can explain the architecture ☐ AI contribution notes complete ☐ No secrets in the repo history
