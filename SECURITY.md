# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 0.1.x   | ✅ Yes     |

## Reporting a Vulnerability

**Please do not report security vulnerabilities through public GitHub Issues.**

If you discover a security vulnerability in ORBIT, please:

1. Open a **GitHub Security Advisory** via the "Security" tab in the repository.
2. Or email the maintainers privately via GitHub's contact mechanism.

Please include:
- A description of the vulnerability
- Steps to reproduce
- Potential impact assessment
- Any suggested mitigations

You can expect:
- Acknowledgment within **48 hours**
- A status update within **7 days**
- Credit in the release notes (if desired)

## Scope

Given ORBIT is a **local-first tool with no network server**, the primary security concerns are:

- Arbitrary code execution via the `orbit trace` command (runs user-provided Python scripts)
- Prompt injection bypass in the Security Guard module
- SQLite injection via unsanitized inputs to the API

## Out of Scope

- Vulnerabilities requiring physical access to the machine
- Issues in third-party dependencies (please report to upstream)
- Theoretical vulnerabilities without a proof of concept
