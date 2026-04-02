# Stakeholder Register

**Session:** {session_id}
**Generated:** {timestamp}

---

## Team Roster

| Role | Name | Allocation | Contact | OpenSearch exp? |
|------|------|------------|---------|-----------------|
| Executive Sponsor | {name} | As needed | {contact} | {yes/no} |
| Product Owner | {name} | {%} | {contact} | {yes/no} |
| Search/Tech Lead | {name} | {%} | {contact} | {yes/no} |
| Solr Engineer | {name} | {%} | {contact} | {yes/no} |
| Infrastructure/Cloud | {name} | {%} | {contact} | {yes/no} |
| Relevance Lead | {name} | {%} | {contact} | {yes/no} |
| Integration Engineer | {name} | {%} | {contact} | {yes/no} |
| Security Lead | {name} | {%} | {contact} | {yes/no} |
| Content Owner | {name} | {%} | {contact} | {yes/no} |

## Decision Authority

| Decision | Who decides | Escalation path |
|----------|-------------|-----------------|
| Go / no-go for cutover | {name + role} | {escalation} |
| Rollback authority | {name + role} | {escalation} |
| Scope changes | {name + role} | {escalation} |
| Timeline changes | {name + role} | {escalation} |
| Budget approval | {name + role} | {escalation} |

## Communication Plan

| Audience | What they need | Frequency | Format |
|----------|---------------|-----------|--------|
| Exec sponsor | Progress dashboard (top section) | Bi-weekly | Email / artifact link |
| Product owner | Progress dashboard + incompatibility tracker | Weekly | Standup + artifact link |
| Engineering team | Full technical detail | Daily / per-sprint | Standup + repo |
| Broader org | Migration status (go/no-go timeline) | Monthly | Slide or 1-pager |

## Staffing Risks

| Risk | Severity | Mitigation |
|------|----------|------------|
| Team at <30% allocation — client deps will bottleneck | {severity} | Get sponsor commitment for response windows |
| Single-person knowledge dependency | {severity} | Capture knowledge early, cross-train |
| Team changes during migration window | {severity} | Confirm roster stability with sponsor |

## Dependency Map

*What does OSC / the migration team need from whom, and when?*

| Dependency | Owner | Needed by | Status |
|------------|-------|-----------|--------|
| Schema XML or Schema API access | {owner} | Intake | {status} |
| Query analytics export | {owner} | Design | {status} |
| Synonym / stopword files | {owner} | Design | {status} |
| Test environment provisioning | {owner} | Build | {status} |
| Production traffic routing control | {owner} | Cutover | {status} |
| Rollback mechanism verification | {owner} | Pre-cutover | {status} |

---

*Auto-generated from session state.  Update by providing stakeholder details
during the advisor conversation.*
