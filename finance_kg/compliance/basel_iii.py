"""
Basel III compliance engine.

Checks capital adequacy, liquidity coverage, leverage ratio,
and net stable funding requirements.
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


class BaselIIIComplianceEngine:
    """Basel III compliance checking engine."""

    def __init__(self):
        self._thresholds = {
            "min_score": 70,
            "min_car": 0.08,  # Minimum Capital Adequacy Ratio: 8%
            "min_lcr": 1.0,   # Minimum Liquidity Coverage Ratio: 100%
            "max_leverage": 0.03,  # Maximum Leverage Ratio: 3%
            "min_nsfr": 1.0,  # Minimum Net Stable Funding Ratio: 100%
        }

    def check(self, capital_data: dict) -> ComplianceResult:
        """Run Basel III compliance check."""
        violations = []

        # Check Capital Adequacy Ratio (CAR)
        violations.extend(self._check_capital_adequacy(capital_data))

        # Check Liquidity Coverage Ratio (LCR)
        violations.extend(self._check_liquidity_coverage(capital_data))

        # Check Leverage Ratio
        violations.extend(self._check_leverage_ratio(capital_data))

        # Check Net Stable Funding Ratio (NSFR)
        violations.extend(self._check_stable_funding(capital_data))

        # Calculate score
        score = self._calculate_score(violations)

        # Calculate metrics
        metrics = self._calculate_metrics(capital_data)

        return ComplianceResult(
            regulation="Basel III",
            score=score,
            passed=score >= self._thresholds["min_score"],
            violations=violations,
            metrics=metrics,
        )

    def _check_capital_adequacy(self, capital_data: dict) -> list[Violation]:
        """Check Capital Adequacy Ratio (CAR) >= 8%."""
        violations = []
        car = capital_data.get("capital_adequacy_ratio", 0)

        if car < self._thresholds["min_car"]:
            violations.append(Violation(
                id=str(uuid.uuid4())[:8],
                category=ViolationCategory.CAPITAL_ADEQUACY,
                description=f"Capital Adequacy Ratio {car:.2%} is below minimum {self._thresholds['min_car']:.0%}",
                risk_level=RiskLevel.CRITICAL,
                regulation="Basel III",
                remediation="Increase Tier 1 capital or reduce risk-weighted assets",
                metadata={"current": car, "minimum": self._thresholds["min_car"]},
            ))

        if car < 0.10:  # Below 10% is a warning
            violations.append(Violation(
                id=str(uuid.uuid4())[:8],
                category=ViolationCategory.CAPITAL_ADEQUACY,
                description=f"Capital Adequacy Ratio {car:.2%} is below recommended 10%",
                risk_level=RiskLevel.MEDIUM,
                regulation="Basel III",
                remediation="Consider increasing capital buffer",
            ))

        return violations

    def _check_liquidity_coverage(self, capital_data: dict) -> list[Violation]:
        """Check Liquidity Coverage Ratio (LCR) >= 100%."""
        violations = []
        lcr = capital_data.get("liquidity_coverage_ratio", 0)

        if lcr < self._thresholds["min_lcr"]:
            violations.append(Violation(
                id=str(uuid.uuid4())[:8],
                category=ViolationCategory.LIQUIDITY,
                description=f"Liquidity Coverage Ratio {lcr:.2%} is below minimum {self._thresholds['min_lcr']:.0%}",
                risk_level=RiskLevel.CRITICAL,
                regulation="Basel III",
                remediation="Increase high-quality liquid assets or reduce net cash outflows",
                metadata={"current": lcr, "minimum": self._thresholds["min_lcr"]},
            ))

        return violations

    def _check_leverage_ratio(self, capital_data: dict) -> list[Violation]:
        """Check Leverage Ratio <= 3%."""
        violations = []
        leverage = capital_data.get("leverage_ratio", float('inf'))

        if leverage > self._thresholds["max_leverage"]:
            violations.append(Violation(
                id=str(uuid.uuid4())[:8],
                category=ViolationCategory.LEVERAGE,
                description=f"Leverage Ratio {leverage:.2%} exceeds maximum {self._thresholds['max_leverage']:.0%}",
                risk_level=RiskLevel.HIGH,
                regulation="Basel III",
                remediation="Reduce leverage by decreasing exposure or increasing Tier 1 capital",
                metadata={"current": leverage, "maximum": self._thresholds["max_leverage"]},
            ))

        return violations

    def _check_stable_funding(self, capital_data: dict) -> list[Violation]:
        """Check Net Stable Funding Ratio (NSFR) >= 100%."""
        violations = []
        nsfr = capital_data.get("net_stable_funding_ratio", 0)

        if nsfr < self._thresholds["min_nsfr"]:
            violations.append(Violation(
                id=str(uuid.uuid4())[:8],
                category=ViolationCategory.LIQUIDITY,
                description=f"Net Stable Funding Ratio {nsfr:.2%} is below minimum {self._thresholds['min_nsfr']:.0%}",
                risk_level=RiskLevel.CRITICAL,
                regulation="Basel III",
                remediation="Increase stable funding sources or reduce required stable funding",
                metadata={"current": nsfr, "minimum": self._thresholds["min_nsfr"]},
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

    def _calculate_metrics(self, capital_data: dict) -> dict[str, float]:
        """Calculate key Basel III metrics."""
        return {
            "car": capital_data.get("capital_adequacy_ratio", 0),
            "lcr": capital_data.get("liquidity_coverage_ratio", 0),
            "leverage_ratio": capital_data.get("leverage_ratio", 0),
            "nsfr": capital_data.get("net_stable_funding_ratio", 0),
            "tier_1_capital": capital_data.get("tier_1_capital", 0),
            "risk_weighted_assets": capital_data.get("risk_weighted_assets", 0),
        }
