# Demo Walkthrough

Date: 2026-03-23
Repo: `/opt/work/OSC/agent99`

## Goal

Show two things in one session:

1. the agent can be steered toward a more opinionated, next-step-oriented tone
2. a YOLO-generated migration spec can be turned into a real toy OpenSearch demo

## What Changed First

We updated the local agent guidance in [AGENTS.md](/opt/work/OSC/agent99/AGENTS.md) so the default behavior is:

- more opinionated when a recommendation is warranted
- assumption-tolerant in Express/YOLO interactions
- clearer for users who are overloaded or unfamiliar
- always ending substantive responses with at least one suggested next step

That matters because the point of YOLO mode is not just speed. It is speed plus useful direction.

## What The Hello Search Output Actually Was

The generated `hello-migration` package was not a runnable application. It was a migration spec:

- orientation in [README.md](/opt/work/OSC/agent99/examples/hello-migration/README.md)
- target mapping and query translation in [design.md](/opt/work/OSC/agent99/examples/hello-migration/design.md)
- phased execution plan in [tasks.md](/opt/work/OSC/agent99/examples/hello-migration/tasks.md)

That is important in a demo because it shows the agent did not pretend planning output was production-ready software.

## What We Built

We converted the planning artifact into a small runnable OpenSearch demo:

- [hello-index.json](/opt/work/OSC/agent99/examples/hello-migration/demo/hello-index.json)
- [hello-docs.json](/opt/work/OSC/agent99/examples/hello-migration/demo/hello-docs.json)
- [bootstrap_hello_demo.py](/opt/work/OSC/agent99/tools/bootstrap_hello_demo.py)
- [demo_hello_search.sh](/opt/work/OSC/agent99/tools/demo_hello_search.sh)

The result is a toy `hello` index with a 12-document sample corpus that can be loaded into a local OpenSearch container.

## Problems Encountered

This part is good demo material because it shows the agent working through real issues instead of succeeding magically.

First, the repo-level Docker Compose path collided with existing container names.

Second, a standalone OpenSearch container failed because of a duplicate security-disable setting.

The fix was pragmatic:

- stop relying on repo compose state for this toy demo
- launch a dedicated standalone container for the `hello` demo
- make the launcher recreate its own failed container cleanly

## Final Outcome

Running:

```bash
bash tools/demo_hello_search.sh
```

produced a working local OpenSearch demo with:

- index: `hello`
- documents loaded: `12`
- endpoint: `http://localhost:9200`
- container: `hello-opensearch-demo`

## Verification

A live search for `relevance drift` returned:

1. `Troubleshooting Relevance Drift`
2. `Migration Risks You Should Resolve First`
3. `Authoritative Product Decisions`

The category aggregation also came back correctly:

- `guide`: 4
- `design`: 3
- `operations`: 3
- `planning`: 2

## Why This Demo Works

The story is clean:

- steer the agent behavior
- generate a YOLO migration spec
- turn that spec into concrete runnable assets
- verify the result with a real search query

That is a better demo than just showing polished text, because it proves the agent can move from assumptions to executable output.

## Recommended Closing

The strongest closing line for the demo is:

“YOLO mode gave us a usable starting point, and the agent turned that starting point into a real OpenSearch artifact we could run and inspect.”

## Suggested Next Step

If you continue this demo path, the next best upgrade is to add a tiny UI or Dashboards walkthrough on top of the `hello` index so the audience sees both generated artifacts and a live search surface.
