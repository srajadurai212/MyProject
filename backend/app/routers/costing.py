
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Any, Optional
from app.services.postgresq import (
    get_part_cost_by_id,
    get_part_operations_by_part_id,
    get_part_cost_summary,
    update_part_cost_field_raw,
    update_operation_field_raw,
    get_available_op_stages_for_part,
    add_operation_to_part,
    delete_operation,
    get_part_id_from_operation,
    get_all_field_statuses_for_part,
    get_edited_fields_for_part,
    get_edited_fields_for_operation,
    clear_field_edit_flag,
    clear_operation_field_edit_flag,
    mark_field_as_edited,
    mark_operation_field_as_edited,
    save_part_data,
    get_all_saved_parts,
    get_unsaved_parts,
    get_saved_parts_dropdown,
    get_stp_file_path,
    engine,
)

from sqlalchemy import text
from fastapi.responses import FileResponse, StreamingResponse
import json
import io
import csv
from datetime import datetime

router = APIRouter()

# =========================
# REQUEST BODY MODELS
# =========================
class PartFieldUpdate(BaseModel):
    part_id: int
    field: str
    value: Any
    edited_by: Optional[str] = None 

class OperationFieldUpdate(BaseModel):
    operation_id: int
    field: str
    value: Any
    edited_by: Optional[str] = None

class SavePartRequest(BaseModel):
    part_id: int
    saved_by: Optional[str] = None

# =========================
# BASIC PART DATA (TOP)
# =========================
@router.get("/part/{part_id}")
def get_part(part_id: int):
    return get_part_cost_by_id(part_id)

# =========================
# RAW MATERIAL COST
# =========================
@router.get("/raw-material/{part_id}")
def raw_material_cost(part_id: int):
    part = get_part_cost_by_id(part_id)
    return {
        "strip_size_width_mm": part["strip_size_width_mm"],
        "strip_size_pitch_mm": part["strip_size_pitch_mm"],
        "no_of_part_per_blank": part["no_of_part_per_blank"],
        "blank_wt": part["blank_wt"],
        "rm_cost_per_kg": part["rm_cost_per_kg"],
        "rm_cost_per_part": part["rm_cost_per_part"],
        "scrap_wt": part["scrap_wt"],
        "scrap_cost_per_kg": part["scrap_cost_per_kg"],
        "scrap_cost_per_part": part["scrap_cost_per_part"],
        "net_rm_cost": part["net_rm_cost"],
        "outer_perimeter_mm": part["outer_perimeter_mm"],
        "approx_blank_ton": part["approx_blank_ton"],
    }

# =========================
# PROCESS COST
# =========================

@router.get("/process/{part_id}")
def process_cost(part_id: int):
    return get_part_operations_by_part_id(part_id)

@router.get("/process-stages/{part_id}")
def get_available_op_stages(part_id: int):
    """
    Get available OP stages for UI tabs (OP1, OP2, etc.)
    """
    operations = get_part_operations_by_part_id(part_id)
    stages = [op['op_stage'] for op in operations if op.get('is_active')]
    
    return {
        "part_cost_id": part_id,
        "available_stages": sorted(set(stages)),  # Unique: ['OP1', 'OP2']
        "total_operations": len(operations)
    }

@router.post("/process/{part_id}/{op_stage}")
def add_operation(part_id: int, op_stage: str, op_name: str = ""):
    """
    Add new operation stage (OP3, OP4, ..., CF)
    Auto-triggers recalculation of all costs
    """
    # Validate available (not already used)
    available_stages = get_available_op_stages_for_part(part_id)
    if op_stage.upper() not in [s.upper() for s in available_stages]:
        raise HTTPException(400, f"OP stage '{op_stage}' already exists or invalid")
    
    operation_id = add_operation_to_part(part_id, op_stage.upper(), op_name)
    
    return {
        "success": True,
        "part_cost_id": part_id,
        "new_operation_id": operation_id,
        "op_stage": op_stage.upper(),
        "available_stages": get_available_op_stages_for_part(part_id)
    }


@router.delete("/process/{part_id}/{operation_id}")
def delete_operation_endpoint(part_id: int, operation_id: int):
    """
    Delete operation (soft delete: is_active=FALSE)
    Auto-triggers cost recalculation
    """
    # Verify operation belongs to this part
    operations = get_part_operations_by_part_id(part_id)
    if not any(op['id'] == operation_id for op in operations):
        raise HTTPException(404, f"Operation {operation_id} not complete for part {part_id}")
    
    delete_operation(operation_id)
    
    return {
        "success": True,
        "part_cost_id": part_id,
        "deleted_operation_id": operation_id,
        "remaining_operations": len(get_part_operations_by_part_id(part_id))
    }

