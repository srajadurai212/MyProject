
import os, tempfile, shutil
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from app.services.processcad_new import extract_dimensions
from app.services.postgresq import insert_part_dimensions, insert_stp_file_path


from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import StreamingResponse
import os, io, shutil, tempfile
 
from OCC.Core.STEPControl import STEPControl_Reader
from OCC.Core.IFSelect import IFSelect_RetDone
from OCC.Core.StlAPI import StlAPI_Writer
from OCC.Core.BRepMesh import BRepMesh_IncrementalMesh
from app.services.postgresq import get_stp_file_path
from fastapi.responses import FileResponse
from pathlib import Path


# Define upload root (adjust BASE_DIR to your project root)
BASE_DIR = Path(__file__).parent.parent.parent  # Assuming app/api/cad.py structure
UPLOAD_ROOT = BASE_DIR / "uploads"
UPLOAD_ROOT.mkdir(parents=True, exist_ok=True)

router = APIRouter()

def sanitize_form_value(value, field_type: str, default=None):
    """Bulletproof sanitization: 'string'/None → proper defaults"""
    if value is None or value == "string" or value == "":
        return default
    try:
        if field_type == "float":
            return float(value) if value else default
        elif field_type == "int":
            return int(value) if value else default
        return str(value)
    except (ValueError, TypeError):
        return default
    
def mandatory_manual_value(value,column_name,field_type):
    val = ["part_number","epu_nos","material_spec"]
    if column_name in val:
        print(column_name,value,"manual")
        if field_type == "float" and not (value == 0.0 or value is None or value == ""):
            return float(value)  
        elif field_type == "str" and not (value == "" or value is None or value == "string"):
            return str(value)
        else: 
            raise HTTPException(500, f"Mandatory field {column_name} is missing")

