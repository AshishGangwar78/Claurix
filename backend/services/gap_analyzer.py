import json
import os
import re
from collections import Counter

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter


def classify_uw_remark(
    uw_remark
):

    if not uw_remark:

        return "PARTIALLY_AGREED"

    remark = str(
        uw_remark
    ).lower().strip()

    not_agreed_keywords = [

        "not agreed",

        "not covered",

        "excluded",

        "declined",

        "rejected",

        "not acceptable",

        "not available"

    ]

    for keyword in not_agreed_keywords:

        if keyword in remark:

            return "NOT_AGREED"

    agreed_keywords = [

        "agreed",

        "covered",

        "accepted",

        "yes"

    ]

    for keyword in agreed_keywords:

        if keyword in remark:

            return "AGREED"

    return "PARTIALLY_AGREED"


def process_policy(
    policy_json
):

    for clause in policy_json.get(
        "clauses",
        []
    ):

        clause["remark_status"] = (
            classify_uw_remark(
                clause.get(
                    "uw_remark",
                    ""
                )
            )
        )

    return policy_json


def json_to_excel(json_file, excel_file):

    with open(json_file, "r", encoding="utf-8") as file:
        data = json.load(file)

    clauses = data.get("clauses", [])
    companies = []

    for clause in clauses:
        for insurer in clause.get("insurers", []):
            company = insurer.get("company", "Unknown Insurer")
            if company not in companies:
                companies.append(company)

    workbook = Workbook()
    summary_sheet = workbook.active
    summary_sheet.title = "Summary"
    comparison_sheet = workbook.create_sheet("Comparison")

    _build_summary_sheet(summary_sheet, data, companies)
    _build_comparison_sheet(comparison_sheet, data, companies)

    os.makedirs(os.path.dirname(excel_file), exist_ok=True)
    workbook.save(excel_file)

    print(f"[EXCEL EXPORTED] {excel_file}")


def _build_summary_sheet(sheet, data, companies):
    policy_name = data.get("policy", "Policy")
    clauses = data.get("clauses", [])

    sheet.merge_cells(start_row=1, start_column=1, end_row=1, end_column=6)
    title = sheet.cell(row=1, column=1, value=f"Insurance Gap Analysis - {policy_name}")
    title.font = Font(bold=True, size=16, color="FFFFFF")
    title.fill = PatternFill("solid", fgColor="1F4E78")
    title.alignment = Alignment(horizontal="center", vertical="center")

    sheet.cell(row=3, column=1, value="Total Clauses")
    sheet.cell(row=3, column=2, value=len(clauses))

    headers = ["Insurer", "Agreed", "Not Agreed", "Partial", "Blank/Unknown", "Total"]
    for column, header in enumerate(headers, start=1):
        cell = sheet.cell(row=5, column=column, value=header)
        _style_header_cell(cell)

    for row, company in enumerate(companies, start=6):
        counts = Counter()

        for clause in clauses:
            insurer = _find_insurer(clause, company)
            status = _normalize_status(insurer.get("remark_status", "") if insurer else "")
            counts[status] += 1

        values = [
            _display_company_name(company),
            counts["AGREED"],
            counts["NOT_AGREED"],
            counts["PARTIAL"],
            counts["BLANK"],
            sum(counts.values()),
        ]

        for column, value in enumerate(values, start=1):
            cell = sheet.cell(row=row, column=column, value=value)
            cell.border = _thin_border()
            cell.alignment = Alignment(vertical="top", wrap_text=True)

        _style_status_count(sheet.cell(row=row, column=2), "AGREED")
        _style_status_count(sheet.cell(row=row, column=3), "NOT_AGREED")
        _style_status_count(sheet.cell(row=row, column=4), "PARTIAL")
        _style_status_count(sheet.cell(row=row, column=5), "BLANK")

    for column, width in enumerate([35, 14, 14, 14, 16, 12], start=1):
        sheet.column_dimensions[get_column_letter(column)].width = width

    sheet.freeze_panes = "A6"
    sheet.sheet_view.showGridLines = False


def _build_comparison_sheet(sheet, data, companies):
    policy_name = data.get("policy", "Policy")
    clauses = data.get("clauses", [])
    total_columns = 3 + (len(companies) * 2)

    sheet.merge_cells(start_row=1, start_column=1, end_row=1, end_column=total_columns)
    title = sheet.cell(row=1, column=1, value=f"Merged Policy Comparison - {policy_name}")
    title.font = Font(bold=True, size=16, color="FFFFFF")
    title.fill = PatternFill("solid", fgColor="1F4E78")
    title.alignment = Alignment(horizontal="center", vertical="center")

    sheet.merge_cells(start_row=3, start_column=1, end_row=3, end_column=3)
    policy_cell = sheet.cell(row=3, column=1, value="Policy Requirement")
    _style_group_header_cell(policy_cell, "5B9BD5")

    column = 4
    for company in companies:
        sheet.merge_cells(start_row=3, start_column=column, end_row=3, end_column=column + 1)
        company_cell = sheet.cell(row=3, column=column, value=_display_company_name(company))
        _style_group_header_cell(company_cell, "70AD47")
        column += 2

    headers = ["Excel Row", "Clause", "Requirement"]
    for company in companies:
        headers.extend(["UW Remark", "Status"])

    for column, header in enumerate(headers, start=1):
        cell = sheet.cell(row=4, column=column, value=header)
        _style_header_cell(cell)

    for row_index, clause in enumerate(clauses, start=5):
        values = [
            clause.get("excel_row", ""),
            clause.get("clause", ""),
            clause.get("requirement", ""),
        ]

        for company in companies:
            insurer = _find_insurer(clause, company)
            values.extend([
                insurer.get("uw_remark", "") if insurer else "",
                insurer.get("remark_status", "") if insurer else "",
            ])

        for column, value in enumerate(values, start=1):
            cell = sheet.cell(row=row_index, column=column, value=value)
            cell.border = _thin_border()
            cell.alignment = Alignment(vertical="top", wrap_text=True)

            if column >= 5 and (column - 5) % 2 == 0:
                _style_status_cell(cell)

        sheet.row_dimensions[row_index].height = 45

    sheet.freeze_panes = "A5"
    sheet.auto_filter.ref = f"A4:{get_column_letter(total_columns)}{max(len(clauses) + 4, 4)}"
    sheet.sheet_view.showGridLines = False

    widths = [12, 42, 24]
    for _company in companies:
        widths.extend([38, 16])

    for column, width in enumerate(widths, start=1):
        sheet.column_dimensions[get_column_letter(column)].width = width

    sheet.row_dimensions[1].height = 28
    sheet.row_dimensions[3].height = 24
    sheet.row_dimensions[4].height = 28


