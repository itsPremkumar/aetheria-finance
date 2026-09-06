"""
SOX (Sarbanes-Oxley) compliance engine.

Checks internal controls, audit trail integrity, financial reporting
accuracy, and segregation of duties.
"""

from __future__ import annotations
import time
import uuid
from typing import Any, Optional

from .models import (
    ComplianceResult,
    RiskLevel,
    Violation,
    ViolationCategory,
)


class SOXComplianceEngine:
    """SOX compliance checking engine."""

    def __init__(self):
        self._thresholds = {
            "min_score": 70,
            "max_critical_violations": 0,
            "max_high_violations": 2,
        }

    def check(
        self,
        financial_data: dict,
        controls: Optional[dict] = None,
    ) -> ComplianceResult:
        """Run SOX compliance check."""
        violations = []

        # Check internal controls
        violations.extend(self._check_internal_controls(controls or {}))

        # Check audit trail integrity
        violations.extend(self._check_audit_trail(financial_data))

        # Check financial reporting accuracy
        violations.extend(self._check_financial_reporting(financial_data))

        # Check segregation of duties
        violations.extend(self._check_segregation_of_duties(controls or {}))

        # Calculate score
        score = self._calculate_score(violations)

        return ComplianceResult(
            regulation="SOX",
            score=score,
            passed=score >= self._thresholds["min_score"],
            violations=violations,
            metrics={
                "critical_count": sum(1 for v in violations if v.risk_level == RiskLevel.CRITICAL),
                "high_count": sum(1 for v in violations if v.risk_level == RiskLevel.HIGH),
                "medium_count": sum(1 for v in violations if v.risk_level == RiskLevel.MEDIUM),
                "low_count": sum(1 for v in violations if v.risk_level == RiskLevel.LOW),
            },
        )

    def _check_internal_controls(self, controls: dict) -> list[Violation]:
        """Check internal controls are in place."""
        violations = []

        if not controls.get("documented"):
            violations.append(Violation(
                id=str(uuid.uuid4())[:8],
                category=ViolationCategory.INTERNAL_CONTROL,
                description="Internal controls are not documented",
                risk_level=RiskLevel.HIGH,
                regulation="SOX",
                remediation="Document all internal controls and maintain evidence",
            ))

        if not controls.get("tested"):
            violations.append(Violation(
                id=str(uuid.uuid4())[:8],
                category=ViolationCategory.INTERNAL_CONTROL,
                description="Internal controls have not been tested",
                risk_level=RiskLevel.HIGH,
                regulation="SOX",
                remediation="Perform regular control testing and document results",
            ))

        if not controls.get("effective"):
            violations.append(Violation(
                id=str(uuid.uuid4())[:8],
                category=ViolationCategory.INTERNAL_CONTROL,
                description="Internal controls are not operating effectively",
                risk_level=RiskLevel.CRITICAL,
                regulation="SOX",
                remediation="Remediate control deficiencies immediately",
            ))

        return violations

    def _check_audit_trail(self, financial_data: dict) -> list[Violation]:
        """Check audit trail integrity."""
        violations = []

        if not financial_data.get("audit_trail"):
            violations.append(Violation(
                id=str(uuid.uuid4())[:8],
                category=ViolationCategory.AUDIT_TRAIL,
                description="No audit trail present",
                risk_level=RiskLevel.CRITICAL,
                regulation="SOX",
                remediation="Implement comprehensive audit trail for all financial transactions",
            ))

        if not financial_data.get("tamper_proof"):
            violations.append(Violation(
                id=str(uuid.uuid4())[:8],
                category=ViolationCategory.AUDIT_TRAIL,
                description="Audit trail is not tamper-proof",
                risk_level=RiskLevel.HIGH,
                regulation="SOX",
                remediation="Implement write-once storage and cryptographic integrity checks",
            ))

        return violations

    def _check_financial_reporting(self, financial_data: dict) -> list[Violation]:
        """Check financial reporting accuracy."""
        violations = []

        if financial_data.get("material_misstatement"):
            violations.append(Violation(
                id=str(uuid.uuid4())[:8],
                category=ViolationCategory.FINANCIAL_REPORTING,
                description="Material misstatement detected in financial reports",
                risk_level=RiskLevel.CRITICAL,
                regulation="SOX",
                remediation="Restate financial reports and investigate root cause",
            ))

        if not financial_data.get("gaap_compliant"):
            violations.append(Violation(
                id=str(uuid.uuid4())[:8],
                category=ViolationCategory.FINANCIAL_REPORTING,
                description="Financial reports are not GAAP compliant",
                risk_level=RiskLevel.HIGH,
                regulation="SOX",
                remediation="Align financial reporting with GAAP standards",
            ))

        return violations

    def _check_segregation_of_duties(self, controls: dict) -> list[Violation]:
        """Check segregation of duties."""
        violations = []

        if not controls.get("segregation_enforced"):
            violations.append(Violation(
                id=str(uuid.uuid4())[:8],
                category=ViolationCategory.SEGREGATION_OF_DUTIES,
                description="Segregation of duties is not enforced",
                risk_level=RiskLevel.HIGH,
                regulation="SOX",
                remediation="Implement role-based access controls with duty separation",
            ))

        return violations

    def _calculate_score(self, violations: list[Violation]) -> float:
        """Calculate compliance score."""
        score = 100.0

        for violation in violations:
            if violation.risk_level == RiskLevel.CRITICAL:
                score -= 25
            elif violation.risk_level == RiskLevel.HIGH:
                score -= 15
            elif violation.risk_level == RiskLevel.MEDIUM:
                score -= 10
            elif violation.risk_level == RiskLevel.LOW:
                score -= 5

        return max(0, score)
