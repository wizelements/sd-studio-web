# Security Policy

## Scope

SD Studio is a remote control surface for a Stable Diffusion backend. The highest-risk boundary is the connection between the browser-facing application and the GPU/model API.

## Reporting a vulnerability

Do **not** open a public issue with exploit details, credentials, private endpoints, or other sensitive information.

Preferred reporting paths:

1. Use GitHub's private security-advisory flow when available.
2. Otherwise email **contact@cod3blackagency.com** with `SECURITY — SD Studio Web` in the subject.

Include the affected component, impact, reproduction steps, and the minimum safe evidence needed to verify the report.

## Security expectations

Deployments should:

- avoid exposing an unauthenticated Automatic1111 API to the public internet;
- use a VPN, authenticated reverse proxy, access-controlled tunnel, or equivalent trust boundary;
- restrict CORS to the intended application origin where browser CORS is required;
- keep server-only secrets out of browser bundles;
- validate backend URLs and avoid unsafe server-side proxy behavior;
- apply rate/resource controls appropriate to GPU cost and capacity;
- use HTTPS for public browser-facing deployments;
- keep dependencies and CodeQL findings reviewed.

## Repository controls

This repository includes CI and CodeQL workflows. Their presence does not prove the security of a separately operated Stable Diffusion backend or tunnel.

## Disclosure

Please allow maintainers to validate and remediate verified issues before public disclosure. Remediation priority depends on severity, exploitability, exposed infrastructure, and user/data impact.