# =========================
# OTHER + TOTAL COST
# =========================
@router.get("/other/{part_id}")
def other_cost(part_id: int):
    part = get_part_cost_by_id(part_id)
    return {
        "total_process_cost_jpy": part["total_process_cost_jpy"],
        "total_rm_process_cost_jpy": part["total_rm_process_cost_jpy"],
        "rejection": part["rejection"],
        "material_oh_cost": part["material_oh_cost"],
        "die_maint": part["die_maint"],
        "mpo": part["mpo"],
        "sga": part["sga"],
        "profit_on_material": part["profit_on_material"],
        "profit_on_process": part["profit_on_process"],
        "total_cost": part["total_cost"],
        "total_part_cost_jpy": part["total_part_cost_jpy"],
        "rate_per_kg": part["rate_per_kg"],
    }

# Update the existing endpoints
@router.patch("/part-field")
def update_part_field(update: PartFieldUpdate):
    """
    Update a single field in part_cost table
    AUTO-TRIGGERS full recalculation of all dependent values
    Returns the updated part data with edit tracking info
    """
    try:
        print(f"Updating part {update.part_id}: {update.field} = {update.value}")
        
        # This automatically recalculates and tracks the edit!
        update_part_cost_field_raw(
            update.part_id, 
            update.field, 
            update.value,
            update.edited_by
        )
        
        # Get fresh data after recalculation
        updated_part = get_part_cost_by_id(update.part_id)
        updated_operations = get_part_operations_by_part_id(update.part_id)
        edited_fields = get_edited_fields_for_part(update.part_id)
        
        return {
            "status": "updated_and_recalculated",
            "part_id": update.part_id,
            "field": update.field,
            "value": update.value,
            "updated_data": {
                "part": updated_part,
                "operations": updated_operations,
                "edited_fields": edited_fields  # ← NEW: which fields are edited
            }
        }
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        print(f"Error updating part field: {e}")
        raise HTTPException(500, f"Update failed: {str(e)}")


@router.patch("/operation-field")
def update_operation_field(update: OperationFieldUpdate):
    """
    Update a single field in part_operations table
    AUTO-TRIGGERS full recalculation of all dependent values
    Returns the updated data with edit tracking info
    """
    try:
        print(f"Updating operation {update.operation_id}: {update.field} = {update.value}")
        
        # Get part_id before update
        part_id = get_part_id_from_operation(update.operation_id)
        
        # This automatically recalculates and tracks the edit!
        update_operation_field_raw(
            update.operation_id, 
            update.field, 
            update.value,
            update.edited_by
        )
        
        # Get fresh data after recalculation
        updated_part = get_part_cost_by_id(part_id)
        updated_operations = get_part_operations_by_part_id(part_id)
        operation_edits = get_edited_fields_for_operation(update.operation_id)
        
        return {
            "status": "updated_and_recalculated",
            "operation_id": update.operation_id,
            "field": update.field,
            "value": update.value,
            "updated_data": {
                "part": updated_part,
                "operations": updated_operations,
                "operation_edited_fields": operation_edits  # ← NEW
            }
        }
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        print(f"Error updating operation field: {e}")
        raise HTTPException(500, f"Update failed: {str(e)}")


# NEW ENDPOINTS for field status tracking

@router.get("/field-status/{part_id}")
def get_field_status(part_id: int):
    """
    Get comprehensive field status for a part
    Shows which fields are:
    - Manually edited (should be highlighted)
    - Auto-calculated
    - System readonly
    
    Response includes edit timestamps and user info
    """
    try:
        status = get_all_field_statuses_for_part(part_id)
        return status
    except Exception as e:
        raise HTTPException(500, f"Failed to get field status: {str(e)}")


@router.delete("/field-edit-flag/{part_id}/{field_name}")
def reset_field_to_auto(part_id: int, field_name: str):
    """
    Reset a field to auto-calculation mode
    Removes the "edited" flag and recalculates
    
    Use this when user wants to revert a manual edit
    """
    try:
        clear_field_edit_flag(part_id, field_name)
        
        # Trigger recalculation
        from app.services.postgresql import recalculate_part_cost
        recalculate_part_cost(part_id)
        
        return {
            "success": True,
            "part_id": part_id,
            "field": field_name,
            "message": "Field reset to auto-calculation"
        }
    except Exception as e:
        raise HTTPException(500, f"Failed to reset field: {str(e)}")


@router.delete("/operation-field-edit-flag/{operation_id}/{field_name}")
def reset_operation_field_to_auto(operation_id: int, field_name: str):
    """
    Reset an operation field to auto-calculation mode
    """
    try:
        clear_operation_field_edit_flag(operation_id, field_name)
        
        # Get part_id and trigger recalculation
        part_id = get_part_id_from_operation(operation_id)
        from app.services.postgresql import recalculate_part_cost
        recalculate_part_cost(part_id)
        
        return {
            "success": True,
            "operation_id": operation_id,
            "field": field_name,
            "message": "Field reset to auto-calculation"
        }
    except Exception as e:
        raise HTTPException(500, f"Failed to reset field: {str(e)}")
    
