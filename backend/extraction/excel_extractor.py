# import pandas as pd

# from backend.classification.sheet_classifier import classify_sheet

# def extract_excel_data(excel_path):

#     sheets_data = {}

#     excel_file = pd.ExcelFile(excel_path)

#     for sheet_name in excel_file.sheet_names:

#         df = pd.read_excel(excel_path, sheet_name=sheet_name)

#         # Convert columns to string

#         df.columns = [str(col) for col in df.columns]

#         # Convert all data to string

#         df = df.astype(str)

#         # Sample rows for classification

#         sample_rows = df.head(5).to_dict(orient="records")

#         # Classify sheet

#         classification = classify_sheet(
#             sheet_name,
#             df.columns,
#             sample_rows
#         )

#         sheets_data[str(sheet_name)] = {

#             "classification": classification,

#             "data": df.fillna("").to_dict(orient="records")
#         }

#     return sheets_data