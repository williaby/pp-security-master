# Known Vulnerabilities

Unfixed CVEs are documented here per the global unfixed-CVE policy.
No entry may age past 60 days without reassessment. Review at least every 60 days.

| CVE | Package | Severity | Introduced | Last Reviewed | Status | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| GHSA-4xh5-x5gv-qwph | pip 25.2 | Medium | 2026-04-23 | 2026-04-29 | Accepted | System-managed pip; not a project dependency, cannot be pinned in pyproject.toml. Fix available in pip 25.3 -- update the system pip when environment is refreshed. |
| GHSA-6vgw-5pg2-w6jp | pip 25.2 | Medium | 2026-04-23 | 2026-04-29 | Accepted | System-managed pip; not a project dependency, cannot be pinned in pyproject.toml. Fix available in pip 26.0 -- update the system pip when environment is refreshed. |
| GHSA-58qw-9mgm-455v | pip 25.2 | Medium | 2026-04-29 | 2026-04-29 | Accepted | System-managed pip; not a project dependency, cannot be pinned in pyproject.toml. Reassess when migrating to uv (Phase 6+). |
| PYSEC-2022-42969 | py 1.11.0 | Medium | 2026-04-23 | 2026-04-29 | Accepted | Transitive dependency via interrogate 1.7.0 (latest). The `py` library is abandoned; CVE is a ReDoS in py.path.svnwc which interrogate does not invoke. No fix available upstream -- reassess when interrogate drops the dependency or an alternative docstring coverage tool is available. |
