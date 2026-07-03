"""
Zero-Knowledge Contract Lifecycle & Redlining Engine
Multi-agent orchestration graph: Sanitizer -> Domain Auditor (LLM) -> Governance Gate
                                  -> Human Triage (resumable) / Auto-Draft

Features included:
  1. Resumable human-in-the-loop triage (resume_after_human_review)
  2. Multi-domain support (contract auditor + NDA auditor share the same nodes)
  3. Token/cost logging before vs after sanitization

You must wire ONE function to a real LLM provider: call_llm_auditor().
Everything else is real, runnable, tested code.
"""

import os
import sys
import json
import time
import uuid

sys.path.append(os.path.join(os.path.dirname(__file__), "skills", "data_sanitizer"))
from mask_regex import sanitize, restore  # noqa: E402

TRAJECTORY_LOG_PATH = "logs/trajectory_trace.json"
CHECKPOINT_DIR = "logs/checkpoints"

DOMAIN_RULES = {
    "contract": "skills/policy_auditor/policy_rules.md",
    "nda": "skills/nda_auditor/nda_rules.md",
}

CRITICAL_VIOLATIONS = [
    "automatic renewal",
    "unlimited liability",
    "indemnity clause",
    "uncapped indemnity",
    "residuals clause",
    "non-mutual",
]


