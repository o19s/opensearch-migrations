# Client Intake Email Example: CSO

Subject: Connecting Sources Openly search assessment kickoff

Hi Evan, Daniel, and team,

Before we recommend a migration posture or delivery plan, we want to confirm the actual shape of the current Drupal search estate.

From what we understand so far, Connecting Sources Openly (CSO) appears to have a large Drupal search deployment backed by roughly `1 TB` of Solr data across a SolrCloud estate. At that size, the early questions are less about "can OpenSearch hold the content?" and more about:

- whether Drupal fully owns the indexing lifecycle
- which collections and search experiences are actually in scope
- which business-critical search behaviors must be preserved
- how role-based access and member-only content restrictions are enforced today
- how long a clean rebuild would take from source systems

We want to avoid guessing our way into a migration plan. To make the first assessment session productive, could you please send whatever you already have from the list below, and reply inline to the short questions that follow?

## Requested Artifacts

High priority:

- Solr managed schema or `schema.xml` for the relevant collection(s)
- `solrconfig.xml` for the relevant collection(s)
- SolrCloud topology summary or cluster status output
- Drupal module list for the affected site(s)
- Drupal Search API server/index configuration export
- sample query logs or analytics export
- synonym, stopword, and protected-word files if applicable

Helpful if available:

- sample documents for each major content type
- architecture diagram showing Drupal, Solr, and upstream content systems
- references to any custom code involved in indexing or query shaping
- current infrastructure sizing details

## Short Intake Questions

1. Is the current deployment definitely SolrCloud?
2. What does the reported `1 TB` represent exactly: Solr index size, raw source content, or total search estate footprint?
3. Does Drupal Search API own indexing, or do external pipelines write to Solr?
4. What are the top 5-10 business-critical search behaviors or query types?
5. Can the index be fully rebuilt from source systems without depending on Solr as a source of truth?
6. Are there any custom Solr plugins, analyzers, or request handlers in production?
7. Are there any permission or entitlement rules that affect what users can see in search?
8. Who should be included in the first assessment session from product, Drupal, Solr/platform, security, and operations?

## Proposed First Session

For the first session, we recommend a 75-minute working intake covering:

- current platform shape and scope
- indexing and content lifecycle
- critical search behaviors and relevance controls
- security and access-control model
- ownership, risks, and next-step recommendation

Our goal for that session is not to force an architecture decision on the call. The goal is to leave with:

- a clearer statement of what is actually in scope
- a short list of high-risk unknowns
- the right artifact follow-ups with owners
- a grounded recommendation on whether the next step is deeper discovery, a proof-of-concept, or implementation planning

Until we see the current topology, indexing ownership, and available evidence, we would treat any timeline or parity commitments as provisional.

If helpful, we can send a lighter agenda version ahead of time.

Best,

[Your Name]
[Title / Team]
