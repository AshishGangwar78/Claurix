# import numpy as np
# from sentence_transformers import SentenceTransformer
# from sklearn.metrics.pairwise import cosine_similarity

# # Load embedding model

# model = SentenceTransformer("all-MiniLM-L6-v2")

# # Real RFQ sheet business categories

# SHEET_TYPES = {

#     "rfq_master_details": [

#         "broker rfq slip policy period proposed occupancy risk location correspondence address insured name",
#         "master insurance policy details",
#         "policy information and insured details",
#         "rfq package details and coverage overview"

#     ],

#     "asset_summary": [

#         "sum total amount sfsp premium rate insured values annexure",
#         "asset value summary by location",
#         "insured value aggregation",
#         "premium calculation summary"

#     ],

#     "asset_register": [

#         "asset name qty location unit price total amount insurance section",
#         "detailed insured asset schedule",
#         "property and equipment list",
#         "asset register with insured values"

#     ],

#     "stock_declaration": [

#         "stock values warehouse location stock sum insured",
#         "inventory declaration and stock exposure",
#         "stock insured values by location",
#         "warehouse stock information"

#     ],

#     "policy_summary": [

#         "summary of insured values and premium",
#         "location wise value summary",
#         "insurance premium summary",
#         "aggregated risk summary"

#     ],

#     "risk_locations": [

#         "warehouse addresses risk locations city state premises",
#         "insured premises and addresses",
#         "location address information",
#         "risk location mapping"

#     ]
# }

# # Precompute embeddings once

# PRECOMPUTED_REF_EMBEDDINGS = {

#     sheet_type: model.encode(examples)

#     for sheet_type, examples in SHEET_TYPES.items()
# }

# def classify_sheet(

#     sheet_name,
#     columns,
#     sample_rows,
#     confidence_threshold=0.35

# ):

#     # Convert columns into text

#     columns_text = " ".join([str(col) for col in columns])

#     # Convert first 5 rows into text

#     sample_text = " ".join([str(row) for row in sample_rows[:5]])

#     # Combine everything

#     combined_text = f"""

#     Sheet Name: {sheet_name}

#     Columns: {columns_text}

#     Sample Data: {sample_text}

#     """

#     # Generate embedding for current sheet

#     sheet_embedding = model.encode([combined_text])

#     # Default classification

#     best_match = "unknown"

#     best_score = confidence_threshold

#     # Compare against all sheet types

#     for sheet_type, example_embeddings in PRECOMPUTED_REF_EMBEDDINGS.items():

#         # Calculate cosine similarity

#         similarities = cosine_similarity(
#             sheet_embedding,
#             example_embeddings
#         )[0]

#         # Find highest similarity

#         max_score = np.max(similarities)

#         # Update best match

#         if max_score > best_score:

#             best_score = max_score

#             best_match = sheet_type

#     return {

#         "sheet_type": best_match,

#         "confidence": round(float(best_score), 4)
#     }




