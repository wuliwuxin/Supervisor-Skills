---
name: supervisor
description: >-
  Routes research supervision requests through the Supervisor-Skills collection,
  connecting idea evaluation, literature research, paper planning, drafting,
  polishing, figure design, submission review, and rebuttal guidance. Use when
  the user requests Supervisor guidance, an AI research supervisor, or help
  choosing and completing the next step in a research or writing project.
license: CC-BY-NC-SA-4.0
---

# Supervisor

Choose the relevant skill from the user's materials, research stage, and requested
deliverable. Read its complete `SKILL.md`, then its references as needed. For a
single task, go directly to that skill; connect stages only when the task requires
them. Honor the user's scope, tools, and existing decisions. Respond in their language.

| Task | Skill |
| --- | --- |
| Literature landscape and gaps | [deep-research](../deep-research/SKILL.md) |
| Idea value, novelty, feasibility | [idea-evaluator](../idea-evaluator/SKILL.md) |
| Technical paper contributions and argument | [tech-paper-template](../tech-paper-template/SKILL.md) |
| Benchmark / evaluation projects and papers | [benchmark-paper-template](../benchmark-paper-template/SKILL.md) |
| Introduction prose | [intro-drafter](../intro-drafter/SKILL.md) |
| Other sections or full manuscript | [paper-writer](../paper-writer/SKILL.md) |
| Polish, translate, or remove AI tone | [paper-polish](../paper-polish/SKILL.md) |
| Motivation, overview, and experimental figures | [figure-designer](../figure-designer/SKILL.md) |
| Submission review and revision priorities | [pre-submission-reviewer](../pre-submission-reviewer/SKILL.md) |
| Human-AI collaboration and tool selection | [vibe-research-workflow](../vibe-research-workflow/SKILL.md) |
| Respond to reviewer concerns | [rebuttal-guidance](../../others/rebuttal-guidance/SKILL.md) |
| Reconstruct editable Draw.io diagrams | [drawio-reconstruction](../../others/drawio-reconstruction/SKILL.md) |

For teaching and case analysis, consult the [Chinese handbook](../../handbook/)
or [English handbook](../../handbook-en/); the [project overview](../../README.md)
lists the chapters. Load only relevant chapters. Older handbook prescriptions
are historical advice, not additional global rules: use the current skill's
evidence-based drafting and translation workflow and the user's explicit request.

## Cross-harness execution

Use the host's available search, filesystem, execution, image viewing, rendering,
and delegation tools. Interpret tool names such as `Read` by capability. Work
serially when delegation is unavailable. Report missing retrieval or rendering
capabilities and complete supported work without claiming unperformed verification.
These skills do not supply API keys or model services.

The global installer prefixes child skills with `supervisor-` to avoid collisions.
Use `supervisor-skills list`, `supervisor-skills path <name>`, and
`supervisor-skills show <name>` when native discovery is unavailable. Cross-skill
resource paths resolve from the collection's skill directory, not the project.
For assistants without local file access, export the selected child skill with
`supervisor-skills export <name>` and provide its text and references as context.
Exported text does not grant tools or include binary assets.

Source: HKUST DIAL / Yuyu Luo's [Supervisor-Skills](https://github.com/HKUSTDial/Supervisor-Skills).
This router is a local addition. Preserve CC BY-NC-SA 4.0 attribution and the
Draw.io extension's MIT license.
