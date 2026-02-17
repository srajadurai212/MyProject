from sqlalchemy import Column, Integer, String
from app.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)


#supplier poc
from pydantic import BaseModel
from typing import List, Optional

from typing import Optional
from pydantic import BaseModel

class FunctionalRequirements(BaseModel):
    yield_strength_mpa: Optional[float] = None
    corrosion_resistance: Optional[str] = None

class PartInput(BaseModel):
    part_name: str
    industry: str
    manufacturing_process: str
    known_material: Optional[str] = ""
    material_hint: Optional[str] = ""
    functional_requirements: Optional[FunctionalRequirements] = None
    region_preference: Optional[List[str]] = []
