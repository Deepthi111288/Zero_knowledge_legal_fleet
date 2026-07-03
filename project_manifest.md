# Project Manifest — Zero-Knowledge Contract Lifecycle & Redlining Engine

## Problem
Manual legal contract review is slow, inconsistent, and exposes sensitive business
data (counterparty names, deal values) to anyone touching the document — including,
in an AI-assisted workflow, the LLM provider itself.

## Solution
A small multi-agent pipeline that:
1. Strips identifying/financial details locally before any text leaves the machine (Sanitizer).
2. Sends only masked text to an LLM to check for policy violations (Policy Auditor).
3. Applies a deterministic, non-LLM rule check on the LLM's findings so a prompt
   injection or hallucination can't silently approve a bad contract (Governance Gate).
4. Halts and hands off to a human whenever a real violation is detected, with a
   reviewable checkpoint file (Human Triage).
5. Logs every step (trajectory), not just the final answer, so the reasoning path
   is auditable.

## Why this architecture (not a single monolithic agent)
- Sanitization must be deterministic and local — you don't want an LLM "deciding"
  whether to mask a company name.
- The Governance Gate is intentionally NOT an LLM call. If the LLM's judgment is
  compromised (injection, hallucination), the gate still enforces hard rules.
- Splitting into nodes makes each piece independently testable (see test_main.py).

## What's mocked vs. real
- Sanitizer, Governance Gate, Human Triage, trajectory logging: fully real, tested, runnable.
- Policy Auditor LLM call: stubbed with `mock_llm_policy_auditor()` so the pipeline
  is runnable today. `call_llm_policy_auditor()` is where you plug in your actual
  model API (Gemini, Claude, GPT, etc.) — see README for instructions.

## Token/cost note
Only the masked, much shorter text ever reaches the LLM. Sensitive values never
leave the local sanitizer node, which also keeps the privacy story simple to explain
to judges/reviewers.
