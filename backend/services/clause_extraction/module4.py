from backend.utils.excel_helpers import column_number_to_excel


#----------------------------------------------------------#
#Module 4 for final json output
#NO AI just python
def get_column_value(

    columns,

    target_column

):

    for cell in columns:

        if cell["column_index"] == target_column:

            return cell["value"]

    return ""


def build_policy_json(
    company_name,
    policy_name,
    sheet_name,
    clause_rows,
    column_info
):
    #here we have to change if clause column,reqiurement, uw remarks not found
    #raise exceptions
    clause_column = column_info.get(
        "clause_column"
    )

    requirement_column = column_info.get(
        "requirement_column"
    )

    uw_remark_column = column_info.get(
        "uw_remark_column"
    )

    clauses = []
    
    for row in clause_rows:

        clause_text = get_column_value(

            row["columns"],

            clause_column

        )

        requirement = get_column_value(

            row["columns"],

            requirement_column

        )

        uw_remark = get_column_value(

            row["columns"],

            uw_remark_column

        )

        clauses.append({

            "clause":
                clause_text,

            "requirement":
                requirement,

            "uw_remark":
                uw_remark,

            "source": {

                "sheet_name":
                    sheet_name,

                "excel_row":
                    row["excel_row"],

                "clause_cell":
                    f"{column_number_to_excel(clause_column)}{row['excel_row']}",

                "requirement_cell":
                    f"{column_number_to_excel(requirement_column)}{row['excel_row']}",

                "uw_remark_cell":
                    f"{column_number_to_excel(uw_remark_column)}{row['excel_row']}"

            }

        })
    
    return {

        "company":
            company_name,

        "policy":
            policy_name,
        
        "column_mapping": {

            "clause_column":
                clause_column,

            "requirement_column":
                requirement_column,

            "uw_remark_column":
                uw_remark_column

        },

        "clauses":
            clauses

    }
#final result stores in the rsult folder now.
