# Feature: Spec-Driven Contract Lifecycle Triage Engine

  Scenario: Processing an incoming third-party service contract
    Given an unreviewed contract document is submitted for review
    When the Data Sanitizer Skill identifies company names, individual names, and currency values
    And deterministic mask filters remove sensitive identifying details before any LLM call
    And the Policy Auditor Skill cross-references the sanitized clauses against internal policy rules
    Then if an unapproved "Indemnity" or "Automatic Renewal" clause is flagged, halt execution and route to Human-in-the-Loop review
    But if the contract adheres to policy, generate a clean redline summary automatically

  Scenario: Policy auditor finds no violations
    Given a sanitized contract with no flagged clauses
    When the Governance Gate evaluates the analysis
    Then the system proceeds directly to auto-draft without human intervention

  Scenario: Human reviewer overrides a flagged clause
    Given a contract was halted for human review
    When the reviewer marks the clause as acceptable
    Then the system resumes the pipeline and produces the redline summary