@router.post("/extract")
def extract_step(
    # REQUIRED first
    file: UploadFile = File(...),
    part_number: str = Form(...),
    
    # SANITIZED optional params
    epu_nos: Optional[float] = Form(None),
    no_of_batch_per_year: Optional[float] = Form(None),
    material_type: Optional[str] = Form(None),
    material_category: Optional[str] = Form(None),
    material_spec: Optional[str] = Form(None),
    surface_finish: Optional[str] = Form(None),
    standard_sheet_length_mm: float = Form(2438.0),
    standard_sheet_width_mm: float = Form(1219.0),
    web_allowance_length_mm: Optional[str] = Form(None),
    web_allowance_width_mm: Optional[str] = Form(None),
    draw_bead_allowance_length_mm: Optional[str] = Form(None),
    draw_bead_allowance_width_mm: Optional[str] = Form(None),
    quantity_per_assembly: Optional[int] = Form(None),
    assy_level: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    part_cat: Optional[str] = Form(None),
    part_or_assy: Optional[str] = Form(None),
    zgs: Optional[str] = Form(None),
):
    if not file.filename.lower().endswith((".stp", ".step")):
        raise HTTPException(400, "Only STEP/STP files allowed")

    # SANITIZE ALL "string" VALUES BEFORE DB
    sanitized = {
        'part_number': mandatory_manual_value(part_number, 'part_number', 'str'),
        'epu_nos': mandatory_manual_value(epu_nos,'epu_nos', 'float'),
        'no_of_batch_per_year': sanitize_form_value(no_of_batch_per_year, 'float', 12.0),
        'material_type': sanitize_form_value(material_type, 'str', 'Sheet Metal'),
        'material_category': sanitize_form_value(material_category, 'str', 'Steel'),
        'material_spec': mandatory_manual_value(material_spec, "material_spec", 'str'),
        'surface_finish': sanitize_form_value(surface_finish, 'str', None),
        'standard_sheet_length_mm': float(standard_sheet_length_mm),
        'standard_sheet_width_mm': float(standard_sheet_width_mm),
        'web_allowance_length_mm': sanitize_form_value(web_allowance_length_mm, 'float', 2.0),
        'web_allowance_width_mm': sanitize_form_value(web_allowance_width_mm, 'float', 1.0),
        'draw_bead_allowance_length_mm': sanitize_form_value(draw_bead_allowance_length_mm, 'str', None),
        'draw_bead_allowance_width_mm': sanitize_form_value(draw_bead_allowance_width_mm, 'str', None),
        'quantity_per_assembly': sanitize_form_value(quantity_per_assembly, 'int', None),
        'assy_level': sanitize_form_value(assy_level, 'str', None),
        'description': sanitize_form_value(description, 'str', None),
        'part_cat': sanitize_form_value(part_cat, 'str', None),
        'part_or_assy': sanitize_form_value(part_or_assy, 'str', None),
        'zgs': sanitize_form_value(zgs, 'str', None),
    }

    # Create safe filename with part_number prefix
    safe_filename = f"{part_number}_{file.filename}"
    step_file_path = UPLOAD_ROOT / safe_filename

    try:
        # SAVE FILE ONCE to permanent location
        with open(step_file_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
        
        print(f"FILE SAVED: {step_file_path.absolute()}")

        # EXTRACT DIMENSIONS from the saved file (not from consumed stream)
        dimensions = extract_dimensions(str(step_file_path))
        if not dimensions:
            raise HTTPException(422, "STEP extraction failed - invalid geometry")

        print(f"SANITIZED INPUT: {sanitized}")

        # INSERT PART DIMENSIONS
        part_id = insert_part_dimensions(
            dimensions=dimensions,
            part_number=part_number,
            material_type=sanitized['material_type'],
            material_category=sanitized['material_category'],
            material_spec=sanitized['material_spec'],
            surface_finish=sanitized['surface_finish'],
            epu_nos=sanitized['epu_nos'],
            no_of_batch_per_year=sanitized['no_of_batch_per_year'],
            standard_sheet_length_mm=sanitized['standard_sheet_length_mm'],
            standard_sheet_width_mm=sanitized['standard_sheet_width_mm'],
            web_allowance_length_mm=sanitized['web_allowance_length_mm'],
            web_allowance_width_mm=sanitized['web_allowance_width_mm'],
            draw_bead_allowance_length_mm=sanitized['draw_bead_allowance_length_mm'],
            draw_bead_allowance_width_mm=sanitized['draw_bead_allowance_width_mm'],
            quantity_per_assembly=sanitized['quantity_per_assembly'],
            assy_level=sanitized['assy_level'],
            description=sanitized['description'],
            part_cat=sanitized['part_cat'],
            part_or_assy=sanitized['part_or_assy'],
            zgs=sanitized['zgs']
        )

        # STORE STEP FILE PATH in database
        insert_stp_file_path(part_id, str(step_file_path.absolute()))

        return {
            "success": True,
            "part_cost_id": part_id,
            "step_file_path": str(step_file_path.absolute()), 
            "dimensions": dimensions,
        }
        
    except HTTPException:
        # If processing failed, clean up the saved file
        if step_file_path.exists():
            step_file_path.unlink()
        raise
        
    except Exception as e:
        # Clean up on any error
        if step_file_path.exists():
            step_file_path.unlink()
        print(f"ERROR: {str(e)}")
        raise HTTPException(500, f"Processing failed: {str(e)}")
        
    finally:
        file.file.close()

@router.post("/convert-to-stl")
def convert_to_stl(
    file: UploadFile = File(...),
    part_number: str = Form("part"),
    format: str = Form("binary")
):
    # --- VALIDATE FILE ---
    if not file.filename.lower().endswith((".stp", ".step")):
        raise HTTPException(status_code=400, detail="Only STEP/STP files allowed")
 
    tmp_dir = tempfile.mkdtemp()
    step_path = os.path.join(tmp_dir, file.filename)
 
    try:
        # --- SAVE STEP FILE ---
        with open(step_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
 
        print(f"Loading STEP: {file.filename}")
 
        # --- LOAD STEP USING OPENCASCADE ---
        reader = STEPControl_Reader()
        status = reader.ReadFile(step_path)
 
        if status != IFSelect_RetDone:
            raise HTTPException(status_code=422, detail="STEP read failed")
 
        reader.TransferRoots()
        shape = reader.OneShape()
 
        if shape.IsNull():
            raise HTTPException(status_code=422, detail="STEP contains no solid geometry")
 
        # --- TESSELLATE SHAPE ---
        # Smaller value = finer mesh
        BRepMesh_IncrementalMesh(shape, 0.1).Perform()
 
        # --- EXPORT STL ---
        stl_path = os.path.join(tmp_dir, f"{part_number}.stl")
        writer = StlAPI_Writer()
        writer.SetASCIIMode(format != "binary")
        writer.Write(shape, stl_path)
 
        # --- VALIDATE STL ---
        if not os.path.exists(stl_path):
            raise HTTPException(status_code=422, detail="STL export failed")
 
        if os.path.getsize(stl_path) < 500:
            raise HTTPException(status_code=422, detail="Generated STL is empty")
 
        with open(stl_path, "rb") as f:
            stl_data = f.read()
 
        print(f"✓ STL generated ({len(stl_data)} bytes)")
 
        return StreamingResponse(
            io.BytesIO(stl_data),
            media_type="application/octet-stream",
            headers={
                "Content-Disposition": f"attachment; filename={part_number}.stl",
                "Content-Length": str(len(stl_data))
            }
        )
 
    except HTTPException:
        raise
    except Exception as e:
        print(f"FATAL ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail="STEP to STL conversion failed")
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)

@router.get("/view-step/{part_id}")
def view_step_file(part_id: int):
    """
    Stream the STEP file for inline viewing (not download)
    Use this endpoint to load the file directly in a 3D viewer
    """
    
    # Get the file path from database
    result = get_stp_file_path(part_id)
    
    if not result or 'step_file_path' not in result:
        raise HTTPException(404, f"STEP file not found for part_id {part_id}")
    
    step_file_path = Path(result['step_file_path'])
    
    # Check if file exists
    if not step_file_path.exists():
        raise HTTPException(
            404, 
            f"STEP file not found on disk: {step_file_path}"
        )
    
    # Return the file for inline viewing (not forcing download)
    return FileResponse(
        path=str(step_file_path),
        media_type="application/step",
        filename=step_file_path.name,
        headers={
            "Content-Disposition": f"inline; filename={step_file_path.name}"
        }
    )