@router.get("/export/{part_id}/json")
def export_part_json(part_id: int):
    """
    Export complete part cost data as JSON file
    
    Returns a downloadable JSON file with all part data
    """
    try:
        summary = get_part_cost_summary(part_id)
        
        if not summary:
            raise HTTPException(404, f"Part {part_id} not found")
        
        # Add export metadata
        export_data = {
            "export_date": datetime.now().isoformat(),
            "part_cost_id": part_id,
            "data": summary
        }
        
        # Create JSON string
        json_str = json.dumps(export_data, indent=2, default=str)
        
        # Create file response
        part_number = summary['part_info']['part_number']
        filename = f"{part_number}_cost_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        return StreamingResponse(
            io.BytesIO(json_str.encode()),
            media_type="application/json",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
        
    except Exception as e:
        raise HTTPException(500, f"Export failed: {str(e)}")

# =========================
# SAVE/RETRIEVE ENDPOINTS
# =========================

@router.post("/save")
def save_part(request: SavePartRequest):
    """
    Save part data after all changes are complete
    Marks the part as "saved" and updates timestamp
    
    Example request:
    {
        "part_id": 143,
        "saved_by": "john.doe@company.com"
    }
    """
    try:
        save_info = save_part_data(request.part_id, request.saved_by)
        
        # Get complete saved data
        part = get_part_cost_by_id(request.part_id)
        operations = get_part_operations_by_part_id(request.part_id)
        summary = get_part_cost_summary(request.part_id)
        
        return {
            "success": True,
            "message": "Part saved successfully",
            "save_info": save_info,
            "data": {
                "part": part,
                "operations": operations,
                "summary": summary
            }
        }
    except ValueError as e:
        raise HTTPException(404, str(e))
    except Exception as e:
        raise HTTPException(500, f"Save failed: {str(e)}")


@router.get("/saved-parts")
def get_saved_parts():
    """
    Get list of all saved parts
    Returns parts that have been explicitly saved by users
    """
    try:
        parts = get_all_saved_parts()
        return {
            "success": True,
            "total_saved_parts": len(parts),
            "parts": parts
        }
    except Exception as e:
        raise HTTPException(500, f"Failed to get saved parts: {str(e)}")


@router.get("/unsaved-parts")
def get_unsaved_parts_list():
    """
    Get list of parts with unsaved changes
    """
    try:
        parts = get_unsaved_parts()
        return {
            "success": True,
            "total_unsaved_parts": len(parts),
            "parts": parts
        }
    except Exception as e:
        raise HTTPException(500, f"Failed to get unsaved parts: {str(e)}")


@router.get("/view-saved/{part_id}")
def view_saved_part_data(part_id: int):
    """
    View complete saved data for a specific part
    User can click on a part from the saved list to view all details
    """
    try:
        # Get part data
        part = get_part_cost_by_id(part_id)
        if not part:
            raise HTTPException(404, f"Part {part_id} not found")
        
        # Get all related data
        operations = get_part_operations_by_part_id(part_id)
        field_status = get_all_field_statuses_for_part(part_id)
        summary = get_part_cost_summary(part_id)

        stp_path = get_stp_file_path(part_id,)  
        
        return {
            "success": True,
            "part_id": part_id,
            "part_number": part.get('part_number'),
            "is_saved": part.get('is_saved', False),
            "saved_at": part.get('last_saved_at'),
            "saved_by": part.get('last_saved_by'),
            "step_file_path": stp_path,
            "data": {
                "part": part,
                "operations": operations,
                "field_status": field_status,
                "summary": summary
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Failed to retrieve part: {str(e)}")


@router.get("/part-status/{part_id}")
def get_part_save_status(part_id: int):
    """
    Check if a part has been saved or has pending changes
    Use this to show "Unsaved changes" indicator in UI
    """
    try:
        part = get_part_cost_by_id(part_id)
        if not part:
            raise HTTPException(404, f"Part {part_id} not found")
        
        return {
            "success": True,
            "part_id": part_id,
            "part_number": part.get('part_number'),
            "is_saved": part.get('is_saved', False),
            "last_saved_at": part.get('last_saved_at'),
            "last_saved_by": part.get('last_saved_by'),
            "has_unsaved_changes": not part.get('is_saved', True)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Failed to get status: {str(e)}")
    
@router.get("/saved-parts/dropdown")
def get_saved_parts_for_dropdown():
    """
    Get simplified list of saved parts for dropdown menu
    Returns only part_number and id - optimized for UI dropdowns
    
    Example response:
    {
        "success": true,
        "total": 25,
        "parts": [
            {"id": 143, "part_number": "ABC-001", "description": "Front Panel", "last_saved_at": "2025-01-20T10:30:00"},
            {"id": 142, "part_number": "ABC-002", "description": "Back Panel", "last_saved_at": "2025-01-20T09:15:00"}
        ]
    }
    """
    try:
        parts = get_saved_parts_dropdown()
        return {
            "success": True,
            "total": len(parts),
            "parts": parts
        }
    except Exception as e:
        raise HTTPException(500, f"Failed to get saved parts: {str(e)}")
    
