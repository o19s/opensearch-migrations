# Drupal Solr to OpenSearch Intake Worksheet

**Use case:** Session 1 intake for a Drupal client with a large Solr estate  
**Recommended format:** Markdown in a plain text editor  
**Prepared:** 2026-03-19

---

## Why Markdown

Markdown is the best default for this worksheet because it is:

- easy to fill in during a live call
- easy to diff and revise later
- easy to paste into chat, email, tickets, or specs
- easy for an agent to read and transform into requirements, risks, and plans

If the client needs a more structured artifact later, convert this into:

- a spreadsheet for roster / inventory tracking
- a form for repeated assessments
- a polished readout document after discovery

Start in Markdown. Structure later if needed.

---

## Engagement Snapshot

- Client name:
- Primary contact:
- Assessment date:
- OSC lead:
- Other attendees:
- Current migration driver:
- Current target timeline:
- Known hard deadline:
- Initial confidence in project scope: `low / medium / high`

---

## 1. Executive Summary

### Working summary

- What the client believes they want:
- What we believe they actually need:
- Immediate concerns:
- Immediate unknowns:

### Early recommendation

- Current recommendation:
- Why:

---

## 2. Estate Shape

### Current platform

- Is the current deployment SolrCloud?
- If yes, number of collections:
- Customer-facing collections:
- Internal/admin collections:
- ZooKeeper in use?
- Solr version:
- Drupal version:
- Search-related Drupal modules:

### Size and topology

- Reported size:
- What that size represents:
- Node count:
- Shard count:
- Replica count:
- Peak query volume:
- Peak indexing volume:
- Notes:

### Open questions

- [ ] Confirm whether `1 TB` means Solr index size, raw content size, or total estate footprint
- [ ] Confirm whether multiple collections matter for migration scope
- [ ] Confirm whether any non-Drupal systems query Solr directly

---

## 3. Content and Indexing Lifecycle

### Source systems

| Content type | Source system | Indexed via Drupal? | Other pipeline? | Notes |
|---|---|---|---|---|
| | | | | |
| | | | | |
| | | | | |

### Rebuildability

- Can the index be fully rebuilt from source systems?
- If yes, estimated rebuild time:
- If no, why not:
- Is Solr acting as a source of truth anywhere?
- Are there manual correction workflows?
- Are attachments extracted? PDFs, Office docs, others?
- Are enrichments applied during indexing?

### Risks

- Content access risk:
- Rebuildability risk:
- Bus-factor risk:

---

## 4. Query Behavior and Relevance

### Search profile

- Top 10 query patterns:
- Known-item vs exploratory mix:
- Business-critical search flows:
- Autocomplete in use?
- Facets in use?
- Multilingual search in use?

### Relevance controls

- Query parser(s) in use:
- Boost rules / function queries:
- Synonyms in use?
- Stopwords / protected words / linguistic assets:
- Who owns relevance today?
- Is there a documented relevance strategy?

### Evidence

- Query analytics available?
- Click / engagement data available?
- Zero-result reporting available?
- Existing gold queries or judgement set?

### Risks

- Relevance parity risk:
- Missing evidence risk:
- Single-person knowledge risk:

---

## 5. Access Control and Security

### Access model

- Are results filtered by role, region, tenant, business unit, or something else?
- Is filtering enforced in Drupal, in Solr queries, or post-filtered in the application?
- Any document-level restrictions?
- Any field-level restrictions?
- Any known leakage concerns?

### Enterprise controls

- SSO / IAM / LDAP / SAML:
- Compliance requirements:
- Audit requirements:
- Security review owner:

### Risks

- Access-control complexity:
- Compliance complexity:
- Security unknowns:

---

## 6. Drupal-Specific Runtime Questions

- Does Drupal Search API own indexing lifecycle?
- Is `search_api_solr` in use?
- Are there custom Search API processors?
- Are there Views pages tightly coupled to Solr behavior?
- Are Facets module behaviors critical?
- Is `search_api_autocomplete` in use?
- Are there multilingual analyzers or language-specific indexes?
- Any custom Drupal code shaping search requests?

### Migration judgement

- Preferred target posture right now:
- Confidence in Drupal-led reindex path:
- Reasons this may need redesign:

---

## 7. Solr Feature Inventory

Mark anything known to be in use.

- [ ] eDisMax / DisMax
- [ ] Grouping / collapse
- [ ] Function queries
- [ ] Custom request handlers
- [ ] Custom update processors
- [ ] Custom plugins / JARs
- [ ] Streaming expressions
- [ ] Atomic updates
- [ ] Nested / child docs
- [ ] Spellcheck / suggest
- [ ] Custom analyzers
- [ ] MoreLikeThis
- [ ] Direct Solr query consumers outside Drupal

### Notes

- Known redesign zones:
- Unknown/undocumented features:
- Features likely not worth preserving:

---

## 8. Team and Ownership

| Responsibility | Named owner | Allocation | Confidence | Notes |
|---|---|---|---|---|
| Sponsor / stakeholder | | | | |
| Product owner | | | | |
| Drupal application lead | | | | |
| Content owner | | | | |
| Relevance owner | | | | |
| Solr platform owner | | | | |
| Platform Ops / SRE | | | | |
| Security / compliance | | | | |
| QA / acceptance | | | | |

### Team risks

- Missing critical roles:
- Under-allocated owners:
- Single-person dependencies:

---

## 9. Performance, Ops, and Cutover

### Current posture

- Current SLA / latency expectation:
- Refresh / indexing lag expectation:
- Peak periods / blackout windows:
- Incident owner today:
- Rollback expectation:
- RTO:
- RPO:

### Migration posture

- Appetite for dual-run:
- Appetite for phased traffic shift:
- Can current routing support canary or staged cutover?
- Is a proof-of-concept acceptable before full migration planning?

### Risks

- Operational readiness risk:
- Cutover risk:
- Rollback risk:

---

## 10. Artifact Checklist

### Requested

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
  Owner:
  Priority:
  Due date:

- Item:
  Owner:
  Priority:
  Due date:

---

## 11. Initial Assessment Output

### Best-guess complexity

- Complexity rating: `1 / 2 / 3 / 4 / 5`
- Confidence in rating: `low / medium / high`

### Initial recommendation

- [ ] Discovery only
- [ ] Strategic planning only
- [ ] Proceed to proof-of-concept
- [ ] Proceed to implementation planning with controls

### Top 5 risks

1. 
2. 
3. 
4. 
5. 

### Top 5 unanswered questions

1. 
2. 
3. 
4. 
5. 

### Suggested next step

- 

---

## 12. Suggested Wrap-Up Language

Use this after Session 1:

> Based on today’s intake, we are treating this as a structured pre-migration assessment rather than a direct implementation start. Before we recommend a target design or delivery plan, we need to confirm the current Solr topology, clarify whether Drupal fully owns indexing, validate the meaning of the reported 1 TB footprint, and review the current relevance, access-control, and operational posture. Once those are confirmed, we can give you a credible migration recommendation, scope shape, and phased next step.
