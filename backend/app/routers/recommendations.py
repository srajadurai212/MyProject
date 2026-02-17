# from fastapi import APIRouter
# from app.material_engine import identify_materials
# from app.supplier_engine import map_suppliers
# from app.models import PartInput
# import logging


# logger = logging.getLogger(__name__)

# router = APIRouter(
#     prefix="/recommendations",
#     tags=["Recommendations"]
# )

# @router.post("/")
# def get_recommendations(part_input: PartInput):
#     logger.info("Received request")
#     logger.info(f"Part input: {part_input}")

#     materials = identify_materials(part_input)
#     logger.info(f"Identified materials: {materials}")

#     required_strength = None
#     if part_input.functional_requirements:
#         required_strength = part_input.functional_requirements.yield_strength_mpa
#         logger.info(f"Required yield strength: {required_strength}")

#     supplier_results = map_suppliers(
#         materials,
#         required_strength=required_strength,
#         region_pref=part_input.region_preference
#     )

#     logger.info(f"Supplier results: {supplier_results}")

#     return {
#         "part_name": part_input.part_name,
#         "materials": materials,
#         "supplier_recommendations": supplier_results
#     }

from fastapi import APIRouter
from app.material_engine import identify_materials
from app.supplier_engine import map_suppliers
from app.models import PartInput
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/recommendations",
    tags=["Recommendations"]
)

@router.post("/")
def get_recommendations(part_input: PartInput):
    logger.info("Received request")
    logger.info(f"Part input: {part_input}")

    # Identify candidate materials
    materials = identify_materials(part_input)
    logger.info(f"Identified materials: {materials}")

    required_strength = None
    if part_input.functional_requirements:
        required_strength = part_input.functional_requirements.yield_strength_mpa
        logger.info(f"Required yield strength: {required_strength}")

    # Map suppliers using new logic: part_name + material + process + cost + region + yield
    supplier_results = map_suppliers(
        normalized_material_list=materials,
        required_strength=required_strength,
        region_pref=part_input.region_preference
    )

    logger.info(f"Supplier results: {supplier_results}")

    return {
        "part_name": part_input.part_name,
        "materials": materials,
        "supplier_recommendations": supplier_results
    }
