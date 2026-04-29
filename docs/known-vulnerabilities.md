# Known Vulnerabilities

Unfixed CVEs are documented here per the global unfixed-CVE policy.
No entry may age past 60 days without reassessment. Review at least every 60 days.

| CVE                                                              | Package     | Severity | Introduced | Last Reviewed | Status       | Notes                                                                   |
|------------------------------------------------------------------|-------------|----------|------------|---------------|--------------|-------------------------------------------------------------------------|
| GHSA-4xh5-x5gv-qwph, GHSA-6vgw-5pg2-w6jp, GHSA-58qw-9mgm-455v | pip 25.2    | Medium   | 2026-04-29 | 2026-04-29    | Cannot fix   | System pip; not Poetry-managed. Reassess when migrating to uv (Phase 6+). |
| GHSA-6w46-j5rx-g56g                                             | pytest 8.4.1 | Low     | 2026-04-29 | 2026-04-29    | Deferred     | Fix is pytest 9.0.3 (major version). Upgrade requires test validation. |
