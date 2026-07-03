```markdown
# Zero-Knowledge Legal Fleet

An enterprise-grade, privacy-preserving multi-agent orchestration pipeline designed for contract compliance auditing and risk mitigation under the principle of **Effective Trust**. Built independently for the Kaggle AI Agents Capstone Project (**Agents for Business** track).

---

## 📌 Problem Statement
In enterprise procurement, manual contract review suffers from high cognitive fatigue and immense liability. Overlooking a single automatic renewal or an uncapped indemnity clause can expose an organization to millions in structural losses. However, routing unredacted, confidential agreements directly to commercial Cloud LLM APIs compromises corporate data privacy, risks intellectual property leakage, and breaches stringent compliance mandates (GDPR, HIPAA, SOC2).

## 🚀 The Solution: Effective Trust Architecture
The **Zero-Knowledge Legal Fleet** solves this paradigm by anchoring flexible LLM intelligence inside strict, non-LLM Python boundaries. The system isolates private enterprise data at the local infrastructure layer while safely leveraging Google's Gemini 1.5 Flash model to audit legal clauses across completely separate transactional domains.

```text
              [Raw Enterprise Document]
                          │
                          ▼
  ============== LOCAL PYTHON BOUNDARY ==============
                          │
            ┌─────────────┴─────────────┐
            │  Node 1: Data Sanitizer   │ ── (Masks PII/Financials,
            └─────────────┬─────────────┘     Logs FinOps Token Savings)
                          │
                          ▼
  ────────────────── CLOUD API LAYER ──────────────────
                          │  (Secure, Sanitized Text Sequence)
                          ▼
            ┌───────────────────────────┐
            │  Node 2: Domain Auditor   │ ── (Contextually Swappable
            └─────────────┬─────────────┘     Contract/NDA Prompt Rules)
                          │
                          ▼  (Plain-Text Evaluation Matrix)
  ============== LOCAL PYTHON BOUNDARY ==============
                          │
            ┌─────────────┴─────────────┐
            │   Node 3: Governance Gate │ ── (Deterministic, Un-hackable
            └─────────────┬─────────────┘     Hardcoded Safety Net)
                          │
              ┌───────────┴───────────┐
              │                       │
      [If Clear]             [If Risk Flagged]
              │                       │
              ▼                       ▼
    ┌───────────────────┐   ┌───────────────────────────┐
    │ Node 4b: AutoDraft│   │ Node 4a: Human Triage     │
    └───────────────────┘   └─────────┬─────────────────┘
                                      │
                                      ▼ (Persistent JSON Checkpoint)
                            ┌───────────────────────────┐
                            │ resume_after_human_review │
                            └───────────────────────────┘

```

---

## 💎 Demonstrated Core Agent Primitives

### 1. Multi-Domain Micro-Agent Reuse

Rather than duplicating prompt chains, the structural topology of the orchestration pipeline remains identical. The engine dynamically pivots from a standard Vendor Procurement Contract to an NDA context purely by hot-swapping the underlying prompt rulesets (`policy_rules.md` vs `nda_rules.md`) and framing files.

### 2. Resumable Asynchronous Human-in-the-Loop

When high-risk clauses are caught by the engine, the pipeline writes a secure, persistent state checkpoint to disk (`logs/checkpoints/`) containing the masked sequence and individual inverse translation arrays. Execution halts safely, permitting human reviewers to inspect, append notes, and call a clean `resume_after_human_review` entry hook asynchronously.

### 3. Deterministic Governance Boundary

To protect against prompt injections, compliance drifts, and LLM hallucinations, the pipeline routes evaluation text through a hardcoded Python verification gate. The system does not trust the LLM's own self-reported compliance verdict; it verifies the text string deterministically.

### 4. FinOps & Sustainability Transparency

Local sanitization reduces payload footprint before transit. The pipeline logs explicit pre- and post-sanitization token deltas, proving that structural text masking actively drops computational overhead and API costs.

---

## 🛠️ Project Structure

```text
zero_knowledge_legal_fleet/
├── main.py                    # Multi-agent orchestrator and interactive demo execution loop
├── test_main.py               # Rigorous 7-point integration test suite 
├── requirements.txt           # Environment dependencies (google-generativeai)
├── README.md                  # System documentation and project architecture landing page
├── project_manifest.md        # Architectural design specifications & core design choices
├── logs/                      # Live system trace outputs and checkpoint storage
│   ├── trajectory_trace.json  # Complete multi-agent state audit trail logs
│   └── checkpoints/           # Persistent JSON human-in-the-loop state snapshots
└── skills/                    # Domain specialized rule playbooks & functional scripts
    ├── data_sanitizer/        # Local regex PII & financial masking node code
    ├── policy_auditor/        # Vendor Procurement compliance rule specs
    └── nda_auditor/           # Non-Disclosure Agreement validation playbooks

```

---

## ⚡ Setup & Verification Guide

### 1. Initialize Virtual Environment

```bash
# Clone and navigate to folder
cd zero_knowledge_legal_fleet

# Create and activate environment
python -m venv venv
source venv/bin/activate       # Mac/Linux
venv\Scripts\activate          # Windows

```

### 2. Install Dependencies & Set Session Keys

```bash
pip install google-generativeai

# Inject API key safely into active shell session memory (Never hardcoded)
export GOOGLE_API_KEY="your_real_gemini_api_key"   # Mac/Linux
set GOOGLE_API_KEY=your_real_gemini_api_key       # Windows CMD

```

### 3. Execute Automated Verification Suite

To verify the integrity of the data sanitizer, governance gates, checkpoint serialization systems, and FinOps logging nodes, execute the 7-point integration test file:

```bash
python test_main.py

```

### 4. Run Main Multi-Agent Live Demos

To see the system process standard agreements, trigger triage states, serialize to disk, resume via human hooks, and hot-swap domains dynamically, execute:

```bash
python main.py

```
