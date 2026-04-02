# Intake Worksheet Example: CSO

**Client name:** Connecting Sources Openly (CSO)  
**Primary contact:** Evan P., CTO  
**Assessment date:** 2026-03-19  
**OSC lead:** [Your Name]  
**Other attendees:** Daniel W., Product Owner; Drupal lead; Solr platform lead; infrastructure manager  
**Current migration driver:** cloud alignment, operational simplification, supportability, improved member search experience  
**Current target timeline:** 2 quarters  
**Known hard deadline:** before annual member summit content relaunch  
**Initial confidence in project scope:** `medium`

---

## 1. Executive Summary

### Working summary

- What the client believes they want:
  Move from a self-managed Drupal + SolrCloud estate to AWS-hosted OpenSearch with minimal disruption.
- What we believe they actually need:
  A phased migration assessment that confirms rebuildability, relevance risk, access-control behavior, and Drupal runtime compatibility before committing to dates.
- Immediate concerns:
  unclear meaning of the reported `1 TB`, uncertain direct Solr consumers, likely custom Drupal query shaping, incomplete ownership map
- Immediate unknowns:
  whether Drupal fully owns indexing, exact SolrCloud topology, and the depth of member-only entitlement logic

### Early recommendation

- Current recommendation:
  discovery and proof-first planning only
- Why:
  the estate is large enough that rebuild, relevance, and cutover assumptions need evidence rather than optimism

---

## 2. Estate Shape

### Current platform

- Is the current deployment SolrCloud?
  likely yes
- If yes, number of collections:
  5 total, 3 customer/member-facing, 2 internal/admin
- Customer-facing collections:
  articles, resource library, member knowledge base
- Internal/admin collections:
  editorial QA, internal reporting support
- ZooKeeper in use?
  yes
- Solr version:
  believed to be 8.x
- Drupal version:
  10.x
- Search-related Drupal modules:
  `search_api`, `search_api_solr`, `facets`, `search_api_autocomplete`, custom Views integrations

### Size and topology

- Reported size:
  ~1 TB
- What that size represents:
  not yet confirmed; likely total index footprint across primary collections and replicas
- Node count:
  believed 5 or 6 data nodes
- Shard count:
  unknown
- Replica count:
  unknown
- Peak query volume:
  weekday daytime spikes tied to member portal usage
- Peak indexing volume:
  scheduled overnight refreshes plus editorial increments during the day
- Notes:
  likely medium-high operational complexity even if user-facing search is conceptually straightforward

### Open questions

- [ ] Confirm whether `1 TB` means Solr index size, raw content size, or total estate footprint
- [ ] Confirm whether multiple collections matter for migration scope
- [ ] Confirm whether any non-Drupal systems query Solr directly

---

## 3. Content and Indexing Lifecycle

### Source systems

| Content type | Source system | Indexed via Drupal? | Other pipeline? | Notes |
|---|---|---|---|---|
| editorial articles | Drupal CMS | yes | no | core public content |
| member resources | Drupal + file assets | yes | maybe | entitlement-sensitive |
| PDFs and attachments | DAM / file store | partial | yes | likely pipeline complexity driver |

### Rebuildability

- Can the index be fully rebuilt from source systems?
  probably, but not yet proven
- If yes, estimated rebuild time:
  unknown
- If no, why not:
  some enrichment or attachment-processing steps may be easier to reproduce from Solr than from source
- Is Solr acting as a source of truth anywhere?
  unknown
- Are there manual correction workflows?
  likely yes for synonyms, promoted content, or edge-case editorial fixes
- Are attachments extracted? PDFs, Office docs, others?
  yes, PDFs definitely
- Are enrichments applied during indexing?
  likely yes, especially metadata normalization and access-tier derivation

### Risks

- Content access risk:
  medium
- Rebuildability risk:
  high until proven
- Bus-factor risk:
  medium-high
- O19s note:
  do not allow "we can always rebuild later" to stand without evidence of a real rebuild path and estimated duration

---

## 4. Query Behavior and Relevance

### Search profile

- Top 10 query patterns:
  policy lookup, member guide lookup, known-title article lookup, troubleshooting phrases, topical browse
- Known-item vs exploratory mix:
  mixed
