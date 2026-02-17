from pydantic import BaseModel
from datetime import date
from typing import List, Optional, Any

from pydantic import BaseModel, EmailStr, constr

class LoginSchema(BaseModel):
    email: EmailStr
    password: str

class RegisterSchema(BaseModel):
    email: EmailStr
    password: constr(min_length=6)


class PredictionResponse(BaseModel):
    date: date
    predicted_price: float

class HistoricalResponse(BaseModel):
    date: date
    flat_steel_price: float

class TestDataResponse(BaseModel):
    date: date
    actual_price: float
    predicted_price: float
    mape: float
    accuracy: float


#benchmarking schemas

# class ObjectClassResponse(BaseModel):
#     same_class: int
#     details: Optional[str] = None
#     reference_image: Optional[str] = None
#     test_image: Optional[str] = None


# class CompareResponse(BaseModel):
#     vlm: str
#     ref_warnings: List[str]
#     test_warnings: List[str]
#     ref_image: bytes
#     test_image: bytes
#     ref_segmented: bytes
#     test_segmented: bytes
    
# class PdfRequest(BaseModel):
#     markdown_text: str
#     ref_image: str | None = None  # base64
#     test_image: str | None = None  # base64


#Digital Costing Schemas

class CADResponse(BaseModel):
    Length_mm: float
    Width_mm: float
    Height_mm: float
    Thickness_mm: float

    Blank_Length_mm: float
    Blank_Width_mm: float

    Volume_mm3: float
    Surface_Area_mm2: float

class UpdatePartCostFieldRequest(BaseModel):
    part_cost_id: int
    field_name: str
    value: Any

class UpdateMachineSpecRequest(BaseModel):
    operation_id: int
    machine_spec: str


class UpdateLabourTypeRequest(BaseModel):
    operation_id: int
    labour_type: str

class InsertPartRequest(BaseModel):

    material_spec: Optional[str] = None
    material_type: Optional[str] = None
    material_category: Optional[str] = None
    surface_finish: Optional[str] = None

    epu_nos: Optional[float] = None
    no_of_batch_per_year: Optional[float] = None

    standard_sheet_length_mm: float = 2438.0
    standard_sheet_width_mm: float = 1219.0

    web_allowance_length_mm: float = 2
    web_allowance_width_mm: float = 1

    draw_bead_allowance_length_mm: Optional[str] = None
    draw_bead_allowance_width_mm: Optional[str] = None