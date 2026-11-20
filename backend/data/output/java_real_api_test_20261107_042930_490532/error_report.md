# Pre-execution quota HOLD

Latest task requires verified available provider capacity and accounting for unknown external organization usage. Saved inventory is quota_unknown; local-only admission cannot prove this prerequisite.

This is a prerequisite failure, not a Groq HTTP error. No new provider response exists. The document runner currently builds LocalQuotaAdmission, which checks recorded limits and local/shared ledger charges but cannot establish unobserved external usage. Using it would not satisfy section 4 of the latest request. No HTTP error, retry, schema failure or latency is inferred. Credential approval remains non-expiring; provider verification must not be fabricated. Existing reservations and unknown usage remain charged according to their original policy.
