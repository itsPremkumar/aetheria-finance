"""
Unified compliance engine.

Provides a single interface for running SOX, Basel III, and GDPR
compliance checks with unified reporting.
"""

from __future__ import annotations
from typing import Any, Optional

from .models import ComplianceReport, ComplianceResult
from .sox import SOXComplianceEngine
from .basel_iii import BaselIIIComplianceEngine
from .gdpr import GDPRComplianceEngine
from .reporting import ComplianceReporter


class ComplianceEngine:
    """Unified compliance checking engine."""

    def __init__(self):
        self.sox_engine = SOXComplianceEngine()
        self.basel_engine = BaselIIIComplianceEngine()
        self.gdpr_engine = GDPRComplianceEngine()
        self.reporter = ComplianceReporter()

    def check_sox(
        self,
        financial_data: dict,
        controls: Optional[dict] = None,
    ) -> ComplianceResult:
        """Run SOX compliance check."""
        return self.sox_engine.check(financial_data, controls)

    def check_basel(self, capital_data: dict) -> ComplianceResult:
        """Run Basel III compliance check."""
        return self.basel_engine.check(capital_data)

    def check_gdpr(
        self,
        personal_data: dict,
        processing_activities: Optional[list] = None,
    ) -> ComplianceResult:
        """Run GDPR compliance check."""
        return self.gdpr_engine.check(personal_data, processing_activities)

    def check_all(
        self,
        financial_data: Optional[dict] = None,
        capital_data: Optional[dict] = None,
        personal_data: Optional[dict] = None,
        controls: Optional[dict] = None,
        processing_activities: Optional[list] = None,
    ) -> ComplianceReport:
        """Run all compliance checks and generate a unified report."""
        results = []

        if financial_data:
            results.append(self.check_sox(financial_data, controls))

        if capital_data:
            results.append(self.check_basel(capital_data))

        if personal_data:
            results.append(self.check_gdpr(personal_data, processing_activities))

        overall_score = sum(r.score for r in results) / len(results) if results else 0

        return ComplianceReport(
            results=results,
            overall_score=overall_score,
        )

    def generate_report(
        self,
        financial_data: Optional[dict] = None,
        capital_data: Optional[dict] = None,
        personal_data: Optional[dict] = None,
        controls: Optional[dict] = None,
        processing_activities: Optional[list] = None,
    ) -> ComplianceReport:
        """Generate a unified compliance report."""
        report = self.check_all(
            financial_data, capital_data, personal_data,
            controls, processing_activities,
        )
        return report
