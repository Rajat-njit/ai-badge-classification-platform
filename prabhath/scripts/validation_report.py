"""
Validation Report Generator for NJIT Badge Classification.

This script validates the classification rules against the 28 real badges
from the master dataset and generates a detailed report showing:
- Match rate for Category, Type, and Level
- Mismatches with expected vs predicted values
- Overall accuracy statistics
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from data.schemas.badge_fact_sheet import BadgeFactSheet, create_fact_sheet_from_dict
from src.classification.step1_category import classify_category, get_category_explanation
from src.classification.step2_type import classify_type, get_type_explanation
from src.classification.step3_level import classify_level, get_level_explanation


class ValidationReport:
    """Generate validation report comparing predicted vs expected classifications."""

    def __init__(self, badges: List[dict]):
        self.badges = badges
        self.results = []
        self.stats = {
            "total": len(badges),
            "category": {"correct": 0, "incorrect": 0, "mismatches": []},
            "type": {"correct": 0, "incorrect": 0, "mismatches": []},
            "level": {"correct": 0, "incorrect": 0, "mismatches": []},
        }

    def run_validation(self) -> dict:
        """Run classification on all badges and compare with expected values."""
        for badge_data in self.badges:
            result = self._validate_badge(badge_data)
            self.results.append(result)

        # Calculate accuracy percentages
        for field in ["category", "type", "level"]:
            total = self.stats[field]["correct"] + self.stats[field]["incorrect"]
            if total > 0:
                self.stats[field]["accuracy"] = round(
                    self.stats[field]["correct"] / total * 100, 2
                )

        return self.stats

    def _validate_badge(self, badge_data: dict) -> dict:
        """Validate a single badge classification."""
        result = {
            "badge_name": badge_data.get("badge_name", "Unknown"),
            "expected_category": badge_data.get("expected_category"),
            "expected_type": badge_data.get("expected_type"),
            "expected_level": badge_data.get("expected_level"),
        }

        # Create fact sheet and classify
        try:
            fact_sheet = create_fact_sheet_from_dict(badge_data)

            predicted_category = classify_category(fact_sheet)
            predicted_type = classify_type(fact_sheet)
            predicted_level = classify_level(fact_sheet, predicted_type)  

            result["predicted_category"] = predicted_category
            result["predicted_type"] = predicted_type
            result["predicted_level"] = predicted_level

            result["category_explanation"] = get_category_explanation(fact_sheet, predicted_category)
            result["type_explanation"] = get_type_explanation(fact_sheet, predicted_type)  
            result["level_explanation"] = get_level_explanation(fact_sheet, predicted_type, predicted_level)  

            # Check matches
            for field, expected_key, predicted in [
                ("category", "expected_category", predicted_category),
                ("type", "expected_type", predicted_type),
                ("level", "expected_level", predicted_level),
            ]:
                expected = result.get(expected_key)
                if not expected:
                    continue  # Skip if no expected value
                # Normalize for comparison
                norm_expected = self._normalize(expected)
                norm_predicted = self._normalize(predicted)
                
                if norm_expected == norm_predicted:
                    self.stats[field]["correct"] += 1
                    result[f"{field}_match"] = True
                else:
                    self.stats[field]["incorrect"] += 1
                    result[f"{field}_match"] = False
                    self.stats[field]["mismatches"].append({
                        "badge": result["badge_name"],
                        "expected": expected,
                        "predicted": predicted,
                    })

        except Exception as e:
            result["error"] = str(e)

        return result

    def _normalize(self, value: str) -> str:
        """Normalize string for comparison."""
        return str(value).strip().lower().replace(" & ", " and ")

    def generate_report(self) -> str:
        """Generate formatted text report."""
        lines = [
            "=" * 70,
            "NJIT BADGE CLASSIFICATION VALIDATION REPORT",
            "=" * 70,
            f"Total Badges Validated: {self.stats['total']}",
            "",
            "ACCURACY SUMMARY",
            "-" * 70,
        ]

        for field in ["category", "type", "level"]:
            stats = self.stats[field]
            accuracy = stats.get("accuracy", 0)
            lines.append(
                f"{field.upper():12} | Correct: {stats['correct']:2d} | "
                f"Incorrect: {stats['incorrect']:2d} | Accuracy: {accuracy:5.1f}%"
            )

        lines.extend(["", "MISMATCH DETAILS", "-" * 70])

        for field in ["category", "type", "level"]:
            mismatches = self.stats[field]["mismatches"]
            if mismatches:
                lines.extend(["", f"{field.upper()} Mismatches:"])
                for m in mismatches[:10]:  # Show first 10
                    lines.append(
                        f"  • {m['badge'][:40]:40s} | "
                        f"Expected: {m['expected'][:20]:20s} | "
                        f"Predicted: {m['predicted'][:20]}")
                if len(mismatches) > 10:
                    lines.append(f"  ... and {len(mismatches) - 10} more")

        lines.extend(["", "=" * 70])
        return "\n".join(lines)

    def save_json_report(self, output_path: str):
        """Save detailed JSON report."""
        report = {
            "statistics": self.stats,
            "results": self.results,
        }
        with open(output_path, "w") as f:
            json.dump(report, f, indent=2)


def main():
    """Main entry point."""
    base_dir = Path(__file__).parent.parent
    master_json = base_dir / "data" / "master" / "master_badges.json"
    output_txt = base_dir / "validation_report.txt"
    output_json = base_dir / "validation_report.json"

    print(f"Loading: {master_json}")

    if not master_json.exists():
        print(f"Error: Master badges file not found: {master_json}")
        print("Run export_badges_to_json.py first!")
        sys.exit(1)

    with open(master_json) as f:
        badges = json.load(f)

    print(f"Loaded {len(badges)} badges")
    print("Running validation...")
    print("-" * 70)

    validator = ValidationReport(badges)
    validator.run_validation()

    # Print and save text report
    report = validator.generate_report()
    print(report)

    with open(output_txt, "w") as f:
        f.write(report)
    print(f"\nText report saved: {output_txt}")

    # Save JSON report
    validator.save_json_report(str(output_json))
    print(f"JSON report saved: {output_json}")

    # Overall accuracy
    total = validator.stats["total"]
    cat_acc = validator.stats["category"].get("accuracy", 0)
    type_acc = validator.stats["type"].get("accuracy", 0)
    level_acc = validator.stats["level"].get("accuracy", 0)
    overall = round((cat_acc + type_acc + level_acc) / 3, 2)

    print(f"\nOVERALL ACCURACY: {overall}%")

    return 0 if overall >= 80 else 1


if __name__ == "__main__":
    sys.exit(main())
