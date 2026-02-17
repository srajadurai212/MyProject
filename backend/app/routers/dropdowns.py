from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.postgresq import (
    get_material_category_options,
    get_material_spec_options,
    get_surface_finishes,
    get_labour_types,
    get_op_stage_options,
    get_web_allowance_options,
    get_bead_type_options,
    get_active_machines,
    get_press_machines,
    get_material_types,
    # Add these new imports
    get_all_material_categories,
    add_user_material_category,
    delete_user_material_category,
    update_user_material_category,
)

router = APIRouter()

# -------------------------
# PYDANTIC MODELS
# -------------------------
class UserMaterialCategory(BaseModel):
    category_name: str
    density: float

class UpdateMaterialCategory(BaseModel):
    category_name: str
    new_density: float

# -------------------------
# MATERIAL DROPDOWNS
# -------------------------
@router.get("/material-categories")
def material_categories():
    return get_material_category_options()

@router.get("/material-spec")
def material_specs():
    return get_material_spec_options()

@router.get("/surface-finishes")
def surface_finishes():
    return get_surface_finishes()

@router.get("/material_types")
def material_types():
    return get_material_types()

# -------------------------
# PRODUCTION DROPDOWNS
# -------------------------
@router.get("/labour-types")
def labour_types():
    return get_labour_types()

@router.get("/op-stages")
def op_stages():
    return get_op_stage_options()

# -------------------------
# SHEET / STRIP DROPDOWNS
# -------------------------
@router.get("/web-allowances")
def web_allowances():
    return get_web_allowance_options()

@router.get("/bead-types")
def bead_types():
    return get_bead_type_options()

# -------------------------
# MACHINES
# -------------------------
@router.get("/machines/active")
def active_machines():
    return get_active_machines()

@router.get("/machines/press")
def press_machines():
    return get_press_machines()

# -------------------------
# MATERIAL CATEGORY MANAGEMENT
# -------------------------
@router.get("/material-categories/all")
def all_material_categories():
    """Get all material categories with their densities and source"""
    return get_all_material_categories()

@router.post("/material-categories/user")
def create_user_material_category(data: UserMaterialCategory):
    """
    Add a new user-defined material category
    
    Example request body:
    {
        "category_name": "Copper",
        "density": 0.0000896
    }
    """
    try:
        category_id = add_user_material_category(
            data.category_name, 
            data.density
        )
        return {
            "success": True,
            "category_id": category_id,
            "category_name": data.category_name,
            "density": data.density
        }
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        raise HTTPException(500, f"Failed to create category: {str(e)}")

@router.patch("/material-categories/user")
def update_user_category_density(data: UpdateMaterialCategory):
    """
    Update density for a user-defined material category
    
    Example request body:
    {
        "category_name": "Copper",
        "new_density": 0.0000900
    }
    """
    try:
        update_user_material_category(data.category_name, data.new_density)
        return {
            "success": True,
            "category_name": data.category_name,
            "new_density": data.new_density
        }
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        raise HTTPException(500, f"Failed to update category: {str(e)}")

@router.delete("/material-categories/user/{category_name}")
def delete_user_category(category_name: str):
    """
    Delete (soft delete) a user-defined material category
    """
    try:
        delete_user_material_category(category_name)
        return {
            "success": True,
            "deleted_category": category_name
        }
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        raise HTTPException(500, f"Failed to delete category: {str(e)}")
    
    