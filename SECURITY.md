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

## PCI Scope

The SDK **never transmits raw cardholder data (PAN, CVV, expiry, track data)**.
All tokenization happens **server-side** at the SolvaPay API; the SDK only
exchanges SolvaPay API keys, customer references, and tokenized identifiers
over HTTPS. Integrators using this SDK do not bring PAN data into their
own application scope through it.

If you discover any code path that would cause raw cardholder data to traverse
the SDK boundary, treat it as a high-severity vulnerability and report it via
the channel below.

## Reporting a Vulnerability

Email: `dhruv.sanan@greyorange.com`

Please include:
- A description of the issue and its impact
- Steps to reproduce
- Any proof-of-concept code (privately)

Encrypt sensitive payloads with the maintainer's public key on request.
Do **not** open public GitHub issues for suspected vulnerabilities.

**Response SLA:** Best-effort; typically within 7 days.
**Disclosure policy:** 90-day coordinated disclosure. Public CVE filed only for confirmed SDK bugs.

## Supported Versions

| Version | Supported |
|---------|-----------|
| 0.9.x   | Yes       |
| 0.8.x   | Yes       |
| < 0.8   | No — upgrade recommended |