def log_step(trajectory, step_num, node, action, status, extra=None):
    entry = {
        "step": step_num,
        "node": node,
        "action": action,
        "status": status,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    if extra:
        entry.update(extra)
    trajectory.append(entry)
    print(f"[Trace] step {step_num} -> {node}: {status}")


def estimate_tokens(text):
    """Rough token estimate (no tokenizer dependency): ~4 chars/token, English-text heuristic."""
    return max(1, len(text) // 4)


# ---------------------------------------------------------------------------
# NODE 1: Deterministic Sanitizer (+ token/cost logging, Feature 3)
# ---------------------------------------------------------------------------
def node_data_sanitizer(document_text, trajectory):
    tokens_before = estimate_tokens(document_text)
    masked_text, reverse_map = sanitize(document_text)
    tokens_after = estimate_tokens(masked_text)

    log_step(
        trajectory, 1, "Data Sanitizer", "Regex-based PII/financial masking", "Success",
        {
            "entities_masked": len(reverse_map),
            "tokens_before_sanitization": tokens_before,
            "tokens_after_sanitization": tokens_after,
            "tokens_saved": tokens_before - tokens_after,
        },
    )
    return masked_text, reverse_map


# ---------------------------------------------------------------------------
# NODE 2: Domain Auditor (LLM call — wire this to your provider)
# ---------------------------------------------------------------------------
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


def mock_llm_auditor(masked_text, rules_text):
    """Deterministic stand-in so the full pipeline is testable without API credentials."""
    findings = []
    lowered = masked_text.lower()
    if "auto-renew" in lowered or "automatically renew" in lowered:
        findings.append("Rule violation: Automatic renewal clause detected with no opt-out window.")
    if "indemnif" in lowered and "uncapped" in lowered:
        findings.append("Rule violation: Uncapped indemnity clause detected.")
    if "residual" in lowered:
        findings.append("Rule violation: Residuals clause detected — high leak risk.")
    if "non-mutual" in lowered or "one-sided" in lowered:
        findings.append("Rule violation: Non-mutual NDA detected.")
    if not findings:
        findings.append("No policy violations detected.")
    return "\n".join(findings)


def node_domain_auditor(masked_text, trajectory, domain="contract", use_mock=False):
    rules_path = DOMAIN_RULES[domain]
    with open(rules_path, "r") as f:
        rules_text = f.read()

    analysis = mock_llm_auditor(masked_text, rules_text) if use_mock else call_llm_auditor(masked_text, rules_text)
    tokens_sent = estimate_tokens(masked_text) + estimate_tokens(rules_text)

    log_step(
        trajectory, 2, f"{domain.title()} Auditor (LLM)",
        f"Cross-referenced clauses against {rules_path}",
        "Flagged" if "violation" in analysis.lower() else "Clear",
        {"analysis": analysis, "approx_tokens_sent_to_llm": tokens_sent},
    )
    return analysis


# ---------------------------------------------------------------------------
# NODE 3: Deterministic Governance Gate (non-LLM, un-hackable)
# ---------------------------------------------------------------------------
def node_governance_gate(analysis_text, trajectory):
    lowered = analysis_text.lower()
    has_violation = "no policy violations" not in lowered and "violation" in lowered
    triggered = has_violation or any(v in lowered for v in CRITICAL_VIOLATIONS)

    decision = "TRIGGER_HUMAN_TRIAGE" if triggered else "PROCEED_TO_AUTO_DRAFT"
    log_step(trajectory, 3, "Governance Gate", "Deterministic rule check on LLM analysis output", decision)
    return decision


# ---------------------------------------------------------------------------
# NODE 4a: Human Triage Checkpoint (now resumable — Feature 1)
# ---------------------------------------------------------------------------
def node_human_triage(masked_text, reverse_map, analysis, trajectory, domain):
    os.makedirs(CHECKPOINT_DIR, exist_ok=True)
    checkpoint_id = str(uuid.uuid4())[:8]
    checkpoint_path = os.path.join(CHECKPOINT_DIR, f"{checkpoint_id}.json")

    checkpoint_data = {
        "checkpoint_id": checkpoint_id,
        "domain": domain,
        "analysis": analysis,
        "masked_text": masked_text,
        "reverse_map": reverse_map,
        "status": "PENDING_HUMAN_REVIEW",
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    with open(checkpoint_path, "w") as f:
        json.dump(checkpoint_data, f, indent=2)

    log_step(
        trajectory, 4, "Human Triage", f"Wrote resumable checkpoint {checkpoint_id}",
        "WAITING_FOR_HUMAN_REVIEW", {"checkpoint_path": checkpoint_path},
    )
    return checkpoint_path


def resume_after_human_review(checkpoint_path, approved: bool, reviewer_notes: str = ""):
    """
    Feature 1: Resumable human-in-the-loop.
    A human calls this after inspecting the checkpoint file. If approved=True, the
    pipeline resumes and produces the redline. If approved=False, the contract is
    rejected and the original (de-masked) text is preserved in the rejection record
    for the legal team's reference.
    """
    with open(checkpoint_path, "r") as f:
        checkpoint = json.load(f)

    trajectory = [{
        "step": 1, "node": "Resume-From-Checkpoint", "action": f"Loaded {checkpoint_path}",
        "status": "Loaded", "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }]

    restored_text = restore(checkpoint["masked_text"], checkpoint["reverse_map"])

    if approved:
        checkpoint["status"] = "APPROVED_BY_HUMAN"
        result_text = f"REVIEWED & APPROVED BY HUMAN (override). Notes: {reviewer_notes}\n\n{restored_text}"
        log_step(trajectory, 2, "Human Reviewer", "Approved despite flagged violation", "APPROVED", {"notes": reviewer_notes})
        status = "STATUS: CONTRACT_APPROVED_AFTER_HUMAN_REVIEW"
    else:
        checkpoint["status"] = "REJECTED_BY_HUMAN"
        result_text = f"REJECTED BY HUMAN REVIEWER. Notes: {reviewer_notes}\n\n{restored_text}"
        log_step(trajectory, 2, "Human Reviewer", "Rejected due to flagged violation", "REJECTED", {"notes": reviewer_notes})
        status = "STATUS: CONTRACT_REJECTED_AFTER_HUMAN_REVIEW"

    checkpoint["reviewer_notes"] = reviewer_notes
    checkpoint["resolved_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    with open(checkpoint_path, "w") as f:
        json.dump(checkpoint, f, indent=2)

    return f"{status}\n\n{result_text}", trajectory


# ---------------------------------------------------------------------------
# NODE 4b: Auto-draft redline (only reached if governance gate clears it)
# ---------------------------------------------------------------------------
def node_auto_draft(document_text, trajectory):
    redline = f"REVIEWED & CLEARED — no policy violations found.\n\n{document_text}"
    log_step(trajectory, 4, "Auto-Draft Generator", "Generated clean redline summary", "Success")
    return redline


# ---------------------------------------------------------------------------
# Orchestration entry point (Feature 2: domain parameter for reuse)
# ---------------------------------------------------------------------------
def run_orchestration_fleet(raw_document_path, domain="contract", use_mock=True):
    trajectory = []
    with open(raw_document_path, "r") as f:
        raw_text = f.read()

    masked_text, reverse_map = node_data_sanitizer(raw_text, trajectory)
    analysis = node_domain_auditor(masked_text, trajectory, domain=domain, use_mock=use_mock)
    decision = node_governance_gate(analysis, trajectory)

    if decision == "TRIGGER_HUMAN_TRIAGE":
        checkpoint_path = node_human_triage(masked_text, reverse_map, analysis, trajectory, domain)
        result = f"STATUS: WAITING_FOR_HUMAN_REVIEW\nCheckpoint: {checkpoint_path}"
    else:
        redline = node_auto_draft(raw_text, trajectory)
        result = f"STATUS: AUTO_DRAFTED\n\n{redline}"
        checkpoint_path = None

    os.makedirs("logs", exist_ok=True)
    with open(TRAJECTORY_LOG_PATH, "w") as f:
        json.dump({"session_id": f"fleet_trace_{int(time.time())}", "domain": domain, "trajectory": trajectory}, f, indent=2)

    return result, checkpoint_path


if __name__ == "__main__":
    # --- Demo 1: vendor contract (flags violations -> human triage) ---
    if not os.path.exists("sample_contract.txt"):
        with open("sample_contract.txt", "w") as f:
            f.write(
                "This agreement between Acme Corp and Globex Inc. shall automatically "
                "renew each year unless terminated. Acme Corp agrees to pay $45,000 annually. "
                "Globex Inc. shall provide uncapped indemnification for all damages."
            )
    print("=== DEMO 1: Vendor Contract (domain=contract) ===")
    result, checkpoint_path = run_orchestration_fleet("sample_contract.txt", domain="contract", use_mock=True)
    print(result)

    if checkpoint_path:
        print("\n=== DEMO 1b: Human approves the flagged contract (resume) ===")
        resumed_result, _ = resume_after_human_review(
            checkpoint_path, approved=True, reviewer_notes="Indemnity cap negotiated separately, acceptable."
        )
        print(resumed_result)

    # --- Demo 2: NDA, same architecture, different domain (Feature 2) ---
    if not os.path.exists("sample_nda.txt"):
        with open("sample_nda.txt", "w") as f:
            f.write(
                "This NDA between Acme Corp and a contractor is non-mutual and includes a "
                "residuals clause permitting use of retained information from memory."
            )
    print("\n=== DEMO 2: NDA (domain=nda, same nodes/architecture reused) ===")
    result2, checkpoint_path2 = run_orchestration_fleet("sample_nda.txt", domain="nda", use_mock=True)
    print(result2)
