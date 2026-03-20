# Intake Worksheet Example

**Client name:** Meridian Industrial  
**Primary contact:** Rachel Kim, Director of Digital Platforms  
**Assessment date:** 2026-03-19  
**OSC lead:** [Your Name]  
**Other attendees:** Drupal lead, Solr platform lead, product manager, infrastructure manager  
**Current migration driver:** cloud alignment, operational simplification, supportability, moderate relevance improvement  
**Current target timeline:** 2 quarters  
**Known hard deadline:** before Q4 product launch freeze  
**Initial confidence in project scope:** `medium`

---

## 1. Executive Summary

### Working summary

- What the client believes they want:
  Move from a self-managed Drupal + SolrCloud estate to AWS-hosted OpenSearch with minimal disruption.
- What we believe they actually need:
  A phased migration assessment that confirms rebuildability, relevance risk, and Drupal runtime compatibility before committing to implementation dates.
- Immediate concerns:
  unclear meaning of the reported `1 TB`, uncertain direct Solr consumers, unknown extent of custom query shaping
- Immediate unknowns:
  whether Drupal fully owns indexing, exact SolrCloud topology, entitlement complexity

### Early recommendation

- Current recommendation:
  discovery and proof-first planning only
- Why:
  the estate is large enough that cutover and rebuild assumptions need evidence, not optimism

---

## 2. Estate Shape

### Current platform

- Is the current deployment SolrCloud?
  likely yes
- If yes, number of collections:
  6 total, 2 customer-facing, 2 authenticated partner-facing, 2 internal/admin
- Customer-facing collections:
  product content, knowledge base
- Internal/admin collections:
  content QA, reporting support
- ZooKeeper in use?
  yes
- Solr version:
  believed to be 8.x
- Drupal version:
  10.x
- Search-related Drupal modules:
  `search_api`, `search_api_solr`, `facets`, `search_api_autocomplete`, several custom Views integrations

### Size and topology

- Reported size:
  ~1 TB
- What that size represents:
  not yet confirmed; likely total Solr index footprint across primary collections and replicas
- Node count:
  believed 6 data nodes
- Shard count:
  unknown
- Replica count:
  unknown
- Peak query volume:
  moderate weekday daytime spikes
- Peak indexing volume:
  nightly bulk refresh plus incremental updates during business hours
- Notes:
  likely medium-high operational complexity even if application behavior is fairly standard

### Open questions

- [x] Confirm whether `1 TB` means Solr index size, raw content size, or total estate footprint
- [ ] Confirm whether multiple collections matter for migration scope
- [ ] Confirm whether any non-Drupal systems query Solr directly

---

## 3. Content and Indexing Lifecycle

### Source systems

| Content type | Source system | Indexed via Drupal? | Other pipeline? | Notes |
|---|---|---|---|---|
| product pages | Drupal CMS | yes | no | standard editorial content |
| manuals and PDFs | DAM + attachment extraction | partial | yes | likely pipeline complexity driver |
| partner-only bulletins | Drupal + entitlement metadata | yes | maybe | access-control sensitive |

### Rebuildability

- Can the index be fully rebuilt from source systems?
  probably, but not yet proven
- If yes, estimated rebuild time:
  unknown
- If no, why not:
  some enrichment steps may currently be easier to reproduce from Solr than from source
- Is Solr acting as a source of truth anywhere?
  unknown
- Are there manual correction workflows?
  likely yes for synonym and content exception handling
- Are attachments extracted? PDFs, Office docs, others?
  yes, PDFs definitely
- Are enrichments applied during indexing?
  yes, likely classification and metadata normalization

### Risks

- Content access risk:
  medium
- Rebuildability risk:
  high until proven
- Bus-factor risk:
  medium-high

---

## 4. Query Behavior and Relevance

### Search profile

- Top 10 query patterns:
  part lookup, manual lookup, error-code lookup, product-family browse, troubleshooting phrases
- Known-item vs exploratory mix:
  mixed, with strong known-item component
- Business-critical search flows:
  support lookup, dealer content retrieval, customer self-service knowledge search
- Autocomplete in use?
  yes
- Facets in use?
  yes
- Multilingual search in use?
  likely limited now, may expand later

### Relevance controls

- Query parser(s) in use:
  likely eDisMax via Drupal / Solr integration
- Boost rules / function queries:
  unknown, probably some recency and title weighting
- Synonyms in use?
  yes
- Stopwords / protected words / linguistic assets:
  likely yes, not yet received
- Who owns relevance today?
  shared between product and one technical lead
- Is there a documented relevance strategy?
  no clear evidence yet

### Evidence

- Query analytics available?
  partial
- Click / engagement data available?
  unknown
- Zero-result reporting available?
  unknown
- Existing gold queries or judgement set?
  no

### Risks

- Relevance parity risk:
  high
- Missing evidence risk:
  high
- Single-person knowledge risk:
  high

---

## 5. Access Control and Security

### Access model

- Are results filtered by role, region, tenant, business unit, or something else?
  role and audience tier
- Is filtering enforced in Drupal, in Solr queries, or post-filtered in the application?
  believed to be query-time filtering, not yet verified
- Any document-level restrictions?
  yes
- Any field-level restrictions?
  none known
- Any known leakage concerns?
  none reported, but auditability unclear

### Enterprise controls

- SSO / IAM / LDAP / SAML:
  enterprise SSO in Drupal; search layer mapping unclear
- Compliance requirements:
  standard enterprise security review
- Audit requirements:
  moderate
- Security review owner:
  to be named

