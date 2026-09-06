"""
Shared data models for compliance checking.

Defines ComplianceResult, Violation, RiskLevel, and other shared types
used across SOX, Basel III, and GDPR compliance engines.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional


class RiskLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ViolationCategory(Enum):
    INTERNAL_CONTROL = "internal_control"
    AUDIT_TRAIL = "audit_trail"
    FINANCIAL_REPORTING = "financial_reporting"
    SEGREGATION_OF_DUTIES = "segregation_of_duties"
    CAPITAL_ADEQUACY = "capital_adequacy"
    LIQUIDITY = "liquidity"
    LEVERAGE = "leverage"
    DATA_PRIVACY = "data_privacy"
    CONSENT = "consent"
    DATA_MINIMIZATION = "data_minimization"
    PURPOSE_LIMITATION = "purpose_limitation"


@dataclass
class Violation:
    """A compliance violation."""
    id: str
    category: ViolationCategory
    description: str
    risk_level: RiskLevel
    regulation: str
    remediation: str
    timestamp: float = field(default_factory=lambda: datetime.now().timestamp())
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "category": self.category.value,
            "description": self.description,
            "risk_level": self.risk_level.value,
            "regulation": self.regulation,
            "remediation": self.remediation,
            "timestamp": self.timestamp,
            "metadata": self.metadata,
        }


@dataclass
class ComplianceResult:
    """Result of a compliance check."""
    regulation: str
    score: float  # 0-100
    passed: bool
    violations: list[Violation]
    metrics: dict[str, Any]
    timestamp: float = field(default_factory=lambda: datetime.now().timestamp())
    metadata: dict = field(default_factory=dict)

    @property
    def violation_count(self) -> int:
        return len(self.violations)

    @property
    def critical_count(self) -> int:
        return sum(1 for v in self.violations if v.risk_level == RiskLevel.CRITICAL)

    @property
    def high_count(self) -> int:
        return sum(1 for v in self.violations if v.risk_level == RiskLevel.HIGH)

    def to_dict(self) -> dict:
        return {
            "regulation": self.regulation,
            "score": self.score,
            "passed": self.passed,
            "violation_count": self.violation_count,
            "critical_count": self.critical_count,
            "high_count": self.high_count,
            "violations": [v.to_dict() for v in self.violations],
            "metrics": self.metrics,
            "timestamp": self.timestamp,
        }


@dataclass
class ComplianceReport:
    """Combined compliance report across all regulations."""
    results: list[ComplianceResult]
    overall_score: float
    generated_at: float = field(default_factory=lambda: datetime.now().timestamp())

    @property
    def total_violations(self) -> int:
        return sum(r.violation_count for r in self.results)

    @property
    def critical_violations(self) -> int:
        return sum(r.critical_count for r in self.results)

    @property
    def passed_all(self) -> bool:
        return all(r.passed for r in self.results)

    def summary(self) -> str:
        lines = [
            f"Compliance Report",
            f"=================",
            f"Overall Score: {self.overall_score:.1f}/100",
            f"Total Violations: {self.total_violations}",
            f"Critical: {self.critical_violations}",
            f"Status: {'PASS' if self.passed_all else 'FAIL'}",
            "",
        ]

        for result in self.results:
            status = "PASS" if result.passed else "FAIL"
            lines.append(f"  {result.regulation}: {result.score:.1f}/100 [{status}]")

        return "\n".join(lines)

    def to_dict(self) -> dict:
        return {
            "overall_score": self.overall_score,
            "total_violations": self.total_violations,
            "critical_violations": self.critical_violations,
            "passed_all": self.passed_all,
            "results": [r.to_dict() for r in self.results],
            "generated_at": self.generated_at,
        }
