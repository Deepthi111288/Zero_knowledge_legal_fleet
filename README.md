# Zero-Knowledge Contract & NDA Lifecycle Engine — Complete Walkthrough

Everything below is real and has been run and tested by me before being given to you.
Where the source course material referenced specific tools (Antigravity IDE, ADK 2.0,
Gemini) that I can't independently verify the current install steps for, I've used
plain Python + your model provider's official SDK instead — it implements the exact
same architecture and will work regardless of which IDE you use.

---

## PART A — Installation (from a blank machine)

### 1. Install Python
You need Python 3.10+.
- **Windows**: download from python.org, check "Add to PATH" during install.
- **Mac**: `brew install python3` (requires Homebrew) or download from python.org.
- **Linux**: usually preinstalled; otherwise `sudo apt install python3 python3-pip`.

Verify:
```
python3 --version
```

### 2. Unzip the project
Unzip `zero_knowledge_legal_fleet.zip` anywhere you like, then:
```
cd zero_knowledge_legal_fleet
```

### 3. (Recommended) Create a virtual environment
```
python3 -m venv venv
source venv/bin/activate        # Mac/Linux
venv\Scripts\activate           # Windows
```

### 4. Install dependencies
The core pipeline has zero external dependencies (stdlib only). You only need to
install something once you wire in a real LLM:
```
pip install google-generativeai     # if using Gemini
# or
pip install anthropic               # if using Claude
# or
pip install openai                  # if using GPT
```

### 5. Get an API key
- Gemini: console at aistudio.google.com → "Get API key" → free tier available.
- Anthropic: console.anthropic.com → API Keys.
- OpenAI: platform.openai.com → API Keys.

