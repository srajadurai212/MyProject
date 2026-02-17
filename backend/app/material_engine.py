# from typing import List
# from app.data_loader import MATERIAL_KB, MATERIAL_NORM

# def identify_materials(part_input) -> List[dict]:
#     """
#     Identify candidate materials for the part
#     """
#     df = MATERIAL_KB

#     df_filtered = df[df['process'].str.lower() == part_input.manufacturing_process.lower()]

#     if part_input.functional_requirements and part_input.functional_requirements.yield_strength_mpa:
#         df_filtered = df_filtered[df_filtered['yield_strength_mpa'] <= part_input.functional_requirements.yield_strength_mpa]

#     if part_input.known_material:
#         df_filtered = df_filtered[df_filtered['material_family'].str.contains(part_input.known_material, case=False)]
#     elif part_input.material_hint:
#         df_filtered = df_filtered[df_filtered['material_family'].str.contains(part_input.material_hint, case=False)]

#     normalized_list = []
#     for _, row in df_filtered.iterrows():
#         norm_row = MATERIAL_NORM[MATERIAL_NORM['raw_grade'] == row['grade']]
#         normalized_family = norm_row['normalized_material_family'].values[0] if not norm_row.empty else row['material_family']
#         normalized_list.append({
#             "material_family": row['material_family'],
#             "grade": row['grade'],
#             "normalized_family": normalized_family,
#             "yield_strength_mpa": row['yield_strength_mpa']
#         })
#     return normalized_list

from typing import List
from app.data_loader import MATERIAL_KB, MATERIAL_NORM

def identify_materials(part_input) -> List[dict]:
    """
    Identify candidate materials for the part based on:
    - Part Name
    - Manufacturing Process
    - Yield Strength (if provided)
    """
    df = MATERIAL_KB

    # Match by part name (case-insensitive)
    df_filtered = df[df['part_name'].str.lower() == part_input.part_name.lower()]

    # Match by manufacturing process
    df_filtered = df_filtered[df_filtered['process'].str.lower() == part_input.manufacturing_process.lower()]

    # Filter by yield strength if provided
    if part_input.functional_requirements and part_input.functional_requirements.yield_strength_mpa:
        df_filtered = df_filtered[df_filtered['yield_strength_mpa'] <= part_input.functional_requirements.yield_strength_mpa]

    # Normalize material grades using corrected MATERIAL_NORM
    normalized_list = []
    for _, row in df_filtered.iterrows():
        norm_row = MATERIAL_NORM[MATERIAL_NORM['raw_grade'].str.strip() == row['grade'].strip()]
        normalized_family = norm_row['normalized_material_family'].values[0] if not norm_row.empty else row['material_family']

        normalized_list.append({
            "material_family": row['material_family'],
            "grade": row['grade'],
            "normalized_family": normalized_family,
            "yield_strength_mpa": row['yield_strength_mpa']
        })

    return normalized_list
