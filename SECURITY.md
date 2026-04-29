# Security Policy

## Reporting a Vulnerability

If you discover a security vulnerability in this repository,
**please do not open a public issue**.
Instead, use GitHub's built-in Security advisories feature:

1. Go to the repository's **Security** tab
2. Click **"Report a vulnerability"**
3. Fill in the details and submit

All reports will be kept confidential. We commit to acknowledging receipt and
next steps via the Security tab. For urgent matters, you may also contact
<byronawilliams@gmail.com>.

## Supported Versions

This project is currently pre-release. Only the latest commit on `main` receives
security fixes.

| Version  | Status       |
|----------|--------------|
| main     | Supported    |
| older    | Not supported |

## Security Practices

- **Static Analysis** with CodeQL, Ruff, and Bandit
- **Dependency Scanning** with pip-audit on every CI run
- **Secrets Detection** with GitGuardian on every push
- **Pinned GitHub Actions** using major-version tags; SHA pinning is a planned improvement

## CVE and Advisory Workflow

1. **Request a CVE** for issues rated Moderate or above.
2. **Draft and publish an advisory** in the Security tab.
3. **Document in** `docs/known-vulnerabilities.md` until resolved.
4. **Include remediation steps** in release notes.

## Response Timeline

- **Acknowledgment:** within 5 business days
- **Fix released:** within 30 days of acknowledgment
- **Emergency patch:** sooner for critical severity

## Disclosure Policy

We follow coordinated disclosure principles. Once a fix is available, we will
publish details in our Security Advisories page. If you wish to receive credit
for responsibly disclosing a vulnerability, please let us know; otherwise
credit will be anonymous.

Last updated: 2026-04-20
