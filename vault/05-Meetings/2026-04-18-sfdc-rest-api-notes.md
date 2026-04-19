---
type: meeting
date: 2026-04-18
tags: [salesforce, api, rest, soql, apex]
related: [[2026-04-10-mcp-architecture]], [[2026-04-15-agentforce-adoption]], [[2026-04-12-vault-kb-retrieval]]
---

# Salesforce REST API — Quick Reference Notes

## Authentication
OAuth 2.0 Connected App flow:
```
POST https://login.salesforce.com/services/oauth2/token
grant_type=client_credentials
client_id=<CONSUMER_KEY>
client_secret=<CONSUMER_SECRET>
```

## Key Endpoints
| Action | Endpoint |
|--------|----------|
| SOQL Query | `GET /services/data/v59.0/query?q=SELECT+Id,Name+FROM+Account` |
| Create Record | `POST /services/data/v59.0/sobjects/Account` |
| Update Record | `PATCH /services/data/v59.0/sobjects/Account/{id}` |
| Get Record | `GET /services/data/v59.0/sobjects/Account/{id}` |
| Delete Record | `DELETE /services/data/v59.0/sobjects/Account/{id}` |
| Execute Apex | `POST /services/data/v59.0/actions/custom/apex_action` |

## SOQL Tips
- Always use WITH SECURITY_ENFORCED for field-level security
- Limit results: `LIMIT 10 OFFSET 0`
- Use relationship queries: `SELECT Id, Account.Name FROM Contact`

## Common Objects
- `Account` — Companies and organizations
- `Contact` — People at accounts
- `Opportunity` — Sales deals
- `Case` — Customer service cases
- `Lead` — Pre-conversion prospects
- `Task` / `Event` — Activities

## Error Handling
- 400: Bad request (invalid SOQL, missing fields)
- 401: Unauthorized (token expired)
- 403: Forbidden (FLS violations)
- 404: Not found (invalid ID)

## Personal Note
Used this to build a quick demo: search all open Cases for a specific account, then create a follow-up Task assigned to the account owner. Total dev time: 45 minutes.