def _display_company_name(company):
    name = str(company)
    name = re.sub(r"\.(xlsx|xls|json)$", "", name, flags=re.IGNORECASE)
    name = re.sub(r"^\d{8}_\d{6}_", "", name)
    return name.replace("_", " ").strip() or "Unknown Insurer"


def _find_insurer(clause, company):
    for insurer in clause.get("insurers", []):
        if insurer.get("company", "Unknown Insurer") == company:
            return insurer

    return None


def _normalize_status(status):
    value = str(status or "").strip().upper().replace(" ", "_")

    if value in {"AGREED", "ACCEPTED", "YES"}:
        return "AGREED"

    if value in {"NOT_AGREED", "NOT_ACCEPTED", "NO", "REJECTED"}:
        return "NOT_AGREED"

    if value in {"PARTIAL", "PARTIALLY_AGREED", "PARTIAL_AGREED"}:
        return "PARTIAL"

    return "BLANK"


def _style_header_cell(cell):
    cell.font = Font(bold=True, color="FFFFFF")
    cell.fill = PatternFill("solid", fgColor="305496")
    cell.border = _thin_border()
    cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)


def _style_group_header_cell(cell, color):
    cell.font = Font(bold=True, color="FFFFFF")
    cell.fill = PatternFill("solid", fgColor=color)
    cell.border = _thin_border()
    cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)


def _style_status_cell(cell):
    status = _normalize_status(cell.value)
    fills = {
        "AGREED": "C6EFCE",
        "NOT_AGREED": "FFC7CE",
        "PARTIAL": "FFEB9C",
        "BLANK": "D9EAD3",
    }
    font_colors = {
        "AGREED": "006100",
        "NOT_AGREED": "9C0006",
        "PARTIAL": "9C6500",
        "BLANK": "666666",
    }

    cell.value = status.replace("_", " ").title() if status != "BLANK" else ""
    cell.fill = PatternFill("solid", fgColor=fills[status])
    cell.font = Font(bold=True, color=font_colors[status])
    cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)


def _style_status_count(cell, status):
    fills = {
        "AGREED": "C6EFCE",
        "NOT_AGREED": "FFC7CE",
        "PARTIAL": "FFEB9C",
        "BLANK": "D9EAD3",
    }
    cell.fill = PatternFill("solid", fgColor=fills[status])
    cell.alignment = Alignment(horizontal="center", vertical="center")


def _thin_border():
    side = Side(style="thin", color="D9E2F3")
    return Border(left=side, right=side, top=side, bottom=side)


def merge_policy_files(policy_files):

    policies = []

    for file_path in policy_files:
        with open(file_path, "r", encoding="utf-8") as file:
            policies.append(json.load(file))

    if not policies:
        return {}

    master_policy = policies[0]

    # Create row lookup for every policy
    policy_maps = []

    for policy in policies:

        row_map = {}

        for clause in policy.get("clauses", []):

            row = clause.get(
                "source",
                {}
            ).get(
                "excel_row"
            )

            if row is not None:
                row_map[row] = clause

        policy_maps.append(
            {
                "company": policy.get("company", ""),
                "row_map": row_map
            }
        )

    merged_clauses = []

    for master_clause in master_policy.get("clauses", []):

        excel_row = master_clause.get(
            "source",
            {}
        ).get(
            "excel_row"
        )

        insurers = []

        for policy_map in policy_maps:

            clause = policy_map[
                "row_map"
            ].get(
                excel_row
            )

            if clause:

                insurers.append({
                    "company":
                        policy_map["company"],

                    "uw_remark":
                        clause.get(
                            "uw_remark",
                            ""
                        ),

                    "remark_status":
                        clause.get(
                            "remark_status",
                            ""
                        ),

                    "source":
                        clause.get(
                            "source",
                            {}
                        )
                })

            else:

                insurers.append({
                    "company":
                        policy_map["company"],

                    "uw_remark":
                        "",

                    "remark_status":
                        "",

                    "source":
                        {}
                })

        merged_clauses.append({

            "excel_row":
                excel_row,

            "clause":
                master_clause.get(
                    "clause",
                    ""
                ),

            "requirement":
                master_clause.get(
                    "requirement",
                    ""
                ),

            "insurers":
                insurers

        })

    return {

        "policy":
            master_policy.get(
                "policy",
                ""
            ),

        "clauses":
            merged_clauses

    }
