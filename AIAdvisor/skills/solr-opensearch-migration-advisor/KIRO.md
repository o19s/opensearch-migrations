# Appendix: Packaging This Skill for Kiro

This appendix explains **why Kiro** and **how this skill is packaged** for
[Amazon Kiro](https://kiro.dev/) -- AWS's agentic AI development environment.

If you're already familiar with Cursor, Claude Code, or GitHub Copilot, you'll
find Kiro familiar but philosophically different. Where those tools optimize for
speed of generation, Kiro optimizes for **correctness of generation** through
spec-driven development. That makes it a natural fit for a migration advisor
where accuracy is non-negotiable.

---

## Quick Start (5 minutes)

1. **Install Kiro** -- download from [kiro.dev](https://kiro.dev/) (free during preview)
2. **Open this repo** -- `File > Open Folder` and select the `AIAdvisor/` directory
3. **Kiro auto-discovers the skill** -- the `.kiro/` directory tells Kiro about the
   steering context, the skill, and the schema-assist hook
4. **Try it** -- open Kiro's agent chat and type:
   > "I want to use the Solr to OpenSearch skill."

   Or just drop a `schema.xml` file into the project -- the hook will fire automatically.

That's it. No configuration, no API keys to paste into Kiro (it uses your existing
AWS credentials), no extensions to install.

---

## What Is Kiro?

Kiro is Amazon's AI-powered IDE, built on Code OSS (the VS Code foundation). It
launched in preview in mid-2025 and is **free to use** during the preview period
(with generous daily interaction limits on Sonnet, and unlimited on Haiku).

Kiro's core philosophy is **spec-driven development**: instead of jumping straight
from a prompt to code ("vibe coding"), Kiro generates structured planning
artifacts -- requirements, technical designs, and sequenced task lists -- before
writing a single line. Think of it as the difference between sketching on a napkin
and drafting blueprints.

### Key Concepts

| Concept | What It Does | Where It Lives |
|---------|-------------|----------------|
| **Steering** | Persistent project context (product goals, tech stack, coding standards) that shapes every AI interaction | `.kiro/steering/*.md` |
| **Specs** | Structured feature plans: requirements (EARS notation), design docs, task checklists | `.kiro/specs/<feature>/` |
| **Hooks** | Event-driven automations -- file created/edited/deleted triggers agent actions | `.kiro/hooks/*.kiro.hook` |
| **Skills** | Portable agent capability packages (the [Agent Skills](https://github.com/agent-skills) open standard) | `.kiro/skills/<name>/SKILL.md` |
| **Custom Agents** | Fine-grained agent configs with tool access, MCP servers, and resource scoping | `.kiro/agents/<name>.json` |

---

## Why Kiro for This Skill?

### 1. Steering Files Keep the Advisor Honest

This migration advisor lives or dies by accuracy (see `steering/accuracy.md`).
Kiro's steering files are **always loaded** into every AI interaction, so the
accuracy rules, incompatibility catalogs, and translation guidelines are always
in context -- not just when the user remembers to mention them.

With other tools you'd rely on the user pasting context, or hope that a
`.cursorrules` / `CLAUDE.md` file gets picked up. Kiro's `inclusion: always`
frontmatter **guarantees** it.

### 2. Hooks Automate the Obvious

Drop a `schema.xml` into your project and Kiro's hook system automatically
invokes the migration advisor to produce an OpenSearch mapping. No prompt
engineering, no remembering which command to run. The
`schema-assist.kiro.hook` file wires this up declaratively:

```json
{
  "when": { "type": "fileCreated", "patterns": ["**/schema.xml"] },
  "then": { "type": "askAgent", "prompt": "Parse this Solr schema..." }
}
```

This is a capability unique to Kiro among AI IDEs.

### 3. Specs Create an Audit Trail

When you use Kiro's spec workflow to plan a migration, the requirements,
design decisions, and task progress are committed alongside your code. For
enterprise migrations -- especially in regulated industries -- this traceability
is invaluable. You get a version-controlled record of *why* each mapping
decision was made, not just the final output.

### 4. Native AWS Integration

Kiro is built by AWS. It uses your existing AWS credentials seamlessly --
no API key juggling, no proxy setup. For teams already on AWS (which, if
you're migrating to Amazon OpenSearch Service, you are), this is the
path of least resistance.

### 5. The Agent Skills Standard Is Open and Portable

The `SKILL.md` format used by this project follows the open
[Agent Skills](https://github.com/agent-skills) standard. Skills you
build for Kiro are not locked in -- they work in any compatible tool.
This is a deliberate design choice: invest in the skill once, deploy
it wherever your team works.

---

## Comparison: Kiro vs Other AI IDEs

The table below compares Kiro with the most common alternatives for
packaging and distributing AI agent skills.

| Capability | Kiro | Cursor | Claude Code | GitHub Copilot | Windsurf |
|---|---|---|---|---|---|
| **Project context** | `.kiro/steering/` with inclusion modes (`always`, `fileMatch`, `auto`, `manual`) | `.cursorrules` (single file, always loaded) | `CLAUDE.md` (single file per directory) | `.github/copilot-instructions.md` | `.windsurfrules` |
| **Granularity of context** | Per-file-type, on-demand, or always -- you choose | All or nothing | All or nothing per directory level | All or nothing | All or nothing |
| **Structured planning** | Specs: requirements (EARS) -> design -> tasks | No | No | No | No |
| **Event-driven hooks** | File create/edit/delete + manual triggers | No | Shell hooks in settings.json | No | No |
| **Agent skills (portable)** | Open Agent Skills standard (`SKILL.md`) | No standard format | Slash-command skills (proprietary) | No | No |
| **Custom agents** | JSON config with tool/MCP/resource scoping | No | No | No | No |
| **Audit trail** | Specs committed with code | No | No | No | No |
| **AWS integration** | Native (uses AWS credentials) | Manual API key config | Anthropic API key | GitHub token | Manual API key config |
| **Pricing** | Free during preview; Sonnet + Haiku included | $20/mo Pro | Pay per API usage | $10/mo Individual | $15/mo Pro |
| **Base** | Code OSS (VS Code) | VS Code fork | CLI + IDE extensions | VS Code / JetBrains | VS Code fork |

### Where Each Tool Excels

- **Kiro** -- Best for teams that want **structured, auditable AI-assisted development**
  with deep AWS integration. The spec-driven workflow is unmatched for enterprise
  and regulated environments. Hooks and skills make it the most automatable option.

- **Cursor** -- Best for **raw speed of code generation**. Its tab-completion and
  inline editing are fast and fluid. Good for solo developers who prefer to
  iterate quickly without planning artifacts.

- **Claude Code** -- Best for **CLI-native workflows** and deep codebase reasoning.
  Excellent for developers who live in the terminal. The agentic loop is powerful
  for complex multi-file changes.

- **GitHub Copilot** -- Best for **broad ecosystem integration** (GitHub Issues, PRs,
  Actions). The most widely adopted, with the largest community. Good baseline
  for teams already invested in the GitHub platform.

- **Windsurf** -- Best for **AI-first editing** with Cascade (multi-step agentic
  flows). Strong at understanding project-wide context through indexing.

### What Only Kiro Can Do (Today)

1. **Spec-driven development** -- no other IDE generates EARS-notation requirements,
   technical designs, and sequenced task lists as a first-class workflow.
2. **File-event hooks** -- declarative JSON hooks that trigger agent actions when
   files are created, edited, or deleted. Claude Code has shell hooks, but Kiro's
   are declarative and agent-native.
3. **Inclusion-mode steering** -- load context always, by file pattern, on-demand,
   or let the AI decide. No other tool offers this granularity.
4. **Custom agent configs** -- scope an agent's tools, MCP servers, model, and
   resources via JSON. No other IDE exposes this level of agent customization.

---

## What's in the `.kiro/` Directory

```
AIAdvisor/.kiro/
  steering/
    product.md              # What this project is and who it serves
    tech.md                 # Tech stack and constraints
    structure.md            # File layout and naming conventions
  skills/
    solr-to-opensearch/     # Symlink -> ../../skills/solr-opensearch-migration-advisor/
  hooks/
    schema-assist.kiro.hook # Auto-invoke advisor when schema.xml is added
```

The skill itself lives in `AIAdvisor/skills/solr-opensearch-migration-advisor/`
and is symlinked into `.kiro/skills/` so Kiro discovers it. This keeps the skill
portable (it can be used outside Kiro) while giving Kiro native access.

---

## Next Steps

This is the **minimal Kiro packaging** -- enough to get the skill working in Kiro
with steering, a hook, and auto-discovery. Future iterations will add:

- **Custom agent config** (`.kiro/agents/migration-advisor.json`) with scoped tools
  and MCP server integration for live Solr/OpenSearch connectivity
- **Spec templates** for common migration scenarios (single collection, multi-tenant,
  SolrCloud fleet)
- **Additional hooks** for query file detection, config file analysis, and
  post-migration validation
- **Parallel packaging** for Cursor (`.cursorrules`), Claude Code (`CLAUDE.md`),
  and GitHub Copilot (`.github/copilot-instructions.md`) -- see the project roadmap

---

*For more on Kiro, visit [kiro.dev](https://kiro.dev/) or read the
[Introducing Kiro](https://kiro.dev/blog/introducing-kiro/) blog post.*
