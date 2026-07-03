---
name: NDA Auditor
description: Cross-references sanitized NDA clauses against NDA-specific policy rules. Second domain proving the skill/node pattern generalizes beyond vendor contracts.
tags: [legal, compliance, nda]
version: 1.0.0
---

# Instructions
1. Receive masked NDA text (never raw/unmasked text).
2. Compare clauses against nda_rules.md.
3. Output a structured verdict the same shape as the Policy Auditor: violations + verdict.
4. Reuses the same Data Sanitizer and Governance Gate nodes as the contract pipeline —
   only the rules file and prompt framing change. This is the proof point that the
   architecture is a reusable pattern, not a one-off script.
