"""
Compliance reporting module.

Generates unified compliance reports with risk scoring and remediation recommendations.
"""

from __future__ import annotations
from datetime import datetime
from typing import Any, Optional

from .models import ComplianceReport, ComplianceResult, RiskLevel


class ComplianceReporter:
    """Generate unified compliance reports."""

    def generate(self, report: ComplianceReport) -> str:
        """Generate a human-readable compliance report."""
        return report.summary()

    def generate_detailed(self, report: ComplianceReport) -> str:
        """Generate a detailed compliance report."""
        lines = [
            "COMPLIANCE REPORT",
            "=" * 50,
            f"Generated: {datetime.fromtimestamp(report.generated_at).strftime('%Y-%m-%d %H:%M:%S')}",
            f"Overall Score: {report.overall_score:.1f}/100",
            f"Total Violations: {report.total_violations}",
            f"Critical: {report.critical_violations}",
            f"Status: {'PASS' if report.passed_all else 'FAIL'}",
            "",
        ]

        for result in report.results:
            lines.append(f"  {result.regulation}")
            lines.append(f"  {'-' * 40}")
            lines.append(f"  Score: {result.score:.1f}/100")
            lines.append(f"  Status: {'PASS' if result.passed else 'FAIL'}")
            lines.append(f"  Violations: {result.violation_count}")

            if result.violations:
                lines.append(f"  Details:")
                for v in result.violations:
                    lines.append(f"    - [{v.risk_level.value.upper()}] {v.description}")
                    lines.append(f"      Remediation: {v.remediation}")

            lines.append("")

        return "\n".join(lines)

    def generate_remediation_plan(self, report: ComplianceReport) -> list[dict]:
        """Generate a prioritized remediation plan."""
        plan = []

        for result in report.results:
            for violation in result.violations:
                priority = self._priority(violation.risk_level)
                plan.append({
                    "priority": priority,
                    "regulation": result.regulation,
                    "violation": violation.description,
                    "remediation": violation.remediation,
                    "risk_level": violation.risk_level.value,
                })

        plan.sort(key=lambda x: x["priority"])
        return plan

    def _priority(self, risk_level: RiskLevel) -> int:
        """Get priority for a risk level (lower = higher priority)."""
        priorities = {
            RiskLevel.CRITICAL: 1,
            RiskLevel.HIGH: 2,
            RiskLevel.MEDIUM: 3,
            RiskLevel.LOW: 4,
        }
        return priorities.get(risk_level, 5)
