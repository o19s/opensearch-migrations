Phase 0: Engagement Setup
Collect and organize:

Client-provided material:
- Project charter / SOW / contract scope
- Pain points and success criteria (why are we migrating?)
- Timeline, budget, constraints (compliance, air-gapped, etc.)
- Roles and ownership (who approves cutover? who owns relevance?)
- Current Solr deployment details:
    - schema.xml or Schema API JSON for each collection
    - solrconfig.xml (request handlers, update chains, plugins)
    - ZooKeeper config (if SolrCloud)
    - Cluster topology (nodes, shards, replicas, hardware)
    - Traffic patterns (QPS, indexing rate, peak hours)
    - Sample queries (production logs ideally, or representative set)
    - Existing relevance tests or judgment sets (if any)
    - Client application code that talks to Solr (SolrJ, pysolr, HTTP)
- Target environment details:
    - AWS account/region, VPC constraints
    - OpenSearch version preference
    - Managed (AWS OpenSearch Service) vs self-managed

Consultant-provided material:
- Initial risk assessment (from the 200-item discovery matrix)
- Resource allocation, schedule, communication cadence
- Initial technical review notes ("I see 3 custom QParserPlugins, this will need application-layer rewrite")
- Relevance measurement plan (Quepid setup, judgment set strategy)

Concrete action: Copy 03-specs/techproducts-demo/ to 03-specs/acme-corp/, customize the steering docs and requirements.

Phase 1: Strategic Assessment (your point b)

This is where the skill's consulting methodology and strategic guidance pay off. Questions at this phase:

- Should we migrate at all? (skill covers "when NOT to migrate")
- What does "success" look like? Relevance parity? Better relevance? Lower cost? Faster indexing?
- How do we measure? Set up Quepid, define judgment sets, establish baseline nDCG on current Solr
- What's the UX? Is this keyword search, SAYT, faceted browse, hybrid semantic+keyword?
- What's the risk profile? Custom plugins? Complex eDisMax tuning? Large-scale data?
- What's the migration strategy? Big-bang cutover vs dual-write vs shadow traffic?

Output: Updated requirements.md and design.md in the client spec folder. These become the contract for the rest of the engagement.

Phase 2: Technical Design (your points b/c overlap)

Shift from strategic to tactical:

- Schema mapping (field-by-field, with incompatibility flags)
- Query translation (each query pattern with behavioral differences noted)
- Analyzer chain mapping (custom tokenizers, filters, synonyms)
- Index settings (shard count, replica strategy, refresh interval)
- Ingest pipeline design (replacing UpdateRequestProcessorChains)
- Client library migration plan (SolrJ -> opensearch-java, etc.)

Output: Detailed design.md with JSON mappings, query DSL examples, architecture diagrams.

Phase 3: Implementation (your point f)

This is where Jeff's tooling and your knowledge skill converge:

- Run schema converter, review output against knowledge skill's gotcha list
- Run query converter, validate against production query logs
- Write/generate migration scripts (reindexing, data transformation)
- Set up dual-write or shadow traffic if applicable
- Iterative tuning — run relevance tests, compare nDCG, adjust

The LLM's role here: troubleshooting live ("I'm getting this error when indexing nested documents"), explaining behavioral differences ("why did my scores change?"), generating config snippets.

Phase 4: Validation & Cutover                                                                                                                                                                                                                                                        
Phase 5: Handoff & Documentation (your point d)

- Architecture document (what was built and why)
- Operational runbook (monitoring, scaling, troubleshooting)
- Decision log (key choices made and rationale)
- Knowledge transfer sessions with client team
- Build/deploy scripts documented and tested

  ---                                                                                                                                                                                                                                                                                  
Your Specific Scenarios

a) Client adds hybrid search mid-project:

This is a scope change. You'd update:
1. 03-specs/acme-corp/steering/product.md — new requirement
2. 03-specs/acme-corp/requirements.md — new functional requirements for hybrid/semantic search
3. 03-specs/acme-corp/design.md — neural search plugin config, embedding model selection, k-NN index settings

You do NOT need to rebuild the skill. The skill is global knowledge. The client spec is engagement-specific. They're separate concerns. The skill should already have guidance on hybrid search in its reference files (this is a gap today — 03-target-design.md is only partial and
doesn't cover neural search yet).

If the skill lacks knowledge the engagement needs, that's when you'd enrich a reference file and rebuild. But that's a "improve the skill for all future engagements" action, not a per-client action.

b) Strategic phase: Covered above in Phase 1. The skill's consulting-methodology.md and consulting-concerns-inventory.md are the primary resources here. The gap is 01-strategic-guidance.md (not yet written) and 05-relevance-validation.md (not yet written, highest priority).

c) Tactical SAYT field mapping: This is Phase 2/3 work. The skill's solr-concepts-reference.md covers feature equivalence. Jeff's schema_converter.py handles the mechanical translation. The skill adds judgment: "SAYT on Solr typically uses EdgeNGramFilterFactory — on          
OpenSearch, use edge_ngram tokenizer in a custom analyzer, but beware: the default max_gram is 1, not 20."

d) Team-wide steering docs: Periodic snapshots of the client spec folder (03-specs/acme-corp/). The requirements.md, design.md, and tasks.md are the canonical state. You could version these with git tags for milestone snapshots, or export them as a PDF deck for stakeholder    
reviews.

e) Things you're not thinking of:
- Judgment set creation — who rates queries? How many? This is the hardest part of relevance validation and the biggest O19s differentiator
- Change management — the client's developers need to change their code, and they'll resist if they don't understand why
- Performance regression — OpenSearch may be slower on certain query patterns (especially complex aggregations); need early benchmarking
- Index lifecycle management — Solr likely has none; OpenSearch ISM policies need to be designed from scratch
- Monitoring gap — going from Solr metrics (JMX/Prometheus) to OpenSearch metrics (CloudWatch or _cat APIs) is a non-trivial operational shift
- Rollback plan — what happens if cutover goes badly? Dual-write makes this easy; big-bang makes it terrifying

f) Conversion scripts/process: This is where the solr_to_opensearch.py in your repo and Jeff's schema_converter.py/query_converter.py live. The workflow is iterative: run conversion, review output, fix edge cases, run again. The LLM provides live troubleshooting ("this field  
mapped to keyword but it should be text with a custom analyzer because...").
                                                                                                                                                                                                                                                                                       
---                                                                                                                                                                                                                                                                                  
What's Missing in the Current System

The biggest gaps for this workflow to actually work end-to-end:

1. 05-relevance-validation.md — the entire "how do we measure success" story is unwritten. This is the O19s core differentiator and it's the empty file.
2. No state management between sessions — when you say "it should remember state," the skill currently has no built-in mechanism for this. Jeff's approach has SessionState in Python; your approach has the 03-specs/ folder. The practical answer today is: the client spec folder
   IS the state, and you reference it in each conversation with the AI.
3. No hybrid/semantic search guidance — if Acme Corp wants neural search, the skill has nothing on embeddings, k-NN, or the neural search plugin.
4. No "live troubleshooting" integration — the skill advises, but there's no connection between the skill and an actual running OpenSearch cluster for interactive debugging.
5. No iteration tracking — you mentioned 5-10 iterations. There's no built-in way to track "iteration 3: changed analyzer chain, nDCG went from 0.72 to 0.78" across sessions.                                                                                                       
