# Security Policy

## Scope

This is a **community** Python SDK. It is not an official SolvaPay product.

**In scope:**
- HMAC webhook signature verification logic
- Secret/API key handling and redaction
- Dependency supply-chain issues

**Out of scope:**
- SolvaPay server-side vulnerabilities
- Issues requiring a SolvaPay account to reproduce

**PCI scope:** The SDK never transmits raw cardholder data (PAN, CVV, expiry).
It only exchanges SolvaPay API keys and customer references over HTTPS.

## Reporting a Vulnerability

Email: `dhruv.sanan@greyorange.com`

Please include:
- A description of the issue and its impact
- Steps to reproduce
- Any proof-of-concept code (privately)

**Response SLA:** Best-effort; typically within 7 days.
**Disclosure policy:** 90-day coordinated disclosure. Public CVE filed only for confirmed SDK bugs.

## Supported Versions

| Version | Supported |
|---------|-----------|
| 0.8.x   | Yes       |
| < 0.8   | No — upgrade recommended |
