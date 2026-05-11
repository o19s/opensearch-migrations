# Authentication

**Trigger:** When the user asks about authentication, Kerberos, SSL/TLS, or identity providers in OpenSearch.

## Rules

- **Kerberos config paths:** keytab and `krb5.conf` files must be placed in the OpenSearch config directory (or a subdirectory). Their paths in `opensearch.yml` must be **relative**, not absolute. Surface this clearly in any Kerberos migration suggestion. ([OpenSearch Kerberos docs](https://docs.opensearch.org/latest/security/authentication-backends/kerberos/))

**Reference:** none yet — this file is the only authentication guidance in the skill. A dedicated `references/10-authentication.md` is a known gap.
