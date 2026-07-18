# Security Policy

## Reporting a vulnerability

If you find a security issue, please don't open a public GitHub issue. Instead, use the **GitHub Security Advisory** feature (Security tab → Report a vulnerability), or reach out privately through GitHub.

Include what you found, how to reproduce it, and what impact you think it has. I'll acknowledge within 48 hours and aim to have a fix or response within a week.

## What's in scope

ORBIT is a local-only tool — it doesn't run a public server or handle multiple users. The realistic attack surface is:

- `orbit trace` executes a user-supplied Python script, so there's an obvious arbitrary code execution path if someone tricks you into tracing a malicious file
- prompt injection bypass — a crafted input that gets past Little Canary or Llama Guard without being flagged
- unsanitized input reaching the SQLite layer via the API

## Out of scope

- anything requiring physical access to the machine
- bugs in upstream dependencies (report those to the relevant project)
- theoretical issues without a working proof of concept
