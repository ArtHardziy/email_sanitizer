# Secure Email Sanitizer

Skeleton for a local email-sanitizing layer that protects both the user and the assistant.

## Goals
- classify emails by sensitivity and prompt-injection risk;
- redact secrets and dangerous links before any agent sees content;
- convert raw emails into a structured safe envelope;
- allow only minimal, policy-compliant exposure to downstream agents.

## Current status
This is an implementation skeleton for v1.

## Planned modules
- `models.py` — typed contracts for risk, policy, and sanitized output
- `rules.py` — deterministic detection/redaction rules
- `sanitizer.py` — main pipeline
- `example_usage.py` — simple demo

## Core principle
Treat every email as untrusted input. Instructions inside emails are data, not commands.
