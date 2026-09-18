# Plan: Fix Chinese examples in English README + remove Screenshot sections

- Gate: plan (v2, after plan review fix + user-confirmed scope expansion)
- Work unit: docs bug fix — (a) English `README.md` contains Chinese example prompts; (b) remove Screenshot sections
  and their image files
- Date: 2026-09-18
- Branch: `docs/english-readme-examples` (from `main`)

## Goal / Motivation / Success Signal

- Goals:
  1. Translate the 7 Chinese example prompt blocks in `README.md` into English.
  2. Delete the `## Screenshot` section from `README.md` (L22-25) and the `## 运行截图` section from `README.zh.md`
     (L20-23).
  3. Delete `working.png` and `working-2.png` from the repository.
- Motivation: the English README targets English-speaking users; Chinese example prompts are copy-paste residue from
  `README.zh.md`. The screenshot sections are no longer wanted (user decision, 2026-09-18); the images are referenced
  only by those sections (verified: no other references in repo).
- Success signals:
  1. All example prompt blocks in `README.md` are English; the only remaining CJK in `README.md` is the intentional
     language-switcher link on line 3 (`English | [中文](README.zh.md)`).
  2. `$skill` names, file paths, agent IDs, commands, and code-fence info strings are preserved verbatim.
  3. Neither README contains a Screenshot/运行截图 section; `working.png` and `working-2.png` no longer exist in the
     repo; no file references them.
  4. No other content changes in either README (prose, tables, headings, commands stay byte-identical).

## Non-goals / Scope Boundary

- No changes to `skills/`, `scripts/`, or any file other than `README.md`, `README.zh.md`, and the two deleted images.
- No rewriting of existing prose beyond the confirmed deletions/translations.
- No README sync/validation tooling, no CI check, no structural reorganization.

## Goal Alignment

| Slice / decision | Confirmed goal or success signal |
| --- | --- |
| Slice 1: translate the 7 example blocks | Goal 1, success signals 1–2 |
| Slice 1: delete Screenshot sections + images | Goals 2–3, success signal 3 |
| Validation: scoped CJK assertion, diff review, reference grep | Success signals 1–4 |

No design document for this work unit; user requirement + direct code evidence is the basis.

## First-principles Judgment and Direct Code Evidence

The English and Chinese READMEs are parallel documents. `README.zh.md` correctly keeps example prompts in Chinese;
`README.md` contains the same Chinese text, which is only correct in the zh file. The Screenshot sections exist in both
files and are the only referencers of the two images (verified via `grep -rn 'working' --include='*.md' --include='*.sh'
--include='*.zsh' --include='*.yaml' .` → only README hits). The fix is translation plus deletion — no behavior,
contract, or schema is involved.

Affected blocks (verified by reading `README.md` and grepping CJK):

1. `README.md:41-42` — Demo example.
2. `README.md:206-209` — Gateflow standalone example.
3. `README.md:215-218` — Gateflow + tmux-agents example.
4. `README.md:224-227` — Gateflow + sub-agents example.
5. `README.md:243-248` — Phaseflow standalone example.
6. `README.md:254-259` — Phaseflow + tmux-agents example.
7. `README.md:265-268` — Phaseflow + sub-agents example.

Deletions:

- `README.md:22-25` — `## Screenshot` + two image lines.
- `README.zh.md:20-23` — `## 运行截图` + two image lines.
- `working.png`, `working-2.png` — `git rm`.

Note: after deleting `README.md:22-25`, the language-switcher line moves from line 3 to... unchanged (deletion is
below line 3? No — Screenshot is at L22-25, below line 3, so line 3 stays line 3). CJK validation anchored to line 3
remains valid.

## Affected Files/Modules

- `README.md`, `README.zh.md`, `working.png` (delete), `working-2.png` (delete).

## Contract/Schema/State-machine/Public-interface Changes

None. Documentation/assets only.

## Implementation Decisions

- Translate example prompt text to natural English matching the surrounding README prose.
- Keep verbatim: `$phaseflow`, `$gateflow`, `$tmux-agents`, `$sub-agents`, `/skill` references, file paths
  (`docs/host/design.md`, `docs/host/issues-implementation-control.md`, `AGENTS.md`), agent IDs
  (`CodexAgent-GPT`, `ClaudeAgent-MiMo`, `ClaudeAgent-DS`, `Codex gpt`, `Claude mimo / ds`), `<work-unit>` placeholder,
  and ```text code fences.
- Keep line structure inside each block (one translated line per source line) so the diff stays minimal and reviewable.
- `README.md:46-49` ("Equivalent explicit argument form") is already English/args-only — not part of the fix.
- Delete sections with their trailing blank line so no double blank lines remain; images via `git rm`.

## Implementation Slices

Single slice:

- id/name: `slice-1` README example translation + Screenshot removal
- objective: success signals 1–4 all hold
- expected outcome: English examples, no Screenshot sections, no orphan images
- allowed files: `README.md`, `README.zh.md`, `working.png`, `working-2.png`
- prerequisites: none
- exact allowed changes: edit only the 7 example blocks + delete the 2 sections + `git rm` the 2 images; no other lines
- non-goals: everything in Non-goals above
- tests/validation: see below
- completion signal: validation commands pass; stop condition: any change needed outside the listed blocks/sections →
  stop and re-confirm

Rationale for one slice: all changes are one docs increment, reviewed in a single diff; per-block or per-file splits
would be mechanical with gate cost exceeding risk. Well under the ≤3 default.

## Tests/Validation

1. `grep -nP '[\x{4e00}-\x{9fff}]' README.md | grep -v '^3:'` → no output (only the intentional line-3 language
   switcher keeps CJK).
2. `git status --short` / `git diff --stat` → only `README.md`, `README.zh.md` modified; `working.png`,
   `working-2.png` deleted.
3. `git diff README.md README.zh.md` → every changed hunk is inside the 7 example blocks or the 2 deleted sections;
   code fences, `$skill` names, paths, and agent IDs unchanged; no stray double blank lines left by deletions.
4. `grep -rn 'working' . --exclude-dir=.git` → no references to `working.png` / `working-2.png` remain;
   `ls working.png working-2.png` → No such file.
5. `grep -n 'Screenshot\|运行截图' README.md README.zh.md` → no output.
6. `./scripts/validate-skills.sh` → passes (repo-level sanity).

## Docs Decision

This work unit IS a docs fix; the changed READMEs are the artifact. No additional docs updates.

## Risks / Open Questions

- Risk: translation wording could drift from the zh source meaning → mitigated by line-by-line mapping and review gate.
- No open questions.

## Why No Over-design / No Goal Drift

The plan changes only the confirmed blocks/sections/files, with validation limited to proving exactly that. No tooling,
no restructuring, no future-slice work. Out-of-scope discoveries (if any) go to residual risks, not implementation.

## Completion Report Format

- what changed (blocks translated, sections/images deleted)
- validation command outputs
- residual risks
- artifact path