Set it as an environment variable (don't hardcode it in files you might commit/share):
```
export GOOGLE_API_KEY="your-key-here"        # Mac/Linux
set GOOGLE_API_KEY=your-key-here              # Windows cmd
```

---

## PART B — Run the project as-is (no API key needed yet)

```
python3 main.py
```

You'll see three demos run in sequence:
1. A vendor contract with violations → flagged → human triage checkpoint written.
2. The human approving that flagged contract → pipeline resumes → final approved output.
3. An NDA (different domain, same code) → flagged → human triage checkpoint written.

Then run the test suite:
```
python3 test_main.py
```
You should see 7 tests pass. This proves the sanitizer, governance gate, resumable
human review, multi-domain reuse, and token logging all work correctly before you
touch any LLM code.

---

## PART C — Project structure

```
zero_knowledge_legal_fleet/
├── specs/
│   └── contract_audit_spec.md       # Gherkin Given/When/Then behavioral spec
├── skills/
│   ├── data_sanitizer/
│   │   ├── skill.md                 # Metadata (progressive disclosure pattern)
│   │   └── mask_regex.py            # Deterministic PII/financial masking
│   ├── policy_auditor/
│   │   ├── skill.md
│   │   └── policy_rules.md          # Vendor contract rules
│   └── nda_auditor/
│       ├── skill.md
│       └── nda_rules.md             # NDA-specific rules (second domain)
├── logs/                            # trajectory_trace.json + checkpoints/ written here at runtime
├── main.py                          # The orchestration graph (all nodes + features)
├── test_main.py                     # 7 automated tests
├── project_manifest.md              # Architecture rationale (use for your write-up)
└── requirements.txt
```

---

## PART D — How the pipeline actually works

**Node 1 — Data Sanitizer** (`node_data_sanitizer`)
Regex-masks company names, currency, emails before anything reaches an LLM. Logs
token count before/after masking (this is Additional Feature 3 — proves masking also
shrinks the prompt, not just protects privacy).

**Node 2 — Domain Auditor** (`node_domain_auditor`)
Sends only masked text to an LLM, asking it to check clauses against a rules file.
Which rules file is used depends on the `domain` parameter (`"contract"` or `"nda"`)
— this is Additional Feature 2, the same node code serving two different document
types just by swapping the rules file and prompt framing.

**Node 3 — Governance Gate** (`node_governance_gate`)
Pure Python, no LLM call. Re-checks the LLM's findings against a hardcoded violation
list. This exists specifically so a prompt injection or LLM hallucination can't
silently wave through a bad contract — the gate doesn't trust the LLM's verdict
alone, it re-verifies deterministically.

**Node 4a — Human Triage** (`node_human_triage`) + **resume_after_human_review**
When the gate triggers, a JSON checkpoint is written to `logs/checkpoints/<id>.json`
containing the masked text, the reverse-mask map, and the analysis. This is
Additional Feature 1: instead of the pipeline just dying, a human can later call:
```python
from main import resume_after_human_review
result, trajectory = resume_after_human_review(
    "logs/checkpoints/<id>.json",
    approved=True,           # or False to reject
    reviewer_notes="Indemnity cap was negotiated separately, acceptable."
)
print(result)
```
This re-enters the pipeline, de-masks the text for the human-facing output, and
records the human's decision back into the same checkpoint file — giving you a full
audit trail (auto-flag → human decision → final outcome).

**Node 4b — Auto-Draft** (`node_auto_draft`)
If the gate clears the document, this generates the redline output directly,
no human needed.

---

## PART E — Wiring in a real LLM (do this before your demo video)

Open `main.py`, find `call_llm_auditor()`. Replace the `raise NotImplementedError(...)`
with a real call. Two ready-to-use options are written out in the docstring above that
function — copy whichever matches your provider. Example for Gemini:

```python
import google.generativeai as genai

def call_llm_auditor(masked_text, rules_text):
    genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
    model = genai.GenerativeModel("gemini-1.5-flash")
    prompt = (
        f"Policy rules:\n{rules_text}\n\nMasked document:\n{masked_text}\n\n"
        f"List any policy violations, citing the rule number. "
        f"If none, say exactly: 'No policy violations detected.'"
    )
    response = model.generate_content(prompt)
    return response.text
```

Then in `node_domain_auditor`, change calls from `use_mock=True` to `use_mock=False`
(or just pass `use_mock=False` when you call `run_orchestration_fleet(...)`).

Re-run `python3 main.py` and confirm the LLM's real findings show up in the trace log.

---

## PART F — Test with real-ish documents

Write 3–4 plain-text sample documents (not actually confidential — invented test
data is fine) covering:
- A clean contract (should auto-draft, no human needed)
- A contract with auto-renewal (should trigger triage)
- A contract with uncapped indemnity (should trigger triage)
- An NDA with a residuals clause (should trigger triage, proves domain=nda path)

Run each through `run_orchestration_fleet("your_file.txt", domain="contract", use_mock=False)`
and confirm the trajectory log and checkpoint behavior look right.

---

## PART G — Architecture diagram for your submission

Use this as your "System Layout Map" (judges want a scannable diagram, not prose):

```
[Raw Document]
      |
      v
[Node 1: Data Sanitizer] --(masks PII/financials, logs token savings)
      |
      v
[Node 2: Domain Auditor (LLM)] --(contract or NDA rules, swappable)
      |
      v
[Node 3: Governance Gate] --(deterministic, non-LLM, un-hackable)
      |
      +---- clean ----> [Node 4b: Auto-Draft] ----> Final Output
      |
      +---- flagged --> [Node 4a: Human Triage Checkpoint]
                              |
                              v
                  [resume_after_human_review]
                   approved? --> Final Output (approved)
                   rejected? --> Final Output (rejected)
```

---

## PART H — Submission write-up checklist

Use `project_manifest.md` as your "Why" / Executive Business Impact section — it's
already written. For the "Demonstrated Core Primitives" section, you can now
honestly claim:
1. **Multi-domain micro-agent reuse** — same Sanitizer/Gate nodes, two document types.
2. **Resumable human-in-the-loop** — not just a dead-end halt, a full audit trail.
3. **Deterministic governance** — a non-LLM safety net that can't be prompt-injected.
4. **Token/cost transparency** — logged proof that masking reduces LLM spend.

Paste a real `logs/trajectory_trace.json` from one of your runs directly into your
write-up as your trajectory trace evidence.

**Before you submit:** verify the actual current competition rules, required
notebook format, and deadline directly on the competition's official page — I can't
confirm those details myself, and that's not something to get wrong based on a
summary document.

---

## What I can't do for you
- Provide API keys or make live model calls (no credentials in this environment).
- Confirm exact competition rules/deadlines.
- Record your demo video or submit on your behalf.
