"""
Export NJIT Badge Classification FACT-SHEET Excel to JSON.

This script reads the master Excel file with 28 real badges and their
pre-classified Category, Type, and Level, then exports to JSON format.
"""

import json
import sys
from pathlib import Path

try:
    import openpyxl
except ImportError:
    print("Error: openpyxl required. Run: pip install openpyxl")
    sys.exit(1)


def excel_to_json(excel_path: str, json_path: str) -> dict:
    """
    Read Excel file and convert badge data to JSON.
    Handles NJIT master dataset format with title row.
    """
    wb = openpyxl.load_workbook(excel_path, data_only=True)

    # Find the sheet with badge data
    ws = None
    for sheet_name in wb.sheetnames:
        temp_ws = wb[sheet_name]
        # Check if this sheet has badge data by looking for "Badge Name" header
        for row in temp_ws.iter_rows(min_row=1, max_row=5, values_only=True):
            if any("badge" in str(cell).lower() and "name" in str(cell).lower()
                   for cell in row if cell):
                ws = temp_ws
                print(f"Found data sheet: {sheet_name}")
                break
        if ws:
            break

    if not ws:
        ws = wb.active
        print(f"Using active sheet: {ws.title}")

    badges = []
    stats = {"total_rows": 0, "valid_badges": 0, "errors": []}

    # Find header row (look for "Badge Name" in first 10 rows)
    header_row = None
    headers = []
    for row_idx, row in enumerate(ws.iter_rows(min_row=1, max_row=15, values_only=True), start=1):
        for cell in row:
            if cell and "badge" in str(cell).lower() and "name" in str(cell).lower():
                header_row = row_idx
                headers = [str(c).strip() if c else None for c in row]
                print(f"Found header row {row_idx}: {[h for h in headers if h][:5]}...")
                break
        if header_row:
            break

    if not header_row:
        # Fallback: use row 2 if row 1 looks like a title
        first_row = list(ws.iter_rows(min_row=1, max_row=1, values_only=True))[0]
        if first_row and first_row[0] and "master" in str(first_row[0]).lower():
            header_row = 2
            headers = [str(c).strip() if c else None for c in list(
                ws.iter_rows(min_row=2, max_row=2, values_only=True))[0]]
            print(f"Using row 2 as header: {[h for h in headers if h][:5]}...")
        else:
            header_row = 1
            headers = [str(c).strip() if c else None for c in first_row]

    # Map Excel columns to badge fields
    column_mapping = {
        "Badge Name": "badge_name",
        "Description": "description",
        "Issuing Department": "issuing_department",
        "Audience": "audience",
        "Context": "context",
        "Has Assessment": "has_assessment",
        "Assessment Type": "assessment_type",
        "Assessment Description": "assessment_description",
        "Completion Criteria": "completion_criteria",
        "Evidence Required": "evidence_required",
        "Bloom's Level": "bloom_levels",
        "Prerequisites": "prerequisites",
        "Is Terminal": "is_terminal",
        "Hours to Complete": "hours_to_complete",
        "Pre-Defined Category": "expected_category",
        "Pre-Defined Type": "expected_type",
        "Pre-Defined Level": "expected_level",
    }

    # Find column indices
    col_indices = {}
    for i, header in enumerate(headers):
        if header:
            for excel_col, json_field in column_mapping.items():
                if excel_col.lower() in header.lower():
                    col_indices[json_field] = i
                    break

    print(f"Mapped {len(col_indices)} fields: {list(col_indices.keys())}")

    if not col_indices:
        # Try fuzzy matching
        for i, header in enumerate(headers):
            if header:
                header_lower = header.lower()
                if "badge" in header_lower and "name" in header_lower:
                    col_indices["badge_name"] = i
                elif "description" in header_lower:
                    col_indices["description"] = i
                elif "department" in header_lower:
                    col_indices["issuing_department"] = i
                elif "audience" in header_lower:
                    col_indices["audience"] = i
                elif "context" in header_lower:
                    col_indices["context"] = i
                elif "assessment" in header_lower and "type" not in header_lower:
                    col_indices["has_assessment"] = i
                elif "type" in header_lower and "assessment" in header_lower:
                    col_indices["assessment_type"] = i
                elif "assessment" in header_lower and "desc" in header_lower:
                    col_indices["assessment_description"] = i
                elif "completion" in header_lower or "criteria" in header_lower:
                    col_indices["completion_criteria"] = i
                elif "evidence" in header_lower:
                    col_indices["evidence_required"] = i
                elif "bloom" in header_lower or "level" in header_lower:
                    col_indices["bloom_levels"] = i
                elif "prereq" in header_lower:
                    col_indices["prerequisites"] = i
                elif "terminal" in header_lower:
                    col_indices["is_terminal"] = i
                elif "hours" in header_lower:
                    col_indices["hours_to_complete"] = i
                elif "category" in header_lower:
                    col_indices["expected_category"] = i
                elif "type" in header_lower and "pre" in header_lower:
                    col_indices["expected_type"] = i
                elif "level" in header_lower and "pre" in header_lower:
                    col_indices["expected_level"] = i

        print(f"Fuzzy mapped {len(col_indices)} fields: {list(col_indices.keys())}")

    # Read data rows (skip header and title rows)
    data_start_row = header_row + 1 if header_row else 3
    for row_idx, row in enumerate(ws.iter_rows(min_row=data_start_row, values_only=True), start=data_start_row):
        stats["total_rows"] += 1

        # Skip empty rows
        if not row or not row[0]:
            continue

        try:
            badge = {"source_format": "master_dataset", "source_row": row_idx}

            # Map fields
            for field, col_idx in col_indices.items():
                value = row[col_idx] if col_idx < len(row) else None

                if field == "badge_name":
                    badge["badge_name"] = str(value) if value else f"Badge_{row_idx}"
                elif field == "description":
                    badge["description"] = str(value) if value else ""
                elif field == "issuing_department":
                    badge["issuing_department"] = str(value) if value else "NJIT"
                elif field == "audience":
                    badge["audience"] = parse_list_field(value)
                elif field == "context":
                    badge["context"] = str(value).lower().replace(" ", "_") if value else ""
                elif field == "has_assessment":
                    badge["has_assessment"] = parse_boolean(value)
                elif field == "assessment_type":
                    badge["assessment_type"] = str(value).lower().replace(" ", "_") if value else None
                elif field == "assessment_description":
                    badge["assessment_description"] = str(value) if value else None
                elif field == "completion_criteria":
                    badge["completion_criteria"] = str(value) if value else ""
                elif field == "evidence_required":
                    badge["evidence_required"] = parse_list_field(value)
                elif field == "bloom_levels":
                    badge["bloom_levels"] = parse_list_field(value)
                elif field == "prerequisites":
                    badge["prerequisites"] = parse_list_field(value) if value else []
                elif field == "is_terminal":
                    badge["is_terminal"] = parse_boolean(value)
                elif field == "hours_to_complete":
                    badge["hours_to_complete"] = int(value) if value else 0
                elif field.startswith("expected_"):
                    badge[field] = str(value) if value else None

            # Validate required fields
            if badge.get("badge_name") and badge["badge_name"] != f"Badge_{row_idx}":
                badges.append(badge)
                stats["valid_badges"] += 1

        except Exception as e:
            stats["errors"].append(f"Row {row_idx}: {str(e)}")

    # Write JSON
    output_path = Path(json_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w") as f:
        json.dump(badges, f, indent=2)

    stats["output_file"] = str(output_path)
    stats["badges"] = badges

    return stats


def parse_list_field(value) -> list:
    """Parse comma-separated or list values."""
    if not value:
        return []
    if isinstance(value, list):
        return [str(v).strip().lower() for v in value if v]
    if isinstance(value, str):
        # Handle comma-separated or newline-separated
        items = []
        for sep in [",", "\n", ";"]:
            if sep in value:
                items = [v.strip().lower() for v in value.split(sep) if v.strip()]
                break
        if not items:
            items = [value.strip().lower()]
        return items
    return [str(value).lower()]


def parse_boolean(value) -> bool:
    """Parse various boolean representations."""
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if not value:
        return False
    value_str = str(value).strip().lower()
    return value_str in ("true", "yes", "1", "y", "x")


def main():
    """Main entry point."""
    base_dir = Path(__file__).parent.parent
    excel_path = base_dir / "data" / "master" / "NJIT_Badge_Classification_FACT-SHEET.xlsx"
    json_path = base_dir / "data" / "master" / "master_badges.json"

    print(f"Reading: {excel_path}")
    print(f"Output: {json_path}")
    print("-" * 50)

    if not excel_path.exists():
        print(f"Error: Excel file not found: {excel_path}")
        sys.exit(1)

    stats = excel_to_json(str(excel_path), str(json_path))

    print(f"\nExport Complete:")
    print(f"  Total rows processed: {stats['total_rows']}")
    print(f"  Valid badges: {stats['valid_badges']}")
    print(f"  Output file: {stats['output_file']}")

    if stats["errors"]:
        print(f"\nErrors ({len(stats['errors'])}):")
        for err in stats["errors"][:5]:
            print(f"  - {err}")

    # Print badge summary
    badges = stats.get("badges", [])
    if badges:
        print(f"\nBadge Summary:")
        categories = {}
        types = {}
        for b in badges:
            cat = b.get("expected_category", "Unknown")
            typ = b.get("expected_type", "Unknown")
            categories[cat] = categories.get(cat, 0) + 1
            types[typ] = types.get(typ, 0) + 1

        print(f"  Categories: {dict(categories)}")
        print(f"  Types: {dict(types)}")


if __name__ == "__main__":
    main()
