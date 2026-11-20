# Five-organization Groq configuration readiness

| Slot | Legacy credential present | Scheduler mapping | Verified organization ID | Duplicate identity check | Enabled | Readiness |
|---|---|---|---|---|---|---|
| 1 | true | PASS, dotenv alias to legacy slot 1 | Missing | UNKNOWN | false | HOLD |
| 2 | true | PASS, dotenv alias to legacy slot 2 | Missing | UNKNOWN | false | HOLD |
| 3 | true | PASS, dotenv alias to legacy slot 3 | Missing | UNKNOWN | false | HOLD |
| 4 | true | PASS, dotenv alias to legacy slot 4 | Missing | UNKNOWN | false | HOLD |
| 5 | true | PASS, dotenv alias to legacy slot 5 | Missing | UNKNOWN | false | HOLD |

Each slot needs its exact organization ID from a current custodian inventory record that binds the organization, project, and existing credential. The scheduler rejects duplicate identities. Enablement requires an explicit true value per slot. The alias resolves when loaded with dotenv interpolation. Supply the numbered legacy variables before interpolation when using the template.

Updated .env and .env.template using variable references. Checked all five references and the disabled loader state locally. The offline scheduler suite passed 49 tests with a workspace-local temporary directory. Zero API requests were made and no extraction ran.