### Risks

- Access-control complexity:
  medium-high
- Compliance complexity:
  medium
- Security unknowns:
  medium-high

---

## 6. Drupal-Specific Runtime Questions

- Does Drupal Search API own indexing lifecycle?
  likely yes for core content, maybe not for all enrichments
- Is `search_api_solr` in use?
  yes
- Are there custom Search API processors?
  likely
- Are there Views pages tightly coupled to Solr behavior?
  yes
- Are Facets module behaviors critical?
  yes
- Is `search_api_autocomplete` in use?
  yes
- Are there multilingual analyzers or language-specific indexes?
  not fully known
- Any custom Drupal code shaping search requests?
  likely yes

### Migration judgement

- Preferred target posture right now:
  OpenSearch through Drupal, not raw index migration
- Confidence in Drupal-led reindex path:
  medium
- Reasons this may need redesign:
  attachment handling, query shaping, access control, autocomplete behavior

---

## 7. Solr Feature Inventory

- [x] eDisMax / DisMax
- [ ] Grouping / collapse
- [ ] Function queries
- [ ] Custom request handlers
- [ ] Custom update processors
- [ ] Custom plugins / JARs
- [ ] Streaming expressions
- [ ] Atomic updates
- [ ] Nested / child docs
- [x] Spellcheck / suggest
- [x] Custom analyzers
- [ ] MoreLikeThis
- [ ] Direct Solr query consumers outside Drupal

### Notes

- Known redesign zones:
  autocomplete, facets, attachment extraction, entitlement-sensitive content
- Unknown/undocumented features:
  custom query shaping, request handlers, external consumers
- Features likely not worth preserving:
  any Solr-specific response-shape quirks with no business value

---

## 8. Team and Ownership

| Responsibility | Named owner | Allocation | Confidence | Notes |
|---|---|---|---|---|
| Sponsor / stakeholder | Rachel Kim | medium | medium | business sponsor present |
| Product owner | Daniel Foster | medium | medium | understands support journeys |
| Drupal application lead | Priya Sethi | high | high | likely key technical lead |
| Content owner | unknown | unknown | low | needs naming |
| Relevance owner | shared / unclear | low | low | needs explicit ownership |
| Solr platform owner | Marcus Lee | medium | medium | likely knows current cluster |
| Platform Ops / SRE | unknown | unknown | low | missing |
| Security / compliance | unknown | unknown | low | missing |
| QA / acceptance | unknown | unknown | low | missing |

### Team risks

- Missing critical roles:
  content owner, security owner, QA/acceptance owner
- Under-allocated owners:
  product and platform likely part-time
- Single-person dependencies:
  Drupal lead and Solr lead

---

## 9. Performance, Ops, and Cutover

### Current posture

- Current SLA / latency expectation:
  likely sub-second user expectation, no hard SLA confirmed
- Refresh / indexing lag expectation:
  probably minutes acceptable for most content, faster for support updates
- Peak periods / blackout windows:
  avoid major launches and Q4 freeze
- Incident owner today:
  unclear
- Rollback expectation:
  likely wants quick fallback
- RTO:
  unknown
- RPO:
  unknown

### Migration posture

- Appetite for dual-run:
  probably yes if framed as risk control
- Appetite for phased traffic shift:
  likely yes
- Can current routing support canary or staged cutover?
  unknown
- Is a proof-of-concept acceptable before full migration planning?
  likely yes

### Risks

- Operational readiness risk:
  high
- Cutover risk:
  high
- Rollback risk:
  high until routing and divergence strategy are understood

---

## 10. Artifact Checklist

### Requested

- [x] Solr schema / managed schema
- [x] Solr config
- [x] SolrCloud topology / cluster status
- [x] Drupal module list
- [x] Search API server/index config export
- [x] Query logs / analytics export
- [x] Synonyms / stopwords / protwords
- [ ] Sample documents
- [ ] Architecture diagram
- [ ] Custom search-related code references

### Received

- [ ] Solr schema / managed schema
- [ ] Solr config
- [ ] SolrCloud topology / cluster status
- [ ] Drupal module list
- [ ] Search API server/index config export
- [ ] Query logs / analytics export
- [ ] Synonyms / stopwords / protwords
- [ ] Sample documents
- [ ] Architecture diagram
- [ ] Custom search-related code references

### Missing / Follow-up

- Item:
  topology export and shard/replica summary
  Owner:
  Marcus Lee
  Priority:
  P0
  Due date:
  TBD

- Item:
  named relevance and content owners
  Owner:
  Rachel Kim
  Priority:
  P0
  Due date:
  TBD

---

## 11. Initial Assessment Output

### Best-guess complexity

- Complexity rating: `4`
- Confidence in rating: `medium-low`

### Initial recommendation

- [x] Discovery only
- [ ] Strategic planning only
- [ ] Proceed to proof-of-concept
- [ ] Proceed to implementation planning with controls

### Top 5 risks

1. unclear rebuild path from source systems
2. unclear relevance ownership and measurement baseline
3. unknown SolrCloud topology details
4. likely attachment and enrichment complexity
5. incomplete ownership for operations, security, and acceptance

### Top 5 unanswered questions

1. what exactly does the 1 TB number represent?
2. can the entire estate be rebuilt from source systems without Solr dependency?
3. are there direct Solr consumers outside Drupal?
4. what custom Solr or Drupal search behaviors exist?
5. how are entitlements enforced end-to-end?

### Suggested next step

- run Session 1 discovery, collect P0 artifacts, and do not promise implementation dates yet

