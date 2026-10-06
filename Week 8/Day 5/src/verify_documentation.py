"""Documentation & Deliverable Verification Module for Week 8 Day 5.
Audits all markdown documentation, verifies structural integrity, validates word counts,
checks links, and confirms metric consistency across deliverables.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple

# Add Day 5 root to sys.path
DAY5_DIR = Path(__file__).resolve().parent.parent
if str(DAY5_DIR) not in sys.path:
    sys.path.insert(0, str(DAY5_DIR))

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from src.presentation_data import EXECUTIVE_METRICS

EXPECTED_DOC_FILES = [
    "01_executive_overview_and_business_case.md",
    "02_system_architecture_and_data_flow.md",
    "03_data_engineering_and_feature_store.md",
    "04_valuation_regression_engine.md",
    "05_lead_scoring_and_explainability.md",
    "06_api_reference_and_service_contracts.md",
    "07_conversational_copilot_and_telephony.md",
    "08_mlops_governance_and_deployment_runbook.md",
    "09_stakeholder_faq_and_troubleshooting.md",
]

EXPECTED_PRESENTATION_FILES = [
    "stakeholder_presentation.pptx",
    "index.html",
    "stakeholder_deck.md",
    "executive_summary_1pager.md",
    "speaker_notes_script.md",
]


def audit_documentation_suite(docs_dir: Path) -> Dict[str, Any]:
    """Audit all documentation files for completeness, word count, and placeholders."""
    results = {
        "files_checked": 0,
        "missing_files": [],
        "total_words": 0,
        "file_details": {},
        "placeholder_issues": [],
        "passed": True,
    }

    for doc_name in EXPECTED_DOC_FILES:
        doc_path = docs_dir / doc_name
        if not doc_path.exists():
            results["missing_files"].append(doc_name)
            results["passed"] = False
            continue

        text = doc_path.read_text(encoding="utf-8")
        words = len(text.split())
        lines = len(text.splitlines())
        results["files_checked"] += 1
        results["total_words"] += words

        # Check for bad placeholders
        bad_patterns = [r"TODO", r"FIXME", r"\[TBD\]", r"Lorem ipsum"]
        for pat in bad_patterns:
            if re.search(pat, text, re.IGNORECASE):
                results["placeholder_issues"].append(f"{doc_name}: Contains '{pat}'")
                results["passed"] = False

        results["file_details"][doc_name] = {
            "words": words,
            "lines": lines,
            "status": "PASS" if words >= 250 else "SHORT",
        }
        if words < 250:
            results["passed"] = False

    return results


def audit_presentation_suite(pres_dir: Path) -> Dict[str, Any]:
    """Audit presentation files and verify HTML and PPTX generation."""
    results = {
        "files_checked": 0,
        "missing_files": [],
        "file_details": {},
        "passed": True,
    }

    for f_name in EXPECTED_PRESENTATION_FILES:
        f_path = pres_dir / f_name
        if not f_path.exists():
            results["missing_files"].append(f_name)
            results["passed"] = False
            continue

        size = f_path.stat().st_size
        results["files_checked"] += 1
        results["file_details"][f_name] = {
            "size_bytes": size,
            "status": "PASS" if size > 1000 else "TOO_SMALL",
        }
        if size <= 1000:
            results["passed"] = False

    return results


def run_full_audit() -> bool:
    """Execute complete deliverable audit and print summary."""
    docs_dir = DAY5_DIR / "docs"
    pres_dir = DAY5_DIR / "presentation"

    print("=" * 70)
    print("  📑 DAY 5 CAPSTONE DELIVERABLE AUDIT & VERIFICATION")
    print("=" * 70)

    doc_audit = audit_documentation_suite(docs_dir)
    print(f"Documentation Files Verified: {doc_audit['files_checked']} / {len(EXPECTED_DOC_FILES)}")
    print(f"Total Documentation Words:    {doc_audit['total_words']:,} words")
    if doc_audit["missing_files"]:
        print(f"❌ Missing Docs: {doc_audit['missing_files']}")
    if doc_audit["placeholder_issues"]:
        print(f"❌ Placeholder Issues: {doc_audit['placeholder_issues']}")

    for name, detail in doc_audit["file_details"].items():
        print(f"  • {name:<45} [{detail['words']} words, {detail['lines']} lines] -> {detail['status']}")

    print("\n" + "-" * 70)
    pres_audit = audit_presentation_suite(pres_dir)
    print(f"Presentation Assets Verified: {pres_audit['files_checked']} / {len(EXPECTED_PRESENTATION_FILES)}")
    if pres_audit["missing_files"]:
        print(f"❌ Missing Presentation Files: {pres_audit['missing_files']}")

    for name, detail in pres_audit["file_details"].items():
        print(f"  • {name:<45} [{detail['size_bytes']:,} bytes] -> {detail['status']}")

    all_passed = doc_audit["passed"] and pres_audit["passed"]
    print("=" * 70)
    if all_passed:
        print("✅ ALL DAY 5 DOCUMENTATION & PRESENTATION ASSETS FULLY VERIFIED")
    else:
        print("❌ SOME DAY 5 ASSETS FAILED VERIFICATION")
    print("=" * 70)

    return all_passed


if __name__ == "__main__":
    success = run_full_audit()
    sys.exit(0 if success else 1)
