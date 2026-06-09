import pandas as pd


def extract_policy_block(
    excel_path,
    sheet_name,
    start_row,
    end_row
):

    df = pd.read_excel(
        excel_path,
        sheet_name=sheet_name,
        header=None,
        dtype=str
    )

    start_idx = start_row - 1
    end_idx = end_row

    block = df.iloc[
        start_idx:end_idx
    ].copy()

    block["__excel_row__"] = (
        block.index + 1
    )

    block = block.fillna("")

    print(
        block["__excel_row__"].tolist()
    )

    return block