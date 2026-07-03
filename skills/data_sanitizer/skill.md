---
name: Data Sanitizer
description: Masks company names, person names, and currency values in contract text before any LLM call.
tags: [security, pii, preprocessing]
version: 1.0.0
---

# Instructions
1. Receive raw contract text.
2. Apply regex-based masking for currency values, common company name patterns, and email addresses.
3. Return the masked text plus a mapping table (kept locally, never sent to the LLM) so the redline output
   can later be de-masked for the human reviewer.
4. Never forward the unmasked original text to any external API call.
