# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| Latest  | Yes                |
| < 1.0   | No                 |

## Reporting a Vulnerability

**Do not** open a public GitHub issue for security vulnerabilities.

Email security concerns to: [security@cod3blackagency.com]

Include:
- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

### Response Timeline

- Acknowledgment: Within 48 hours
- Initial assessment: Within 7 days
- Resolution: Within 30 days (severity dependent)

## Security Measures

- Dependency scanning via Dependabot
- Code scanning via GitHub CodeQL
- Environment variables for secrets (never committed)
- HTTPS-only deployments
- Input validation and sanitization
