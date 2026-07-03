"""Run with: python3 test_main.py"""
import sys
import os
import json
sys.path.append(os.path.join(os.path.dirname(__file__), "skills", "data_sanitizer"))

from mask_regex import sanitize, restore
from main import (
    node_governance_gate,
    mock_llm_auditor,
    run_orchestration_fleet,
    resume_after_human_review,
)


def test_sanitizer_masks_and_restores():
    text = "Acme Corp will pay $1,000 to Globex Inc."
    masked, rmap = sanitize(text)
    assert "$1,000" not in masked
    assert "Acme Corp" not in masked
    assert restore(masked, rmap) == text


def test_governance_gate_triggers_on_violation():
    assert node_governance_gate("Rule violation: automatic renewal detected.", []) == "TRIGGER_HUMAN_TRIAGE"


def test_governance_gate_clears_clean_contract():
    assert node_governance_gate("No policy violations detected.", []) == "PROCEED_TO_AUTO_DRAFT"


def test_mock_auditor_flags_autorenew():
    result = mock_llm_auditor("this contract will auto-renew annually", "")
    assert "violation" in result.lower()


def test_feature1_resumable_human_review():
    """Feature 1: resume_after_human_review should let a human approve a flagged contract."""
    with open("sample_contract.txt", "w") as f:
        f.write("This deal shall automatically renew with uncapped indemnification.")
    result, checkpoint_path = run_orchestration_fleet("sample_contract.txt", domain="contract", use_mock=True)
    assert checkpoint_path is not None
    assert os.path.exists(checkpoint_path)

    resumed_result, _ = resume_after_human_review(checkpoint_path, approved=True, reviewer_notes="ok")
    assert "APPROVED" in resumed_result

    with open(checkpoint_path) as f:
        data = json.load(f)
    assert data["status"] == "APPROVED_BY_HUMAN"


def test_feature2_multi_domain_reuse():
    """Feature 2: same pipeline functions handle both contract and NDA domains."""
    with open("sample_nda.txt", "w") as f:
        f.write("This NDA is non-mutual and includes a residuals clause.")
    result, checkpoint_path = run_orchestration_fleet("sample_nda.txt", domain="nda", use_mock=True)
    assert "WAITING_FOR_HUMAN_REVIEW" in result
    assert checkpoint_path is not None


def test_feature3_token_logging():
    """Feature 3: sanitizer logs token counts before/after masking."""
    trajectory = []
    from main import node_data_sanitizer
    masked, rmap = node_data_sanitizer("Acme Corp will pay $1,000 to Globex Inc.", trajectory)
    sanitizer_entry = trajectory[0]
    assert "tokens_before_sanitization" in sanitizer_entry
    assert "tokens_after_sanitization" in sanitizer_entry
    assert "tokens_saved" in sanitizer_entry


if __name__ == "__main__":
    tests = [
        test_sanitizer_masks_and_restores,
        test_governance_gate_triggers_on_violation,
        test_governance_gate_clears_clean_contract,
        test_mock_auditor_flags_autorenew,
        test_feature1_resumable_human_review,
        test_feature2_multi_domain_reuse,
        test_feature3_token_logging,
    ]
    for t in tests:
        t()
        print(f"PASS: {t.__name__}")
    print("\nAll tests passed.")
