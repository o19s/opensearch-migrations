# Client Intake Email Draft

Subject: Pre-migration assessment kickoff for Drupal Solr to OpenSearch

Hi [Client Name / Team],

To start the pre-migration assessment, we want to confirm the shape of the current Drupal search estate before we recommend a migration posture or implementation plan.

From what we understand so far, this appears to be a large Drupal search deployment backed by roughly `1 TB` of Solr data. At that size, the key early questions are:

- whether the current platform is SolrCloud
- whether Drupal fully owns the indexing lifecycle
- what business-critical search behaviors must be preserved
- how access control and relevance are managed today
- how long a clean rebuild would take from source systems

To make the first assessment session productive, could you please send whatever you already have from the list below, and reply inline to the short questions that follow?

## Requested Artifacts

High priority:

- Solr `schema.xml` or managed schema for the relevant collection(s)
- Solr `solrconfig.xml` for the relevant collection(s)
- SolrCloud topology summary or cluster status output
- Drupal module list
- Drupal Search API server/index configuration export
- query logs or search analytics export
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
8. Who should be included in the first assessment session from product, Drupal, Solr/platform, and operations?

## Proposed First Session

For the first session, we recommend a 60-90 minute working intake covering:

- current platform shape and scope
- indexing and content lifecycle
- critical search behaviors and relevance controls
- security and access-control model
- ownership, risks, and next-step recommendation

If helpful, we can send a lighter agenda version ahead of time.

Best,

[Your Name]
[Title / Team]

