# from app.data_loader import SUPPLIER_MASTER

# def yield_strength_score(required_strength, supplier_strength):
#     """
#     Returns points based on how close supplier strength is to required strength
#     """
#     difference = abs(supplier_strength - required_strength)
#     if difference <= 5:
#         return 20
#     elif difference <= 10:
#         return 15
#     elif difference <= 20:
#         return 10
#     elif difference <= 50:
#         return 5
#     else:
#         return 0

# def map_suppliers(normalized_material_list, required_strength=None, region_pref=[]):
#     results = []
#     seen_materials = set()

#     for material in normalized_material_list:
#         norm_family = material["normalized_family"]
#         if norm_family in seen_materials:
#             continue
#         seen_materials.add(norm_family)

#         df = SUPPLIER_MASTER[SUPPLIER_MASTER['materials'].str.contains(norm_family, case=False)]
#         suppliers = []
#         for _, row in df.iterrows():
#             score = 40  # material family match

#             # Yield strength proximity scoring
#             if required_strength and 'yield_strength_mpa' in material:
#                 score += yield_strength_score(required_strength, material['yield_strength_mpa'])

#             # Region preference
#             if region_pref and row['region'] in region_pref:
#                 score += 20

#             suppliers.append({
#                 "supplier_name": row['supplier_name'],
#                 "country": row['country'],
#                 "region": row['region'],
#                 "score": score
#             })

#         # Sort by score descending, top 5
#         suppliers = sorted(suppliers, key=lambda x: x['score'], reverse=True)[:5]
#         results.append({
#             "material": norm_family,
#             "suppliers": suppliers
#         })
#     return results

from app.data_loader import SUPPLIER_MASTER


def yield_strength_score(required_strength, material_strength):
    """
    Returns points based on how close material strength is to required strength
    """
    if not required_strength or not material_strength:
        return 0

    diff = abs(material_strength - required_strength)
    if diff <= 5:
        return 20
    elif diff <= 10:
        return 15
    elif diff <= 20:
        return 10
    elif diff <= 50:
        return 5
    return 0


def map_suppliers(normalized_material_list, required_strength=None, region_pref=[]):
    """
    Supplier mapping based on:
    - Material family
    - Region
    - Yield strength fit
    - Cost (POC)
    """
    results = []
    seen_materials = set()

    for material in normalized_material_list:
        material_family = material["material_family"]  # ✅ USE THIS
        normalized_family = material["normalized_family"]

        if normalized_family in seen_materials:
            continue
        seen_materials.add(normalized_family)

        # ✅ CORRECT FILTER
        df = SUPPLIER_MASTER[
            SUPPLIER_MASTER['materials']
            .str.contains(material_family, case=False, na=False)
        ]

        suppliers = []
        for _, row in df.iterrows():
            score = 40  # Material match

            # Yield strength proximity
            score += yield_strength_score(
                required_strength,
                material.get("yield_strength_mpa")
            )

            # Region preference
            if region_pref and row["region"] in region_pref:
                score += 20

            suppliers.append({
                "supplier_name": row["supplier_name"],
                "country": row["country"],
                "region": row["region"],
                "score": score,
                "cost_usd": row["cost_usd"]
            })

        # Sort: Score DESC, Cost ASC
        suppliers = sorted(
            suppliers,
            key=lambda x: (-x["score"], x["cost_usd"])
        )[:5]

        results.append({
            "material": normalized_family,
            "suppliers": suppliers
        })

    return results