- Business-critical search flows:
  member self-service, staff support lookup, public resource discovery
- Autocomplete in use?
  yes
- Facets in use?
  yes
- Multilingual search in use?
  not central today, but some future expectation exists

### Relevance controls

- Query parser(s) in use:
  likely eDisMax via Drupal / Solr integration
- Boost rules / function queries:
  unknown, probably some recency, title, and content-type weighting
- Synonyms in use?
  yes
- Stopwords / protected words / linguistic assets:
  likely yes, not yet received
- Who owns relevance today?
  probably split between product and technical staff
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
- O19s note:
  no parity promise should be made before query evidence, top-query review, and explicit agreement on what behaviors actually matter

---

## 5. Access Control and Security

### Access model

- Are results filtered by role, region, tenant, business unit, or something else?
  role and membership tier
- Is filtering enforced in Drupal, in Solr queries, or post-filtered in the application?
  believed to be query-time filtering, not yet verified
- Any document-level restrictions?
  yes
- Any field-level restrictions?
  none known
- Any known leakage concerns?
  none reported, but auditability is unclear

### Enterprise controls

- SSO / IAM / LDAP / SAML:
  enterprise SSO in Drupal; search-layer mapping unclear
- Compliance requirements:
  standard enterprise review, privacy considerations for member content
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
- O19s note:
  if entitlement logic is partly application-side and partly Solr-side, treat that as a design risk rather than an implementation detail

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
  attachment handling, entitlement-sensitive content, query shaping, autocomplete behavior
- O19s note:
  the likely outcome is not "port Solr exactly," but "preserve the important user behaviors and redesign the rest intentionally"

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
  Solr-specific response-shape quirks with no business value

---

## 8. Team and Ownership

| Responsibility | Named owner | Allocation | Confidence | Notes |
|---|---|---|---|---|
| Sponsor / stakeholder | Evan P. | medium | medium | executive sponsor / CTO |
| Product owner | Daniel W. | medium | medium | owns member search priorities |
| Drupal application lead | to be named | unknown | low | key implementation role |
| Content owner | unknown | unknown | low | needs naming |
| Relevance owner | shared / unclear | low | low | needs explicit ownership |
| Solr platform owner | to be named | unknown | low | current topology knowledge holder |
| Platform Ops / SRE | unknown | unknown | low | missing |
| Security / compliance | unknown | unknown | low | missing |
| QA / acceptance | unknown | unknown | low | missing |

### Team risks

- Missing critical roles:
  content owner, platform ops, security owner, QA/acceptance owner
- Under-allocated owners:
  sponsor and product likely part-time
- Single-person dependencies:
  likely Drupal lead and Solr platform lead
- O19s note:
  until content, ops, and relevance ownership are explicit, this is discovery work, not delivery planning

---

## 9. Performance, Ops, and Cutover

### Current posture

- Current SLA / latency expectation:
  likely sub-second perceived user expectation, no hard SLA confirmed
- Refresh / indexing lag expectation:
  probably minutes acceptable for most content
- Peak periods / blackout windows:
  avoid annual conference launch and major member-content releases
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
- O19s note:
  do not treat "we can switch back to Solr" as a rollback plan unless routing, divergence limits, and recovery steps are named

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
  Solr platform owner
  Priority:
  P0
  Due date:
  TBD

- Item:
  named content, security, and acceptance owners
  Owner:
  Evan P.
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

### Gate language

- Recommended client-facing line:
  We are not ready to discuss implementation dates with confidence yet. The correct next step is structured discovery plus artifact review, followed by a gated recommendation on whether CSO should move into proof-of-concept or implementation planning.

### Top 5 risks

1. unclear rebuild path from source systems
2. unclear relevance ownership and baseline evidence
3. unknown SolrCloud topology details
4. likely attachment and entitlement complexity
5. incomplete ownership for operations, security, and acceptance

### Top 5 unanswered questions

1. what exactly does the 1 TB number represent?
2. can the entire estate be rebuilt from source systems without Solr dependency?
3. are there direct Solr consumers outside Drupal?
4. what custom Solr or Drupal search behaviors exist?
5. how are member entitlements enforced end-to-end?

### Suggested next step

- run Session 1 discovery, collect P0 artifacts, and do not promise implementation dates yet
