# Security Policy

## Reporting a Vulnerability

**Do NOT open a public GitHub issue for security vulnerabilities.**

SecureDx AI handles protected health information. We take security reports extremely seriously.

### How to Report

Email: **security@your-securedx-org.com**  
PGP Key: (publish your public key here)

Include:
- Description of the vulnerability
- Steps to reproduce
- Potential impact assessment
- Your name/handle for credit (optional)

### Response Timeline

| Milestone | Target |
|-----------|--------|
| Acknowledgement | 24 hours |
| Initial assessment | 72 hours |
| Patch for critical issues | 7 days |
| Patch for high issues | 30 days |
| Public disclosure | After patch is deployed |

### Scope

In scope:
- PHI boundary bypass (data leaving clinic network)
- Authentication bypass
- Privilege escalation (accessing physician data as admin, or vice versa)
- Audit log tampering or bypass
- FL gradient attacks enabling patient re-identification
- SQL injection or other injection vulnerabilities

Out of scope:
- Social engineering attacks
- Physical access to the clinic server
- Denial of service attacks

### Safe Harbor

We will not pursue legal action against researchers who report vulnerabilities in good faith, provided they do not access, modify, or delete patient data, and report to us before public disclosure.
