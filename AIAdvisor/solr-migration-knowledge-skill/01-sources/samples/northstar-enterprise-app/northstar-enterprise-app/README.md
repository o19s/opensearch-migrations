# Northstar Enterprise Demo App

This is the first-pass demo implementation scaffold for the Northstar enterprise Solr to
Amazon OpenSearch Service migration sample.

## What Is Here

- a Spring Boot/Kotlin application skeleton for the demo API
- a static landing page with a lightweight polished demo surface
- a target OpenSearch index definition in `src/main/resources/opensearch/atlas-index.json`
- a local copy of the Northstar sample corpus in `src/main/resources/samples/northstar-sample-docs.json`
- a Python reindex workflow in `scripts/reindex_northstar.py`
- a local OpenSearch plus Dashboards stack in `docker-compose.yml`
- a one-command bootstrap helper in `scripts/demo_bootstrap.sh`

## Demo Workflow

1. Review the mapping in `src/main/resources/opensearch/atlas-index.json`
2. Start the local demo stack with Docker Compose
3. Create the target index and aliases
4. Bulk-load the sample corpus with `scripts/reindex_northstar.py`
5. Start the demo app and exercise the sample search endpoints

## Local Demo Stack

The included `docker-compose.yml` provisions:

- `opensearch-demo` on `http://localhost:9200`
- `dashboards-demo` on `http://localhost:5601`

If you prefer one shared repo-level stack, the root
[`docker-compose.yaml`](/opt/work/OSC/agent99/docker-compose.yaml) now includes an
`opensearch-demo` profile with the same default ports. Use either the app-local compose file or
the root compose profile, not both at once.

Fastest path:

```bash
cd /opt/work/OSC/agent99/01-sources/samples/northstar-enterprise-app/northstar-enterprise-app
cp .env.example .env
bash scripts/demo_bootstrap.sh
GRADLE_USER_HOME=.gradle gradle bootRun
```

Then open:

- `http://localhost:8086/`
- `http://localhost:8086/actuator/health`
- `http://localhost:5601/`

## Reindex Script

The reindex script supports:

- `--create-index`
- `--recreate`
- `--index-name atlas-search-v1`
- `--read-alias atlas-search-read`
- `--write-alias atlas-search-write`

Example:

```bash
python scripts/reindex_northstar.py \
  --opensearch-url http://localhost:9200 \
  --create-index \
  --recreate
```

To use the shared repo-level demo engines instead of the app-local compose file:

```bash
cd /opt/work/OSC/agent99
bash tools/demo_search_stack.sh both
```

## Notes

- This is a starter implementation, not a production-ready application.
- AWS SigV4 support is intentionally deferred in this first pass; the script currently assumes
  direct HTTP access to an OpenSearch-compatible endpoint.
- The landing page is intentionally limited in scope, but it gives the demo a cleaner and more
  polished presentation than raw JSON endpoints alone.
- The search service now prefers live OpenSearch reads through `atlas-search-read`, but will
  fall back to the bundled sample corpus if the demo cluster or alias is unavailable.
- The shared repo-level bootstrap can also load the same sample corpus into Elasticsearch for
  side-by-side inspection in Kibana, but the demo app itself still queries OpenSearch.
