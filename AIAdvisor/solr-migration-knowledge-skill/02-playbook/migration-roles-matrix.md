# Migration Roles Matrix: Solr to OpenSearch

This matrix provides a tiered framework for staffing a Solr to OpenSearch migration based on team size and project complexity. It distinguishes between **Strategic/Architectural** (the "Why" and "What") and **Tactical/Implementation** (the "How") concerns.

For the compact canonical role model, specialist add-on roles, and escalation triggers, see
[`../04-skills/solr-to-opensearch-migration/references/roles-and-escalation-patterns.md`](/opt/work/OSC/agent99/04-skills/solr-to-opensearch-migration/references/roles-and-escalation-patterns.md).

## 1. The Tiered Matrix

| Tier | Team Size | Persona | Key Characteristic | Common Role Merges | High-Level Guidance |
|:---|:---|:---|:---|:---|:---|
| **Tier 1: Sole Proprietor** | 1 | The "Hero" | All core responsibilities in one head. | **All.** | Focus on "Minimum Viable Relevance." Avoid over-engineering; use managed services to reduce Ops load. |
| **Tier 2: Small Team** | 2–5 | Lean Engineering | Multi-hatting is mandatory. | PO+PM, Architect+Dev, Strategist+Engineer. | **Warning:** Don't forget the *Content Owner*. Ensure someone is explicitly responsible for "Success Criteria" separate from "Code." |
| **Tier 3: Standard Team** | 5–10 | Search Product Team | Most formal roles covered. | Strategy + Engineering might still overlap. | Focus on *Relevance Governance*. Use Quepid/RRE to move from "vibes" to "metrics." |
| **Tier 4: Large Team** | 10+ | Enterprise Platform | Highly specialized & siloed. | Roles are split (e.g., Ingestion vs. Search API). | Focus on *Communication & Observability*. Governance and "Change Absorption" become the primary bottlenecks. |
| **Tier 5: Challenge Round** | Any | The "Rescue" | Troubled/Passive-Aggressive environment. | **Dysfunctional.** Roles are often "unowned" or contested. | "Roll up your sleeves." Focus on *Evidence-based Truth Detection* to bypass political gridlock. |

---

## 2. Role Definitions: Strategic vs. Tactical

Use these labels to distinguish between long-term system design (**[S]**) and day-to-day execution (**[T]**).

### [S] Strategic / Architectural Roles
*   **Stakeholder:** Defines business success (ROI, Cost, Speed).
*   **Product Owner:** Translates user needs into prioritized features.
*   **Architect:** Designs the cross-system integration and "Target Posture" (AWS vs. Cloud-agnostic).
*   **Search Relevance Strategist:** Designs the tuning loop and ranking philosophy.
*   **Metadata Owner:** Owns the "Source of Truth" for synonyms, taxonomies, and business rules.

### [T] Tactical / Implementation Roles
*   **Project Manager:** Owns the timeline, blockers, and resource allocation.
*   **Software Engineer:** Implements the API, ingestion pipelines, and engine configuration.
*   **Search Relevance Engineer:** Executes experiments, tunes weights, and builds the judgement set.
*   **Data Analyst:** Extracts query logs and identifies customer trends.
*   **Content Owner:** Provides access to raw data and solves ingestion "stalls."

---

## 3. Tier Guidance & Expert Warnings

### Tier 1: Sole Proprietor (The "All-In-One")
*   **The Trap:** Spending 80% of time on infra (Ops) and 0% on Relevance.
*   **Expert Tip:** Use AWS OpenSearch Serverless or Managed Service default settings as much as possible. Don't try to build a custom Lucene analyzer if a standard one "works."
*   **Strategic vs Tactical:** You must force yourself to "wear the Strategist hat" for 1 hour a week to ensure you aren't just moving technical debt from one engine to another.

### Tier 2: Small Team (2–5 People)
*   **The Trap:** "The Developer owns everything." If the dev is also the PO, they will prioritize "easy to code" over "valuable to user."
*   **Expert Tip:** Explicitly name a **Stakeholder Proxy** (e.g., a PM or Senior Dev) whose only job is to ask: "Is this better than Solr, or just different?"
*   **Warning:** Content acquisition is the #1 schedule killer. Ensure a dev is not spending 3 weeks "guessing" how the database schema works.

### Tier 3: Standard Team (5–10 People)
*   **The Trap:** Siloing between "Ingestion Team" and "Search Team." If the data arrives "dirty," the search team can't fix it with weights.
*   **Expert Tip:** Stand up a **Weekly Relevance Sync** where the Strategist, Engineer, and PO look at real queries together.
*   **RACI Requirement:** Clear ownership of *Synonyms*. If the Metadata Owner is missing, relevance tuning will hit a ceiling early.

### Tier 4: Large Team (10+ People)
*   **The Trap:** "Relevance Paralysis." Too many stakeholders with different opinions on what "#1" should be.
*   **Expert Tip:** Implement **Automated Offline Testing (RRE/Quepid)** immediately. You cannot manage a large team's opinions without objective data.
*   **Communication:** Use a "Status Dashboard" that tracks not just "CPU/Latency" but "Migration Progress" (e.g., % of features at parity).

---

## 4. The Challenge Round: "Messy" Situations
*   **Symptoms:** "We want 100% parity with a system we don't understand," passive-aggressive stakeholders, or "haunted" legacy code that no one dares touch.
*   **The Strategy:**
    1.  **Truth Detection First:** Don't trust documentation or "word of mouth." Use query logs to find out what users *actually* do.
    2.  **Evidence-Based Decisions:** When a stakeholder says "it feels wrong," reply with "Here are the metrics for the top 50 queries."
    3.  **Surgical Cuts:** Identify "Deliberate Non-Survivors" (features that are too complex/broken to move) and get sign-off to kill them early.
    4.  **Roll Up Sleeves:** Expect to do "Data Archaeology." You will likely find business logic hidden in Solr `schema.xml` comments or custom Java plugins.

---

## 5. Agent Instructions: Using this Matrix

When guiding a user, the Agent should:
1.  **Identify the Tier:** Ask "How many people are on your migration team?" and "Who owns the definition of success?"
2.  **Map the Roles:** Look for gaps. If they are Tier 2, ask "Who is your Content Owner?"
3.  **Distinguish [S] vs [T]:** In documentation and tasks, label them as Strategic or Tactical.
4.  **Detect "Challenge Round" signals:** If the user mentions "Parity is the only goal" or "Stakeholders aren't sure," trigger the Tier 5 guidance.
5.  **Record Q&A:** Document the roles assigned to individuals in the project's `requirements.md` or `design.md`.
