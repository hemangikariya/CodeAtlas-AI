# Security Policy - CodeAtlas AI

We take the security of your codebase and developer operations seriously. Please review this policy to understand our security model and how to report vulnerabilities.

---

## Security Model

CodeAtlas AI is built with several default security layers:
* **Single-Tenant Deployment**: Design constraints restrict V1 to single-tenant deployments, keeping codebases isolated inside your private cloud or virtual private cloud (VPC).
* **AI Guardrails Layer**: Every prompt and response passes through guardrails checking for injection vulnerabilities, model permission violations, and PII leakage.
* **Non-Root Execution**: Ingestion workers run within isolated container privileges, preventing direct file system access to host resources.
* **Secrets Ingestion Scanning**: Standard parsing runs token and secret scans to identify and sanitize hardcoded credentials in uploaded files before indexing.

---

## Reporting a Vulnerability

If you discover a security vulnerability, please do **not** open a public issue on GitHub. Instead, follow these steps to report it privately:

1. Send an email to `security@codeatlas.ai` with detailed description of the vulnerability.
2. Include:
   * A proof-of-concept (PoC) or steps to reproduce the issue.
   * Potential impact details (e.g. data leak, privilege escalation).
   * Any suggested mitigation steps.
3. We will acknowledge receipt of your report within 48 hours and work with you to coordinate a patch and disclosure timeline.
