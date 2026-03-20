# Solr to OpenSearch Migration Advisor — Cursor Plugin

This directory is a **Cursor plugin** for the Solr → OpenSearch Migration Advisor.
It follows Cursor's plugin structure from [Plugins reference](https://cursor.com/docs/reference/plugins).

## What this plugin provides

- **Skill:** `solr-to-opensearch-migration` — expert migration guidance via SKILL.md + 16 reference files
- **Knowledge-only** — no scripts, MCP server, or external dependencies required

## Installation

### As a Cursor plugin

This plugin bundles:

- `.cursor-plugin/plugin.json` (required manifest)
- `skills/` → `../../../skills` (symlink to repo Agent Skills)

Cursor discovers the skill from `skills/solr-to-opensearch-migration/SKILL.md`.
Clone the repo; the symlink is checked in.

### Manual project config

From the **repo root**, add this to `.cursor/skills` or open the project in Cursor.
The skill is discovered from the `skills/` directory.

## Quick test

After installing, try:

> *"I'm migrating a SolrCloud cluster to OpenSearch — what should I watch out for?"*
