"""
GDPR (General Data Protection Regulation) compliance engine.

Checks data privacy, consent management, right to erasure,
data minimization, and purpose limitation.
"""

from __future__ import annotations
import uuid
from typing import Any, Optional

from .models import (
    ComplianceResult,
    RiskLevel,
    Violation,
    ViolationCategory,
)


class GDPRComplianceEngine:
    """GDPR compliance checking engine."""

    def __init__(self):
        self._thresholds = {
            "min_score": 80,
            "max_high_violations": 1,
        }

    def check(
        self,
        personal_data: dict,
        processing_activities: Optional[list] = None,
    ) -> ComplianceResult:
        """Run GDPR compliance check."""
        violations = []

        # Check data privacy
        violations.extend(self._check_data_privacy(personal_data))

        # Check consent management
        violations.extend(self._check_consent(personal_data))

        # Check data minimization
        violations.extend(self._check_data_minimization(personal_data))

        # Check purpose limitation
        violations.extend(self._check_purpose_limitation(processing_activities or []))

        # Check right to erasure
        violations.extend(self._check_right_to_erasure(personal_data))

        # Calculate score
        score = self._calculate_score(violations)

        return ComplianceResult(
            regulation="GDPR",
            score=score,
            passed=score >= self._thresholds["min_score"],
            violations=violations,
            metrics={
                "consent_coverage": self._consent_coverage(personal_data),
                "data_minimization_score": self._minimization_score(personal_data),
                "processing_activities": len(processing_activities or []),
            },
        )

    def _check_data_privacy(self, personal_data: dict) -> list[Violation]:
        """Check data privacy protections."""
        violations = []

        if not personal_data.get("encrypted"):
            violations.append(Violation(
                id=str(uuid.uuid4())[:8],
                category=ViolationCategory.DATA_PRIVACY,
                description="Personal data is not encrypted at rest",
                risk_level=RiskLevel.CRITICAL,
                regulation="GDPR",
                remediation="Implement AES-256 encryption for all personal data at rest",
            ))

        if not personal_data.get("pseudonymized"):
            violations.append(Violation(
                id=str(uuid.uuid4())[:8],
                category=ViolationCategory.DATA_PRIVACY,
                description="Personal data is not pseudonymized",
                risk_level=RiskLevel.HIGH,
                regulation="GDPR",
                remediation="Apply pseudonymization techniques to reduce identifiability",
            ))

        if not personal_data.get("access_controlled"):
            violations.append(Violation(
                id=str(uuid.uuid4())[:8],
                category=ViolationCategory.DATA_PRIVACY,
                description="Access to personal data is not properly controlled",
                risk_level=RiskLevel.HIGH,
                regulation="GDPR",
                remediation="Implement role-based access controls with audit logging",
            ))

        return violations

    def _check_consent(self, personal_data: dict) -> list[Violation]:
        """Check consent management."""
        violations = []
        consent_records = personal_data.get("consent_records", [])

        if not consent_records:
            violations.append(Violation(
                id=str(uuid.uuid4())[:8],
                category=ViolationCategory.CONSENT,
                description="No consent records found",
                risk_level=RiskLevel.CRITICAL,
                regulation="GDPR",
                remediation="Obtain and document consent for all personal data processing",
            ))

        return violations

    def _check_data_minimization(self, personal_data: dict) -> list[Violation]:
        """Check data minimization principle."""
        violations = []
        collected_fields = personal_data.get("collected_fields", [])
        necessary_fields = personal_data.get("necessary_fields", [])

        if collected_fields and necessary_fields:
            excess = set(collected_fields) - set(necessary_fields)
            if excess:
                violations.append(Violation(
                    id=str(uuid.uuid4())[:8],
                    category=ViolationCategory.DATA_MINIMIZATION,
                    description=f"Excess data collected: {', '.join(excess)}",
                    risk_level=RiskLevel.MEDIUM,
                    regulation="GDPR",
                    remediation="Collect only data that is strictly necessary for the stated purpose",
                ))

        return violations

    def _check_purpose_limitation(self, processing_activities: list) -> list[Violation]:
        """Check purpose limitation."""
        violations = []

        for activity in processing_activities:
            if not activity.get("purpose"):
                violations.append(Violation(
                    id=str(uuid.uuid4())[:8],
                    category=ViolationCategory.PURPOSE_LIMITATION,
                    description="Processing activity without documented purpose",
                    risk_level=RiskLevel.HIGH,
                    regulation="GDPR",
                    remediation="Document the specific purpose for each processing activity",
                ))

        return violations

    def _check_right_to_erasure(self, personal_data: dict) -> list[Violation]:
        """Check right to erasure (right to be forgotten) compliance."""
        violations = []

        if not personal_data.get("erasure_procedure"):
            violations.append(Violation(
                id=str(uuid.uuid4())[:8],
                category=ViolationCategory.DATA_PRIVACY,
                description="No procedure for handling erasure requests",
                risk_level=RiskLevel.HIGH,
                regulation="GDPR",
                remediation="Implement a documented procedure for handling data subject erasure requests within 30 days",
            ))

        return violations

    def _calculate_score(self, violations: list[Violation]) -> float:
        """Calculate compliance score."""
        score = 100.0

        for violation in violations:
            if violation.risk_level == RiskLevel.CRITICAL:
                score -= 20
            elif violation.risk_level == RiskLevel.HIGH:
                score -= 15
            elif violation.risk_level == RiskLevel.MEDIUM:
                score -= 10
            elif violation.risk_level == RiskLevel.LOW:
                score -= 5

        return max(0, score)

    def _consent_coverage(self, personal_data: dict) -> float:
        """Calculate consent coverage ratio."""
        records = personal_data.get("consent_records", [])
        total = personal_data.get("total_data_subjects", 0)
        if total == 0:
            return 0.0
        return len(records) / total

    def _minimization_score(self, personal_data: dict) -> float:
        """Calculate data minimization score."""
        collected = len(personal_data.get("collected_fields", []))
        necessary = len(personal_data.get("necessary_fields", []))
        if collected == 0:
            return 1.0
        return necessary / collected
