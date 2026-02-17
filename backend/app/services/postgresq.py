import math
from typing import Optional
from sqlalchemy import create_engine, text
import logging
import os
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging. DEBUG)

DB_URL = os.getenv("COSTING_DB_URL")

# DB_URL = "postgresql://postgres:Intelizign%40123@localhost:5432/Digital_Cost"


engine = create_engine(DB_URL)

# ============================================================
# SYSTEM READONLY FIELDS - CANNOT BE EDITED
# ============================================================
SYSTEM_READONLY_FIELDS = {
    # Primary keys / Foreign keys - Never edit
    "id",
    "part_cost_id",
    
    # Calculated costs - Always system calculated
    "net_rm_cost",
    "total_process_cost_jpy",
    "total_rm_process_cost_jpy",
    "total_cost",
    "total_part_cost_jpy",
}

# ============================================================
# USER EDITABLE FIELDS - CAN BE EDITED (part_cost table)
# ============================================================
USER_EDITABLE_FIELDS = {
    # Identity
    "si",
    "assy_level",
    "part_number",
    "description",
    "image",
    "zgs",
    
    # Production
    "epu_nos",
    "no_of_batch_per_year",
    "batch_qty",
    "part_cat",
    "part_assy",
    
    # Material
    "material_type",
    "material_category",
    "material_spec",
    "surface_finish",
    
    # Dimensions (from STEP - but editable)
    "part_length_mm",
    "part_width_mm",
    "part_height_mm",
    "part_thick_mm",
    "volume_cu_m",
    "weight_kg",
    "surface_area_sq_m",
    "complexity",
    
    # Blank
    "blank_length_mm",
    "blank_width_mm",
    
    # Sheet & Strip
    "standard_sheet_length_mm",
    "standard_sheet_width_mm",
    "web_allowance_length_mm",
    "web_allowance_width_mm",
    "draw_bead_allowance_length_mm",
    "draw_bead_allowance_width_mm",
    "strip_size_width_mm",
    "strip_size_pitch_mm",
    "no_of_part_per_blank",
    
    # Weight & Costs
    "blank_wt",
    "rm_cost_per_kg",
    "rm_cost_per_part",
    "scrap_wt",
    "scrap_cost_per_kg",
    "scrap_cost_per_part",
    
    # Perimeter & Tonnage
    "outer_perimeter_mm",
    "approx_blank_ton",
    
    # Cost factors
    "rejection",
    "material_oh_cost",
    "die_maint",
    "mpo",
    "sga",
    "profit_on_material",
    "profit_on_process",
    "rate_per_kg",
    
    # Other
    "tool_cost",
    "remarks",
    "quantity_per_assembly",
}

# ============================================================
# PART_OPERATIONS TABLE - EDITABLE FIELDS
# ============================================================
OPERATION_EDITABLE_FIELDS = {
    "part_number",
    "op_stage",
    "op_name",
    "machine_spec",
    "machine_spec_source",
    "no_of_strokes",
    "labour_type",
    "labour_type_source",
    "no_of_labour",
    "setup_time_min",
    "cycle_time_min",
    "mhr",
    "process_cost",
    "is_active",
}

OPERATION_READONLY_FIELDS = {
    "id",
    "part_cost_id",
    "created_at",
}

OVERRIDABLE_CALCULATED_FIELDS = {
    "blank_wt",
    "weight_kg",
    "rm_cost_per_part",
    "rm_cost_per_kg",
    "scrap_wt",
    "scrap_cost_per_part",
    "scrap_cost_per_kg",
    "strip_size_width_mm",
    "strip_size_pitch_mm",
    "no_of_part_per_blank",
    "outer_perimeter_mm",
    "approx_blank_ton",
    "rejection",
    "material_oh_cost",
    "die_maint",
    "mpo",
    "sga",
    "profit_on_material",
    "profit_on_process",
    "rate_per_kg",    
    # Operation fields
    "no_of_strokes",
    "machine_spec",
    "labour_type",
    "no_of_labour",
    "setup_time_min",
    "cycle_time_min",
    "mhr",
    "process_cost",
}

# ============================================================
# DROPDOWN FUNCTIONS
# ============================================================

def get_web_allowance_options():
    """Returns all values from web_allowance table as a list"""
    query = text("SELECT value FROM web_allowance ORDER BY value")
    with engine.connect() as conn:
        result = conn.execute(query)
        options = [row[0] for row in result.fetchall()]
    return options


def get_material_spec_options():
    """Dropdown values for material_spec"""
    query = text("""
        SELECT material_grade
        FROM raw_material_cost
        ORDER BY material_grade
    """)
    with engine.connect() as conn:
        return [row[0] for row in conn.execute(query).fetchall()]


def get_labour_types():
    """Dropdown values for labour_type"""
    sql = text("""
        SELECT labor_code
        FROM labor_types
        ORDER BY labor_code
    """)
    with engine.connect() as conn:
        return [row[0] for row in conn.execute(sql).fetchall()]


def get_active_machines():
    """
    Dropdown values for machine_spec. 
    Returns all active machine names. 
    """
    query = text("""
        SELECT operation_code
        FROM machines
        WHERE is_active = TRUE
        ORDER BY id
    """)
    with engine.connect() as conn:
        rows = conn.execute(query).fetchall()
    return [row[0] for row in rows]


def get_press_machines():
    """
    Returns only Press type machines (for automatic assignment).
    Sorted by tonnage.
    """
    query = text("""
        SELECT machine_name, tonnage
        FROM machines
        WHERE is_active = TRUE
          AND machine_type = 'Press'
          AND tonnage IS NOT NULL
        ORDER BY tonnage ASC
    """)
    with engine.connect() as conn:
        rows = conn.execute(query).fetchall()
    return [{"machine_name": row[0], "tonnage": row[1]} for row in rows]


def get_surface_finishes():
    """Dropdown values for surface_finish"""
    query = text("""
        SELECT finish_code
        FROM surface_finishes
        ORDER BY id
    """)
    with engine.connect() as conn:
        result = conn.execute(query)
        return [row[0] for row in result.fetchall()]
    
def get_material_types():
    """Dropdown values for material_types"""
    query = text("""
        SELECT type_name
        FROM material_types
        ORDER BY id
    """)
    with engine.connect() as conn:
        result = conn.execute(query)
        return [row[0] for row in result.fetchall()]

def get_material_category_options():
    """
    Dropdown values for material_category (system + user-defined)
    """
    query = text("""
        SELECT category_name FROM material_categories
        UNION ALL
        SELECT category_name FROM user_material_categories WHERE is_active = TRUE
        ORDER BY category_name
    """)
    with engine.connect() as conn:
        return [row[0] for row in conn.execute(query).fetchall()]

def get_bead_type_options():
    """Returns all bead types as a list of bead_name"""
    query = text("SELECT bead_name FROM bead_types ORDER BY id")
    with engine.connect() as conn:
        result = conn.execute(query)
        options = [row[0] for row in result.fetchall()]
    return options


def get_op_stage_options():
    """
    Dropdown values for OP Stage
    Returns:  ['OP1', 'OP2', ...  'OP10', 'CF']
    """
    sql = text("""
        SELECT stage_code
        FROM opn_stages
        ORDER BY id
    """)
    with engine.connect() as conn:
        return [row[0] for row in conn.execute(sql).fetchall()]

# ============================================================
# USER MATERIAL CATEGORY FUNCTIONS
# ============================================================

def insert_stp_file_path(part_id: int, step_file_path: str):
    with engine.connect() as conn:
        conn.execute(
            text("INSERT INTO stp_file (part_id, step_file_path) VALUES (:part_id, :path)"),
            {"part_id": part_id, "path": step_file_path}
        )
        conn.commit()

def get_stp_file_path(part_id: int) -> Optional[dict]:
    """Get STEP file path for part_id"""
    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT step_file_path FROM stp_file WHERE part_id = :part_id"),
            {"part_id": part_id}
        ).fetchone()
        if result:
            return {"step_file_path": result[0]}
        return None

def add_user_material_category(category_name: str, density: float):
    """
    Add a new user-defined material category with custom density
    If a soft-deleted category exists, reactivate it instead
    """
    if not category_name or not density or density <= 0:
        raise ValueError("Category name and positive density are required")
    
    # Check if already exists (active or inactive)
    check_sql = text("""
        SELECT id, is_active, density 
        FROM user_material_categories 
        WHERE LOWER(category_name) = LOWER(:category_name)
    """)
    
    with engine.connect() as conn:
        existing = conn.execute(check_sql, {"category_name": category_name}).fetchone()
        
        if existing:
            existing_id = existing[0]
            is_active = existing[1]
            existing_density = existing[2]
            
            # If it's soft-deleted, reactivate it
            if not is_active:
                reactivate_sql = text("""
                    UPDATE user_material_categories
                    SET is_active = TRUE,
                        density = :density
                    WHERE id = :id
                    RETURNING id
                """)
                
                with engine.begin() as conn_update:
                    result = conn_update.execute(reactivate_sql, {
                        "density": float(density),
                        "id": existing_id
                    })
                    reactivated_id = result.fetchone()[0]
                
                print(f"Reactivated user material category: {category_name} (density updated to: {density})")
                return reactivated_id
            else:
                # It's already active
                raise ValueError(f"Material category '{category_name}' already exists and is active")
    
    # If it doesn't exist at all, create new
    insert_sql = text("""
        INSERT INTO user_material_categories (category_name, density, is_active)
        VALUES (:category_name, :density, TRUE)
        RETURNING id
    """)
    
    with engine.begin() as conn:
        result = conn.execute(insert_sql, {
            "category_name": category_name,
            "density": float(density)
        })
        category_id = result.fetchone()[0]
    
    print(f"Added user material category: {category_name} (density: {density})")
    return category_id


def get_all_material_categories():
    """
    Get all material categories (system + user-defined)
    Returns list of dicts with category_name and density
    """
    query = text("""
        SELECT category_name, density, 'system' as source
        FROM material_categories
        WHERE TRUE
        UNION ALL
        SELECT category_name, density, 'user' as source
        FROM user_material_categories
        WHERE is_active = TRUE
        ORDER BY category_name
    """)
    
    with engine.connect() as conn:
        rows = conn.execute(query).mappings().fetchall()
        return [dict(row) for row in rows]


def delete_user_material_category(category_name: str):
    """
    Soft delete a user-defined material category
    """
    sql = text("""
        UPDATE user_material_categories
        SET is_active = FALSE
        WHERE category_name = :category_name
    """)
    
    with engine.begin() as conn:
        result = conn.execute(sql, {"category_name": category_name})
        if result.rowcount == 0:
            raise ValueError(f"User category '{category_name}' not found")
    
    print(f"Deleted user material category: {category_name}")


def update_user_material_category(category_name: str, new_density: float):
    """
    Update density for a user-defined material category
    """
    if new_density <= 0:
        raise ValueError("Density must be positive")
    
    sql = text("""
        UPDATE user_material_categories
        SET density = :density
        WHERE category_name = :category_name AND is_active = TRUE
    """)
    
    with engine.begin() as conn:
        result = conn.execute(sql, {
            "category_name": category_name,
            "density": float(new_density)
        })
        if result.rowcount == 0:
            raise ValueError(f"User category '{category_name}' not found")
    
    print(f"Updated density for {category_name}: {new_density}")

# ============================================================
# LOOKUP FUNCTIONS
# ============================================================

def get_density_by_material_category(material_category: str) -> float:
    """
    Fetch density from material_categories table (system or user-defined)
    """
    if not material_category:
        material_category = "Steel"

    # First check system categories
    query = text("""
        SELECT density
        FROM material_categories
        WHERE category_name = :category
        UNION ALL
        SELECT density
        FROM user_material_categories
        WHERE category_name = :category AND is_active = TRUE
        LIMIT 1
    """)

    with engine.connect() as conn:
        row = conn.execute(query, {"category": material_category}).fetchone()
        return float(row[0]) if row and row[0] is not None else 0.0

def get_material_density(material_category: str) -> float:
    """Alias for get_density_by_material_category"""
    return get_density_by_material_category(material_category)

def get_rm_cost_per_kg(material_spec: str) -> float:
    """Fetch RM cost per kg from raw_material_cost table"""
    material_spec = resolve_material_spec(material_spec)

    query = text("""
        SELECT cost_per_kg
        FROM raw_material_cost
        WHERE material_grade = :material_spec
    """)

    with engine.connect() as conn:
        row = conn.execute(query, {"material_spec": material_spec}).fetchone()
        return float(row[0]) if row and row[0] is not None else 0.0


def get_scrap_cost_per_kg(material_category: str) -> float:
    """Fetch scrap cost per kg from scrap_costs table"""
    if not material_category:
        material_category = "Steel"

    query = text("""
        SELECT cost_per_kg
        FROM scrap_costs
        WHERE material_category = :category
    """)

    with engine.connect() as conn:
        row = conn.execute(query, {"category": material_category}).fetchone()
        return float(row[0]) if row and row[0] is not None else 0.0


def get_bead_allowance_mm(bead_type: str) -> float:
    """Fetch allowance_mm from bead_allowance table"""
    if not bead_type:
        return 0.0

    query = text("""
        SELECT allowance_mm
        FROM bead_allowance
        WHERE bead_type = :bead_type
    """)

    with engine.connect() as conn:
        result = conn.execute(query, {"bead_type": bead_type}).fetchone()
        return float(result[0]) if result else 0.0


def get_machine_by_tonnage(approx_blank_ton: float) -> dict:
    """
    Get the closest machine with tonnage >= approx_blank_ton. 
    Only considers Press type machines.
    """
    if not approx_blank_ton or approx_blank_ton <= 0:
        return None

    query = text("""
        SELECT machine_name, tonnage, hour_rate, setup_time_min, skilled_labours
        FROM machines
        WHERE is_active = TRUE
          AND tonnage IS NOT NULL
          AND tonnage >= :approx_blank_ton
          AND machine_type = 'Press'
        ORDER BY tonnage ASC
        LIMIT 1
    """)

    with engine.connect() as conn:
        row = conn.execute(query, {"approx_blank_ton": approx_blank_ton}).fetchone()
        if row:
            return {
                "machine_name": row[0],
                "tonnage": row[1],
                "hour_rate": row[2],
                "setup_time_min": row[3],
                "skilled_labours": row[4]
            }
    return None

# ============================================================
# RESOLVE FUNCTIONS (Default Values)
# ============================================================

def resolve_material_spec(material_spec: str) -> str:
    """Default:  HTP540"""
    return material_spec if material_spec else None


def resolve_material_type(material_type: str) -> str:
    """Default: Sheet Metal"""
    return material_type if material_type else "Sheet Metal"


def resolve_material_category(material_category: str) -> str:
    """Default: Steel"""
    return material_category if material_category else "Steel"


def resolve_epu_nos(epu_nos: float) -> float:
    """Default: 14738.0"""
    return float(epu_nos) if epu_nos and epu_nos > 0 else None


def resolve_no_of_batch_per_year(no_of_batch_per_year: float) -> float:
    """Default: 12.0"""
    return float(no_of_batch_per_year) if no_of_batch_per_year and no_of_batch_per_year > 0 else 12.0


# ============================================================
# CALCULATION FUNCTIONS
# ============================================================

def calculate_weight_kg(volume_mm3: float, material_category: str) -> float:
    """weight = volume × density"""
    density = get_density_by_material_category(material_category)
    if volume_mm3 <= 0 or density <= 0:
        return 0.0
    weight_kg = volume_mm3 * density
    return round(weight_kg, 3)


def calculate_batch_qty(epu_nos: float, no_of_batch_per_year:  float) -> float:
    """batch_qty = epu_nos / no_of_batch_per_year"""
    if epu_nos > 0 and no_of_batch_per_year > 0:
        return round(epu_nos / no_of_batch_per_year, 2)
    return 0.0


def calculate_scrap_weight(rm_cost_per_part: float, blank_wt: float, weight_kg: float) -> float:
    """scrap_wt = blank_wt - weight_kg"""
    if rm_cost_per_part > 0 and blank_wt > 0 and weight_kg >= 0:
        scrap = blank_wt - weight_kg
        return round(max(scrap, 0.0), 3)
    return 0.0


def calculate_scrap_cost_per_part(scrap_wt: float, scrap_cost_per_kg:  float) -> float:
    """scrap_cost_per_part = scrap_wt × scrap_cost_per_kg"""
    if scrap_wt > 0 and scrap_cost_per_kg > 0:
        return round(scrap_wt * scrap_cost_per_kg, 2)
    return 0.0


def calculate_net_rm_cost(rm_cost_per_part: float, scrap_cost_per_part:  float) -> float:
    """net_rm_cost = rm_cost_per_part - scrap_cost_per_part"""
    if rm_cost_per_part > 0:
        net_cost = rm_cost_per_part - (scrap_cost_per_part or 0.0)
        return round(max(net_cost, 0.0), 2)
    return 0.0


def calculate_strip_size_width(
    blank_length_mm: float,
    web_allowance_length_mm:  float,
    part_thick_mm: float,
    draw_bead_allowance_length_mm: str
) -> float:
    """strip_size_width = blank_length + web_term + bead_allowance"""
    factor = 1.5 if part_thick_mm < 3 else 1.0
    web_term = web_allowance_length_mm * part_thick_mm * factor
    bead_allowance = get_bead_allowance_mm(draw_bead_allowance_length_mm)
    strip_size_width_mm = blank_length_mm + web_term + bead_allowance
    return round(strip_size_width_mm, 3)


def calculate_strip_size_pitch(
    blank_width_mm: float,
    web_allowance_width_mm:  float,
    part_thick_mm: float,
    draw_bead_allowance_width_mm: str
) -> float:
    """strip_size_pitch = blank_width + web_term + bead_allowance"""
    factor = 1.5 if part_thick_mm < 3 else 1.0
    web_term = web_allowance_width_mm * part_thick_mm * factor
    bead_allowance = get_bead_allowance_mm(draw_bead_allowance_width_mm)
    strip_size_pitch_mm = blank_width_mm + web_term + bead_allowance
    return round(strip_size_pitch_mm, 3)


def calculate_no_of_part_per_blank(
    standard_sheet_length_mm: float,
    standard_sheet_width_mm: float,
    strip_size_width_mm: float,
    strip_size_pitch_mm: float
) -> int:
    """Optimize parts per sheet"""
    if (standard_sheet_width_mm <= 0 or strip_size_width_mm <= 0 or strip_size_pitch_mm <= 0):
        return 1

    option1 = (
        int(standard_sheet_length_mm / strip_size_width_mm) *
        int(standard_sheet_width_mm / strip_size_pitch_mm)
    )
    option2 = (
        int(standard_sheet_length_mm / strip_size_pitch_mm) *
        int(standard_sheet_width_mm / strip_size_width_mm)
    )
    return max(option1, option2, 1)


def calculate_blank_weight(
    material_type: str,
    material_category: str,
    part_width_mm: float,
    part_height_mm: float,
    part_thick_mm: float,
    part_length_mm: float,
    standard_sheet_length_mm: float,
    standard_sheet_width_mm: float,
    no_of_part_per_blank: float = 1.0
) -> float:
    """Calculate blank weight based on material type"""
    material_type = material_type or "Sheet Metal"
    material_category = material_category or "Steel"
    no_of_part_per_blank = float(no_of_part_per_blank or 1.0)

    density = float(get_material_density(material_category))

    part_width_mm = float(part_width_mm or 0)
    part_height_mm = float(part_height_mm or 0)
    part_thick_mm = float(part_thick_mm or 0)
    part_length_mm = float(part_length_mm or 0)
    standard_sheet_length_mm = float(standard_sheet_length_mm or 0)
    standard_sheet_width_mm = float(standard_sheet_width_mm or 0)

    if material_type == "Round Tube":
        volume = math.pi * (part_width_mm / 2) ** 2 * part_thick_mm * part_length_mm
    elif material_type == "Square Tube":
        volume = (part_width_mm ** 2 - (part_width_mm - 2 * part_thick_mm) ** 2) * part_length_mm
    elif material_type == "Rectangular Tube": 
        volume = (
            (part_width_mm * part_height_mm * part_length_mm)
            - ((part_width_mm - 2 * part_thick_mm) * (part_height_mm - 2 * part_thick_mm) * part_length_mm)
        )
    elif material_type == "Sheet Metal":
        volume = standard_sheet_length_mm * standard_sheet_width_mm * part_thick_mm
    else:
        return 0.0

    if no_of_part_per_blank <= 0:
        no_of_part_per_blank = 1.0

    blank_weight = (volume * density) / no_of_part_per_blank
    return round(blank_weight, 2)


def calculate_outer_perimeter_mm(material_type: str, blank_length_mm: float, blank_width_mm: float) -> float:
    """outer_perimeter = (length + width) × 2"""
    if material_type == "Sheet Metal" and blank_length_mm > 0 and blank_width_mm > 0:
        return round((blank_length_mm + blank_width_mm) * 2, 2)
    return 0.0


def calculate_approx_blank_ton(material_type: str, outer_perimeter_mm: float, part_thick_mm: float) -> float:
    """approx_blank_ton = (perimeter × thickness × 45 / 1000) × 1.25"""
    if material_type == "Sheet Metal" and outer_perimeter_mm > 0 and part_thick_mm > 0:
        approx_ton = (outer_perimeter_mm * part_thick_mm * 45 / 1000) * 1.25
        return round(approx_ton, 3)
    return 0.0


# ============================================================
# OPERATION UPDATE FUNCTIONS
# ============================================================

def assign_machine_to_operations(conn, part_cost_id: int):
    """
    Assign machine_spec to operations based on approx_blank_ton.
    ONLY updates operations where machine_spec_source = 'AUTO' or NULL.
    Preserves user's manual selections.
    """

    # 1. Get approx_blank_ton
    approx_sql = text("""
        SELECT approx_blank_ton
        FROM part_cost
        WHERE id = :part_cost_id
    """)

    approx_row = conn.execute(approx_sql, {"part_cost_id": part_cost_id}).fetchone()

    if not approx_row or approx_row[0] is None:
        print("No approx_blank_ton found, skipping machine assignment")
        return

    approx_blank_ton = float(approx_row[0])

    # 2. Select closest higher tonnage machine (Press type only)
    machine_sql = text("""
        SELECT machine_name
        FROM machines
        WHERE is_active = TRUE
          AND tonnage IS NOT NULL
          AND tonnage >= :approx_blank_ton
          AND machine_type = 'Press'
        ORDER BY tonnage ASC
        LIMIT 1
    """)

    machine_row = conn.execute(machine_sql, {"approx_blank_ton": approx_blank_ton}).fetchone()

    if not machine_row:
        print(f"No matching Press machine found for tonnage >= {approx_blank_ton}")
        return

    machine_name = machine_row[0]

    # 3. Update ONLY operations where machine_spec_source = 'AUTO' or NULL
    update_sql = text("""
        UPDATE part_operations
        SET 
            machine_spec = :machine_name,
            machine_spec_source = 'AUTO'
        WHERE part_cost_id = :part_cost_id
          AND is_active = TRUE
          AND (machine_spec_source = 'AUTO' OR machine_spec_source IS NULL)
    """)

    conn.execute(
        update_sql,
        {
            "machine_name": machine_name,
            "part_cost_id": part_cost_id
        }
    )

    print(f"Machine '{machine_name}' assigned (AUTO only) for approx_blank_ton={approx_blank_ton}")


def update_operation_labour_and_strokes(conn, part_cost_id: int):
    """
    Excel formulas:
    - no_of_strokes: =IF(AS18>1,1,"") → 1 if op_stage has any value
    - labour_type: =IF(AS18>1,"Skilled","") → 'Skilled' if op_stage has value (AUTO only)
    - no_of_labour: =VLOOKUP(machine_spec, Machines!B:I, 8, 0) → skilled_labours
    
    UPDATED: Now respects manual overrides for each operation
    """
    
    # Get all operations for this part
    ops_sql = text("""
        SELECT id FROM part_operations 
        WHERE part_cost_id = :part_cost_id AND is_active = TRUE
    """)
    operations = conn.execute(ops_sql, {"part_cost_id": part_cost_id}).fetchall()
    
    for op_row in operations:
        op_id = op_row[0]
        
        # Check which fields are manually overridden for THIS specific operation
        no_of_strokes_manual = is_field_manual(part_cost_id, f"op_{op_id}_no_of_strokes")
        no_of_labour_manual = is_field_manual(part_cost_id, f"op_{op_id}_no_of_labour")
        labour_type_manual = is_field_manual(part_cost_id, f"op_{op_id}_labour_type")
        
        # Build SET clause only for non-manual fields
        set_clauses = []
        
        if not no_of_strokes_manual:
            set_clauses.append("""
                no_of_strokes = CASE
                    WHEN op_stage IS NOT NULL AND op_stage <> ''
                    THEN 1
                    ELSE NULL
                END
            """)
        
        if not no_of_labour_manual:
            set_clauses.append("""
                no_of_labour = CASE
                    WHEN machine_spec IS NOT NULL
                    THEN (
                        SELECT m.skilled_labours
                        FROM machines m
                        WHERE m.machine_name = part_operations.machine_spec
                          AND m.is_active = TRUE
                        LIMIT 1
                    )
                    ELSE NULL
                END
            """)
        
        if not labour_type_manual:
            set_clauses.append("""
                labour_type = CASE
                    WHEN (labour_type_source = 'AUTO' OR labour_type_source IS NULL)
                         AND op_stage IS NOT NULL 
                         AND op_stage <> ''
                    THEN 'Skilled'
                    ELSE labour_type
                END
            """)
        
        # Only execute UPDATE if there's something to update
        if set_clauses:
            update_sql = text(f"""
                UPDATE part_operations
                SET {', '.join(set_clauses)}
                WHERE id = :operation_id
                  AND is_active = TRUE
            """)
            
            conn.execute(update_sql, {"operation_id": op_id})
            print(f"  Updated operation {op_id} (skipped manual fields)")
        else:
            print(f"  Skipped operation {op_id} (all fields are manual)")
    
    print(f"Updated no_of_strokes, no_of_labour, labour_type for part_cost_id={part_cost_id}")


def update_setup_time_min(conn, part_cost_id: int):
    """
    Excel: =IF(ISBLANK(AU18),"",VLOOKUP(AU18,Machines!$B:$H,4,0)/$J18)
    Column 4 from B = E = setup_time_min
    Divided by batch_qty
    
    UPDATED: Now respects manual overrides
    """
    ops_sql = text("""
        SELECT id FROM part_operations 
        WHERE part_cost_id = :part_cost_id AND is_active = TRUE
    """)
    operations = conn.execute(ops_sql, {"part_cost_id": part_cost_id}).fetchall()
    
    for op_row in operations:
        op_id = op_row[0]
        
        # Skip if manually overridden
        if is_field_manual(part_cost_id, f"op_{op_id}_setup_time_min"):
            print(f"  Skipped setup_time_min for operation {op_id} (MANUAL)")
            continue
        
        sql = text("""
            UPDATE part_operations po
            SET setup_time_min = CASE
                WHEN po.machine_spec IS NULL
                  OR pc.batch_qty IS NULL
                  OR pc.batch_qty = 0
                THEN NULL
                ELSE (
                    SELECT m.setup_time_min
                    FROM machines m
                    WHERE m.machine_name = po.machine_spec
                      AND m.is_active = TRUE
                    LIMIT 1
                ) / pc.batch_qty
            END
            FROM part_cost pc
            WHERE po.part_cost_id = pc.id
              AND po.id = :operation_id
              AND po.is_active = TRUE
        """)
        
        conn.execute(sql, {"operation_id": op_id})
    
    print(f"Updated setup_time_min for part_cost_id={part_cost_id}")


def update_cycle_time_min(conn, part_cost_id: int):
    """
    Excel: =IFERROR(1/VLOOKUP(AU18,Machines!$B:$F,5,0),"")
    Column 5 from B = F = strokes_per_min
    cycle_time_min = 1 / strokes_per_min
    
    UPDATED: Now respects manual overrides
    """
    ops_sql = text("""
        SELECT id FROM part_operations 
        WHERE part_cost_id = :part_cost_id AND is_active = TRUE
    """)
    operations = conn.execute(ops_sql, {"part_cost_id": part_cost_id}).fetchall()
    
    for op_row in operations:
        op_id = op_row[0]
        
        # Skip if manually overridden
        if is_field_manual(part_cost_id, f"op_{op_id}_cycle_time_min"):
            print(f"  Skipped cycle_time_min for operation {op_id} (MANUAL)")
            continue
        
        sql = text("""
            UPDATE part_operations po
            SET cycle_time_min = CASE
                WHEN po.machine_spec IS NOT NULL
                     AND m.strokes_per_min IS NOT NULL
                     AND m.strokes_per_min > 0
                THEN 1.0 / m.strokes_per_min
                ELSE NULL
            END
            FROM machines m
            WHERE m.machine_name = po.machine_spec
              AND m.is_active = TRUE
              AND po.id = :operation_id
              AND po.is_active = TRUE
        """)
        
        conn.execute(sql, {"operation_id": op_id})
    
    print(f"Updated cycle_time_min for part_cost_id={part_cost_id}")


def update_mhr(conn, part_cost_id: int):
    """
    Excel: =IFERROR(IF(ISBLANK(AU18),"",VLOOKUP(AU18,Machines!$B:$H,7,0))
                   +VLOOKUP(AW18,Machines!$M:$N,2,0)*AX18*1.05,0)
    
    Column 7 from B = H = hour_rate
    Labor lookup = hourly_rate from labor_types
    
    MHR = hour_rate + (hourly_rate × no_of_labour × 1.05)
    
    UPDATED: Now respects manual overrides
    """
    ops_sql = text("""
        SELECT id FROM part_operations 
        WHERE part_cost_id = :part_cost_id AND is_active = TRUE
    """)
    operations = conn.execute(ops_sql, {"part_cost_id": part_cost_id}).fetchall()
    
    for op_row in operations:
        op_id = op_row[0]
        
        # Skip if manually overridden
        if is_field_manual(part_cost_id, f"op_{op_id}_mhr"):
            print(f"  Skipped mhr for operation {op_id} (MANUAL)")
            continue
        
        sql = text("""
            UPDATE part_operations po
            SET mhr = COALESCE(
                CASE
                    WHEN po.machine_spec IS NULL THEN NULL
                    ELSE
                        COALESCE(
                            (SELECT m.hour_rate 
                             FROM machines m 
                             WHERE m.machine_name = po.machine_spec 
                               AND m.is_active = TRUE 
                             LIMIT 1), 0
                        )
                        + COALESCE(
                            (SELECT lt.hourly_rate 
                             FROM labor_types lt 
                             WHERE lt.labor_code = po.labour_type 
                             LIMIT 1), 0
                        ) * COALESCE(po.no_of_labour, 0) * 1.05
                END,
                0
            )
            WHERE po.id = :operation_id
              AND po.is_active = TRUE
        """)
        
        conn.execute(sql, {"operation_id": op_id})
    
    print(f"MHR updated for part_cost_id={part_cost_id}")


def update_process_cost(engine, part_cost_id: int):
    """
    Excel: =IFNA(IF(AND(AU18<>"FPO 1,2 & 3",AU18<>"FPO 4",AU18<>"FPO 4A",AU18<>"FPO 5"),
                    IF(ISBLANK(AU18),0,(((AY18+AZ18*AV18)/(60))*(BA18))),
                    VLOOKUP(AU18,Machines!$Q:$R,2,0)*$V18),0)
    
    Non-FPO: ((setup_time_min + cycle_time_min × no_of_strokes) / 60) × mhr
    FPO (Coating): cost_per_sqm × weight_kg
    
    FPO machines: 'FPO 1,2 & 3', 'FPO 4', 'FPO 4A', 'FPO 5' (with spaces)
    
    UPDATED: Now respects manual overrides
    """
    with engine.begin() as conn:
        ops_sql = text("""
            SELECT id FROM part_operations 
            WHERE part_cost_id = :part_cost_id AND is_active = TRUE
        """)
        operations = conn.execute(ops_sql, {"part_cost_id": part_cost_id}).fetchall()
        
        for op_row in operations:
            op_id = op_row[0]
            
            # Skip if manually overridden
            if is_field_manual(part_cost_id, f"op_{op_id}_process_cost"):
                print(f"  Skipped process_cost for operation {op_id} (MANUAL)")
                continue
            
            sql = text("""
                UPDATE part_operations po
                SET process_cost = COALESCE(
                    CASE
                        -- Non-coating operations (NOT FPO)
                        WHEN po.machine_spec IS NOT NULL
                             AND po.machine_spec NOT IN ('FPO 1,2 & 3', 'FPO 4', 'FPO 4A', 'FPO 5')
                        THEN
                            (
                                (COALESCE(po.setup_time_min, 0)
                                + COALESCE(po.cycle_time_min, 0) * COALESCE(po.no_of_strokes, 0))
                                / 60.0
                            ) * COALESCE(po.mhr, 0)
                            
                        -- Coating operations (FPO)
                        WHEN po.machine_spec IN ('FPO 1,2 & 3', 'FPO 4', 'FPO 4A', 'FPO 5')
                        THEN
                            COALESCE(
                                (SELECT cc.cost_per_sqm 
                                 FROM coating_costs_part cc 
                                 WHERE cc.operation_name = po.machine_spec
                                 LIMIT 1
                                ), 0
                            ) * COALESCE(pc.weight_kg, 0)
                            
                        -- No machine spec
                        ELSE 0
                    END,
                    0
                )
                FROM part_cost pc
                WHERE po.part_cost_id = pc.id
                  AND po.id = :operation_id
                  AND po.is_active = TRUE
            """)
            
            conn.execute(sql, {"operation_id": op_id})

    print(f"Process cost updated for part_cost_id={part_cost_id}")


def update_total_process_cost(conn, part_cost_id: int):
    """total_process_cost_jpy = SUM(process_cost) from all operations"""

    sql = text("""
        UPDATE part_cost pc
        SET total_process_cost_jpy = COALESCE(
            (SELECT SUM(COALESCE(process_cost, 0))
             FROM part_operations
             WHERE part_cost_id = :part_cost_id
               AND is_active = TRUE
            ), 0
        )
        WHERE pc.id = :part_cost_id
    """)

    conn.execute(sql, {"part_cost_id": part_cost_id})
    print(f"Total process cost updated for part_cost_id={part_cost_id}")


def update_total_rm_process_cost(conn, part_cost_id: int):
    """total_rm_process_cost_jpy = net_rm_cost + total_process_cost_jpy"""

    sql = text("""
        UPDATE part_cost
        SET total_rm_process_cost_jpy = COALESCE(net_rm_cost, 0) + COALESCE(total_process_cost_jpy, 0)
        WHERE id = :part_cost_id
    """)

    conn.execute(sql, {"part_cost_id": part_cost_id})
    print(f"Total RM + Process cost updated for part_cost_id={part_cost_id}")

def update_final_costs(conn, part_cost_id: int):
    """
    Update rejection, material_oh_cost, die_maint, mpo, sga, profit, total_cost
    UPDATED: Now respects manual overrides for each field
    """
    
    # Get current part data to check manual overrides
    part_sql = text("SELECT * FROM part_cost WHERE id = :id")
    part_row = conn.execute(part_sql, {"id": part_cost_id}).mappings().fetchone()
    if not part_row:
        return
    
    part = dict(part_row)
    
    # Get cost factors
    cf_sql = text("SELECT * FROM cost_factors LIMIT 1")
    cf_row = conn.execute(cf_sql).mappings().fetchone()
    if not cf_row:
        print("No cost_factors found")
        return
    
    cf = dict(cf_row)
    
    # Calculate each field, respecting manual overrides
    total_rm_process_cost_jpy = float(part.get('total_rm_process_cost_jpy') or 0)
    net_rm_cost = float(part.get('net_rm_cost') or 0)
    total_process_cost_jpy = float(part.get('total_process_cost_jpy') or 0)
    
    # Rejection
    if is_field_manual(part_cost_id, 'rejection'):
        rejection = float(part.get('rejection') or 0)
        print(f"Skipping rejection (MANUAL)")
    else:
        rejection = total_rm_process_cost_jpy * float(cf.get('rejection_pct') or 0)
    
    # Material OH Cost
    if is_field_manual(part_cost_id, 'material_oh_cost'):
        material_oh_cost = float(part.get('material_oh_cost') or 0)
        print(f"Skipping material_oh_cost (MANUAL)")
    else:
        material_oh_cost = net_rm_cost * float(cf.get('material_oh_pct') or 0)
    
    # Die Maintenance
    if is_field_manual(part_cost_id, 'die_maint'):
        die_maint = float(part.get('die_maint') or 0)
        print(f"Skipping die_maint (MANUAL)")
    else:
        die_maint = total_process_cost_jpy * float(cf.get('die_maint_pct') or 0)
    
    # MPO
    if is_field_manual(part_cost_id, 'mpo'):
        mpo = float(part.get('mpo') or 0)
        print(f"Skipping mpo (MANUAL)")
    else:
        mpo = total_process_cost_jpy * float(cf.get('mpo_pct') or 0)
    
    # Profit on Material
    if is_field_manual(part_cost_id, 'profit_on_material'):
        profit_on_material = float(part.get('profit_on_material') or 0)
        print(f"Skipping profit_on_material (MANUAL)")
    else:
        profit_on_material = net_rm_cost * float(cf.get('profit_material_pct') or 0)
    
    # Profit on Process
    if is_field_manual(part_cost_id, 'profit_on_process'):
        profit_on_process = float(part.get('profit_on_process') or 0)
        print(f"Skipping profit_on_process (MANUAL)")
    else:
        profit_on_process = total_process_cost_jpy * float(cf.get('profit_process_pct') or 0)
    
    # SGA (depends on calculated rejection, material_oh_cost, mpo)
    if is_field_manual(part_cost_id, 'sga'):
        sga = float(part.get('sga') or 0)
        print(f"Skipping sga (MANUAL)")
    else:
        sga = (
            total_rm_process_cost_jpy
            + rejection
            + material_oh_cost
            + mpo
        ) * float(cf.get('sga_pct') or 0)
    
    # Total Cost (always calculated from current values)
    total_cost = (
        rejection
        + material_oh_cost
        + die_maint
        + mpo
        + sga
        + profit_on_material
        + profit_on_process
    )
    
    # Update all fields
    update_sql = text("""
        UPDATE part_cost
        SET
            rejection = :rejection,
            material_oh_cost = :material_oh_cost,
            die_maint = :die_maint,
            mpo = :mpo,
            sga = :sga,
            profit_on_material = :profit_on_material,
            profit_on_process = :profit_on_process,
            total_cost = :total_cost
        WHERE id = :part_cost_id
    """)
    
    conn.execute(update_sql, {
        "rejection": round(rejection, 2),
        "material_oh_cost": round(material_oh_cost, 2),
        "die_maint": round(die_maint, 2),
        "mpo": round(mpo, 2),
        "sga": round(sga, 2),
        "profit_on_material": round(profit_on_material, 2),
        "profit_on_process": round(profit_on_process, 2),
        "total_cost": round(total_cost, 2),
        "part_cost_id": part_cost_id
    })
    
    print(f"Final cost columns updated for part_cost_id={part_cost_id}")

def update_total_part_cost_and_rate(conn, part_cost_id: int):
    """total_part_cost_jpy = total_rm_process_cost_jpy + total_cost"""

    sql = text("""
        UPDATE part_cost
        SET
            total_part_cost_jpy = COALESCE(total_rm_process_cost_jpy, 0) + COALESCE(total_cost, 0),
            rate_per_kg = CASE
                WHEN weight_kg IS NOT NULL AND weight_kg > 0
                THEN (COALESCE(total_rm_process_cost_jpy, 0) + COALESCE(total_cost, 0)) / weight_kg
                ELSE 0
            END
        WHERE id = :part_cost_id
    """)

    conn.execute(sql, {"part_cost_id": part_cost_id})
    print(f"Total part cost & rate per kg updated for part_cost_id={part_cost_id}")


# ============================================================
# MASTER RECALCULATION FUNCTION
# ============================================================

def recalculate_part_cost(part_cost_id: int):
    """
    MASTER recalculation pipeline. 
    Skips fields that have been manually overridden.
    FIXED: Now properly handles weight_kg, rm_cost_per_kg, scrap_cost_per_kg overrides
    """
    print(f"\n{'='*60}")
    print(f"RECALCULATING PART {part_cost_id}")
    print(f"{'='*60}")
    
    # Show manual overrides
    if part_cost_id in MANUAL_OVERRIDES and MANUAL_OVERRIDES[part_cost_id]:
        print(f"Manual overrides active: {MANUAL_OVERRIDES[part_cost_id]}")
    
    with engine.begin() as conn:
        part_sql = text("SELECT * FROM part_cost WHERE id = :id")
        part_row = conn.execute(part_sql, {"id": part_cost_id}).mappings().fetchone()

        if not part_row: 
            raise ValueError(f"Invalid part_cost_id: {part_cost_id}")

        part = dict(part_row)

        # Resolve material values
        material_category = part.get('material_category') or 'Steel'
        material_spec = part.get('material_spec') or None
        material_type = part.get('material_type') or 'Sheet Metal'

        # Get fresh values from lookup tables (check manual overrides first!)
        if is_field_manual(part_cost_id, 'rm_cost_per_kg'):
            rm_cost_per_kg = float(part.get('rm_cost_per_kg') or 0)
            print(f"Skipping rm_cost_per_kg (MANUAL) = {rm_cost_per_kg}")
        else:
            rm_cost_per_kg = get_rm_cost_per_kg(material_spec)
        
        if is_field_manual(part_cost_id, 'scrap_cost_per_kg'):
            scrap_cost_per_kg = float(part.get('scrap_cost_per_kg') or 0)
            print(f"Skipping scrap_cost_per_kg (MANUAL) = {scrap_cost_per_kg}")
        else:
            scrap_cost_per_kg = get_scrap_cost_per_kg(material_category)

        # Recalculate weight (check manual override first!)
        if is_field_manual(part_cost_id, 'weight_kg'):
            weight_kg = float(part.get('weight_kg') or 0)
            print(f"Skipping weight_kg (MANUAL) = {weight_kg}")
        else:
            volume_cu_m = float(part.get('volume_cu_m') or 0)
            volume_mm3 = volume_cu_m * 1_000_000_000

            if volume_mm3 > 0:
                weight_kg = calculate_weight_kg(volume_mm3, material_category)
            else:
                weight_kg = float(part.get('weight_kg') or 0)

        # Recalculate batch quantity
        epu_nos = float(part.get('epu_nos')) if part.get('epu_nos') else None
        no_of_batch_per_year = float(part.get('no_of_batch_per_year') or 12.0)
        batch_qty = calculate_batch_qty(epu_nos, no_of_batch_per_year) if epu_nos else None

        # Strip sizes
        blank_length_mm = float(part.get('blank_length_mm') or 0)
        blank_width_mm = float(part.get('blank_width_mm') or 0)
        part_thick_mm = float(part.get('part_thick_mm') or 0)
        web_allowance_length_mm = float(part.get('web_allowance_length_mm') or 2)
        web_allowance_width_mm = float(part.get('web_allowance_width_mm') or 1)
        draw_bead_allowance_length_mm = part.get('draw_bead_allowance_length_mm')
        draw_bead_allowance_width_mm = part.get('draw_bead_allowance_width_mm')

        # Strip size width (check manual override)
        if is_field_manual(part_cost_id, 'strip_size_width_mm'):
            strip_size_width_mm = float(part.get('strip_size_width_mm') or 0)
            print(f"Skipping strip_size_width_mm (MANUAL)")
        else:
            strip_size_width_mm = calculate_strip_size_width(
                blank_length_mm, web_allowance_length_mm,
                part_thick_mm, draw_bead_allowance_length_mm
            )

        # Strip size pitch (check manual override)
        if is_field_manual(part_cost_id, 'strip_size_pitch_mm'):
            strip_size_pitch_mm = float(part.get('strip_size_pitch_mm') or 0)
            print(f"Skipping strip_size_pitch_mm (MANUAL)")
        else:
            strip_size_pitch_mm = calculate_strip_size_pitch(
                blank_width_mm, web_allowance_width_mm,
                part_thick_mm, draw_bead_allowance_width_mm
            )

        # No of parts per blank (check manual override)
        standard_sheet_length_mm = float(part.get('standard_sheet_length_mm') or 2438.0)
        standard_sheet_width_mm = float(part.get('standard_sheet_width_mm') or 1219.0)

        if is_field_manual(part_cost_id, 'no_of_part_per_blank'):
            no_of_part_per_blank = int(part.get('no_of_part_per_blank') or 1)
            print(f"Skipping no_of_part_per_blank (MANUAL)")
        else:
            no_of_part_per_blank = calculate_no_of_part_per_blank(
                standard_sheet_length_mm, standard_sheet_width_mm,
                strip_size_width_mm, strip_size_pitch_mm
            )

        # Blank weight (check manual override)
        if is_field_manual(part_cost_id, 'blank_wt'):
            blank_wt = float(part.get('blank_wt') or 0)
            print(f"Skipping blank_wt (MANUAL)")
        else:
            part_width_mm = float(part.get('part_width_mm') or 0)
            part_height_mm = float(part.get('part_height_mm') or 0)
            part_length_mm = float(part.get('part_length_mm') or 0)

            blank_wt = calculate_blank_weight(
                material_type, material_category,
                part_width_mm, part_height_mm, part_thick_mm, part_length_mm,
                standard_sheet_length_mm, standard_sheet_width_mm,
                no_of_part_per_blank
            )

        # RM cost per part (check manual override)
        if is_field_manual(part_cost_id, 'rm_cost_per_part'):
            rm_cost_per_part = float(part.get('rm_cost_per_part') or 0)
            print(f"Skipping rm_cost_per_part (MANUAL)")
        else:
            rm_cost_per_part = rm_cost_per_kg * blank_wt if part_thick_mm > 0 else 0.0

        # Scrap weight (check manual override)
        if is_field_manual(part_cost_id, 'scrap_wt'):
            scrap_wt = float(part.get('scrap_wt') or 0)
            print(f"Skipping scrap_wt (MANUAL)")
        else:
            scrap_wt = calculate_scrap_weight(rm_cost_per_part, blank_wt, weight_kg)
        
        # Scrap cost per part (check manual override)
        if is_field_manual(part_cost_id, 'scrap_cost_per_part'):
            scrap_cost_per_part = float(part.get('scrap_cost_per_part') or 0)
            print(f"Skipping scrap_cost_per_part (MANUAL)")
        else:
            scrap_cost_per_part = calculate_scrap_cost_per_part(scrap_wt, scrap_cost_per_kg)

        # Net RM cost (always calculated from current values)
        net_rm_cost = calculate_net_rm_cost(rm_cost_per_part, scrap_cost_per_part)

        # Perimeter (check manual override)
        if is_field_manual(part_cost_id, 'outer_perimeter_mm'):
            outer_perimeter_mm = float(part.get('outer_perimeter_mm') or 0)
            print(f"Skipping outer_perimeter_mm (MANUAL)")
        else:
            outer_perimeter_mm = calculate_outer_perimeter_mm(material_type, blank_length_mm, blank_width_mm)
        
        # Tonnage (check manual override)
        if is_field_manual(part_cost_id, 'approx_blank_ton'):
            approx_blank_ton = float(part.get('approx_blank_ton') or 0)
            print(f"Skipping approx_blank_ton (MANUAL)")
        else:
            approx_blank_ton = calculate_approx_blank_ton(material_type, outer_perimeter_mm, part_thick_mm)

        # Update part_cost
        update_part_sql = text("""
            UPDATE part_cost
            SET
                rm_cost_per_kg = :rm_cost_per_kg,
                scrap_cost_per_kg = :scrap_cost_per_kg,
                weight_kg = :weight_kg,
                batch_qty = :batch_qty,
                strip_size_width_mm = :strip_size_width_mm,
                strip_size_pitch_mm = :strip_size_pitch_mm,
                no_of_part_per_blank = :no_of_part_per_blank,
                blank_wt = :blank_wt,
                rm_cost_per_part = :rm_cost_per_part,
                scrap_wt = :scrap_wt,
                scrap_cost_per_part = :scrap_cost_per_part,
                net_rm_cost = :net_rm_cost,
                outer_perimeter_mm = :outer_perimeter_mm,
                approx_blank_ton = :approx_blank_ton
            WHERE id = :id
        """)

        conn.execute(update_part_sql, {
            "rm_cost_per_kg": rm_cost_per_kg,
            "scrap_cost_per_kg": scrap_cost_per_kg,
            "weight_kg": weight_kg,
            "batch_qty": batch_qty,
            "strip_size_width_mm": strip_size_width_mm,
            "strip_size_pitch_mm": strip_size_pitch_mm,
            "no_of_part_per_blank": no_of_part_per_blank,
            "blank_wt": blank_wt,
            "rm_cost_per_part": round(rm_cost_per_part, 2),
            "scrap_wt": scrap_wt,
            "scrap_cost_per_part": round(scrap_cost_per_part, 2),
            "net_rm_cost": round(net_rm_cost, 2),
            "outer_perimeter_mm": outer_perimeter_mm,
            "approx_blank_ton": approx_blank_ton,
            "id": part_cost_id
        })

        print(f"Part cost base values recalculated")
        # Recalculate operations (preserves MANUAL overrides)
        assign_machine_to_operations(conn, part_cost_id)
        update_operation_labour_and_strokes(conn, part_cost_id)
        update_setup_time_min(conn, part_cost_id)
        update_cycle_time_min(conn, part_cost_id)
        update_mhr(conn, part_cost_id)

    # Process cost (separate transaction)
    update_process_cost(engine, part_cost_id)

    with engine.begin() as conn:
        update_total_process_cost(conn, part_cost_id)
        update_total_rm_process_cost(conn, part_cost_id)
        update_final_costs(conn, part_cost_id)
        update_total_part_cost_and_rate(conn, part_cost_id)

    print(f"Full recalculation complete for part_cost_id={part_cost_id}")
    print(f"{'='*60}\n")

# ============================================================
# DATA ACCESS FUNCTIONS
# ============================================================

def get_part_cost_by_id(part_cost_id: int):
    """Get part_cost record by ID"""
    sql = text("SELECT * FROM part_cost WHERE id = :id")
    with engine.connect() as conn:
        row = conn.execute(sql, {"id": part_cost_id}).mappings().fetchone()
        return dict(row) if row else None


def get_part_operations_by_part_id(part_cost_id: int):
    """Get all operations for a part"""
    sql = text("""
        SELECT *
        FROM part_operations
        WHERE part_cost_id = :id AND is_active = TRUE
        ORDER BY id
    """)
    with engine.connect() as conn:
        rows = conn.execute(sql, {"id": part_cost_id}).mappings().fetchall()
        return [dict(r) for r in rows]


def get_available_op_stages_for_part(part_cost_id: int):
    """
    Returns op_stages that are NOT yet used for this part.
    Helps frontend show only available options.
    """
    all_stages = get_op_stage_options()

    sql = text("""
        SELECT op_stage
        FROM part_operations
        WHERE part_cost_id = :part_cost_id
          AND is_active = TRUE
    """)

    with engine.connect() as conn:
        used_stages = [row[0] for row in conn.execute(sql, {"part_cost_id": part_cost_id}).fetchall()]

    return [s for s in all_stages if s not in used_stages]

def get_part_id_from_operation(operation_id: int) -> int:
    """Get part_cost_id from operation_id"""
    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT part_cost_id FROM part_operations WHERE id = :id"),
            {"id": operation_id}
        ).fetchone()
        
        if not result:
            raise ValueError(f"Operation {operation_id} not found")
        
        return result[0]

# ============================================================
# UPDATE FUNCTIONS (with recalculation)
# ============================================================

# Track manual overrides: {part_cost_id: {field_name, ...}}
MANUAL_OVERRIDES = {}

def mark_field_as_manual(part_cost_id: int, field_name: str):
    """Mark a field as manually overridden - won't be recalculated"""
    if part_cost_id not in MANUAL_OVERRIDES:
        MANUAL_OVERRIDES[part_cost_id] = set()
    MANUAL_OVERRIDES[part_cost_id].add(field_name)
    print(f"Marked {field_name} as MANUAL for part {part_cost_id}")

def is_field_manual(part_cost_id: int, field_name: str) -> bool:
    """Check if a field has been manually overridden"""
    return part_cost_id in MANUAL_OVERRIDES and field_name in MANUAL_OVERRIDES[part_cost_id]

def clear_manual_override(part_cost_id: int, field_name: str):
    """Clear manual override - field will be auto-calculated again"""
    if part_cost_id in MANUAL_OVERRIDES:
        MANUAL_OVERRIDES[part_cost_id].discard(field_name)
        print(f"Cleared MANUAL flag for {field_name} on part {part_cost_id}")

def reset_all_manual_overrides(part_cost_id: int):
    """Reset all manual overrides for a part - all fields will be recalculated"""
    if part_cost_id in MANUAL_OVERRIDES:
        del MANUAL_OVERRIDES[part_cost_id]
        print(f"Cleared ALL manual overrides for part {part_cost_id}")

# ============================================================
# REPLACE YOUR update_part_cost_field_raw FUNCTION WITH THIS
# ============================================================

def update_part_cost_field_raw(part_cost_id: int, field_name: str, value, edited_by: str = None):
    """
    Update a single field in part_cost table. 
    ALWAYS triggers recalculation after update.
    Tracks which fields have been manually edited.
    Marks part as unsaved when edited.
    """
    print(f"\n{'='*60}")
    print(f"UPDATE PART FIELD")
    print(f"{'='*60}")
    print(f"Part ID: {part_cost_id}")
    print(f"Field: {field_name}")
    print(f"Value: {value} (type: {type(value).__name__})")
    
    if field_name in SYSTEM_READONLY_FIELDS:
        error_msg = f"'{field_name}' is system-calculated and cannot be edited"
        print(f"ERROR: {error_msg}")
        raise ValueError(error_msg)

    if field_name not in USER_EDITABLE_FIELDS:
        print(f"WARNING: '{field_name}' is not in USER_EDITABLE_FIELDS")

    try:
        # Mark as manual override if it's an overridable calculated field
        if field_name in OVERRIDABLE_CALCULATED_FIELDS:
            mark_field_as_manual(part_cost_id, field_name)
        
        # Track that this field was manually edited
        mark_field_as_edited(part_cost_id, field_name, edited_by)
        
        with engine.begin() as conn:
            # Update the field value
            sql = text(f"UPDATE part_cost SET {field_name} = :value WHERE id = :id")
            result = conn.execute(sql, {"value": value, "id": part_cost_id})
            
            rows_affected = result.rowcount
            print(f"Rows affected: {rows_affected}")
            
            if rows_affected == 0:
                raise ValueError(f"Part with id {part_cost_id} not found")
            
            # Mark as unsaved (has pending changes)
            conn.execute(
                text("UPDATE part_cost SET is_saved = FALSE WHERE id = :id"),
                {"id": part_cost_id}
            )
        
        print(f"Database updated: {field_name} = {value}")
        print(f"Part marked as UNSAVED")
        print(f"AUTO-RECALCULATING...")
        
        # ALWAYS recalculate
        recalculate_part_cost(part_cost_id)
        
        print(f"AUTO-RECALCULATION COMPLETE")
        print(f"{'='*60}\n")
        
    except Exception as e:
        print(f"ERROR during update: {e}")
        import traceback
        traceback.print_exc()
        raise

def update_operation_field_raw(operation_id: int, field_name: str, value, edited_by: str = None):
    """
    Update a single field in part_operations table.
    ALWAYS triggers recalculation after update.
    Tracks which fields have been manually edited.
    Marks parent part as unsaved.
    """
    print(f"\n{'='*60}")
    print(f"UPDATE OPERATION FIELD")
    print(f"{'='*60}")
    print(f"Operation ID: {operation_id}")
    print(f"Field: {field_name}")
    print(f"Value: {value} (type: {type(value).__name__})")
    
    if field_name in OPERATION_READONLY_FIELDS: 
        error_msg = f"'{field_name}' cannot be edited"
        print(f"ERROR: {error_msg}")
        raise ValueError(error_msg)

    if field_name not in OPERATION_EDITABLE_FIELDS:
        error_msg = f"'{field_name}' is not an editable field"
        print(f"ERROR: {error_msg}")
        raise ValueError(error_msg)

    try:
        with engine.begin() as conn:
            # Get the part_cost_id first
            result = conn.execute(
                text("SELECT part_cost_id FROM part_operations WHERE id = :operation_id"),
                {"operation_id": operation_id}
            ).fetchone()

            if not result:
                raise ValueError(f"Operation {operation_id} not found")

            part_cost_id = result[0]
            print(f"Part ID: {part_cost_id}")

            # Mark as manual override if applicable
            if field_name in OVERRIDABLE_CALCULATED_FIELDS:
                override_key = f"op_{operation_id}_{field_name}"
                mark_field_as_manual(part_cost_id, override_key)
            
            # Track that this field was manually edited
            mark_operation_field_as_edited(operation_id, field_name, edited_by)

            if field_name == "machine_spec":
                sql = text("""
                    UPDATE part_operations 
                    SET machine_spec = :value,
                        machine_spec_source = 'MANUAL'
                    WHERE id = :operation_id
                """)
                print("Setting machine_spec_source = 'MANUAL'")
            elif field_name == "labour_type":
                sql = text("""
                    UPDATE part_operations 
                    SET labour_type = :value,
                        labour_type_source = 'MANUAL'
                    WHERE id = :operation_id
                """)
                print("Setting labour_type_source = 'MANUAL'")
            else:
                sql = text(f"""
                    UPDATE part_operations 
                    SET {field_name} = :value 
                    WHERE id = :operation_id
                """)
            
            result = conn.execute(sql, {
                "value": value, 
                "operation_id": operation_id
            })
            
            rows_affected = result.rowcount
            print(f"Rows affected: {rows_affected}")
            
            if rows_affected == 0:
                raise ValueError(f"No rows updated for operation {operation_id}")
            
            # Mark parent part as unsaved
            conn.execute(
                text("UPDATE part_cost SET is_saved = FALSE WHERE id = :id"),
                {"id": part_cost_id}
            )

        print(f"Database updated: {field_name} = {value}")
        print(f"Part marked as UNSAVED")
        print(f"AUTO-RECALCULATING...")
        
        # ALWAYS recalculate
        recalculate_part_cost(part_cost_id)
        
        print(f"AUTO-RECALCULATION COMPLETE")
        print(f"{'='*60}\n")
        
    except Exception as e:
        print(f"ERROR during update: {e}")
        import traceback
        traceback.print_exc()
        raise

def update_machine_spec_for_operation(operation_id: int, machine_spec: str):
    """
    Manually set machine_spec for an operation. 
    Sets machine_spec_source to 'MANUAL' so it won't be overwritten.
    """
    sql = text("""
        UPDATE part_operations
        SET 
            machine_spec = :machine_spec,
            machine_spec_source = 'MANUAL'
        WHERE id = :operation_id
          AND is_active = TRUE
    """)

    with engine.begin() as conn:
        result = conn.execute(
            text("SELECT part_cost_id FROM part_operations WHERE id = :id"),
            {"id": operation_id}
        ).fetchone()

        if not result:
            raise ValueError(f"Operation {operation_id} not found")

        part_cost_id = result[0]

        conn.execute(sql, {
            "machine_spec": machine_spec,
            "operation_id": operation_id
        })

    print(f"Machine spec manually set to '{machine_spec}' for operation_id={operation_id}")
    recalculate_part_cost(part_cost_id)


def update_labour_type_for_operation(operation_id: int, labour_type: str):
    """
    Manually set labour_type for an operation. 
    Sets labour_type_source to 'MANUAL' so it won't be overwritten.
    """
    sql = text("""
        UPDATE part_operations
        SET
            labour_type = :labour_type,
            labour_type_source = 'MANUAL'
        WHERE id = :operation_id
          AND is_active = TRUE
    """)

    with engine.begin() as conn:
        result = conn.execute(
            text("SELECT part_cost_id FROM part_operations WHERE id = :id"),
            {"id": operation_id}
        ).fetchone()

        if not result: 
            raise ValueError(f"Operation {operation_id} not found")

        part_cost_id = result[0]

        conn.execute(sql, {
            "labour_type": labour_type,
            "operation_id": operation_id
        })

    print(f"Labour type manually set to '{labour_type}' for operation_id={operation_id}")
    recalculate_part_cost(part_cost_id)


def update_op_stage_and_name(operation_id: int, op_stage: str, op_name: str):
    """Updates OP Stage and OP Name for an operation"""
    sql = text("""
        UPDATE part_operations
        SET op_stage = :op_stage, op_name = :op_name
        WHERE id = :operation_id AND is_active = TRUE
    """)

    with engine.begin() as conn:
        result = conn.execute(
            text("SELECT part_cost_id FROM part_operations WHERE id = :id"),
            {"id": operation_id}
        ).fetchone()

        if not result:
            raise ValueError(f"Operation {operation_id} not found")

        part_cost_id = result[0]

        conn.execute(sql, {
            "op_stage":  op_stage,
            "op_name": op_name,
            "operation_id": operation_id
        })

    print(f"Updated OP Stage={op_stage}, OP Name={op_name} for operation_id={operation_id}")
    recalculate_part_cost(part_cost_id)

# ============================================================
# FIELD EDIT TRACKING FUNCTIONS
# ============================================================

def mark_field_as_edited(part_cost_id: int, field_name: str, edited_by: str = None):
    """
    Mark a field as manually edited in part_cost table
    This will be used to highlight the field in UI
    """
    sql = text("""
        INSERT INTO part_field_edits (part_cost_id, field_name, edited_by)
        VALUES (:part_cost_id, :field_name, :edited_by)
        ON CONFLICT (part_cost_id, field_name) 
        DO UPDATE SET edited_at = CURRENT_TIMESTAMP, edited_by = :edited_by
    """)
    
    with engine.begin() as conn:
        conn.execute(sql, {
            "part_cost_id": part_cost_id,
            "field_name": field_name,
            "edited_by": edited_by
        })
    
    print(f"Marked {field_name} as edited for part {part_cost_id}")


def mark_operation_field_as_edited(operation_id: int, field_name: str, edited_by: str = None):
    """
    Mark a field as manually edited in part_operations table
    """
    sql = text("""
        INSERT INTO operation_field_edits (operation_id, field_name, edited_by)
        VALUES (:operation_id, :field_name, :edited_by)
        ON CONFLICT (operation_id, field_name) 
        DO UPDATE SET edited_at = CURRENT_TIMESTAMP, edited_by = :edited_by
    """)
    
    with engine.begin() as conn:
        conn.execute(sql, {
            "operation_id": operation_id,
            "field_name": field_name,
            "edited_by": edited_by
        })
    
    print(f"Marked {field_name} as edited for operation {operation_id}")


def get_edited_fields_for_part(part_cost_id: int) -> dict:
    """
    Get all manually edited fields for a part
    Returns: {field_name: {edited_at, edited_by}, ...}
    """
    sql = text("""
        SELECT field_name, edited_at, edited_by
        FROM part_field_edits
        WHERE part_cost_id = :part_cost_id
    """)
    
    with engine.connect() as conn:
        rows = conn.execute(sql, {"part_cost_id": part_cost_id}).mappings().fetchall()
        return {
            row['field_name']: {
                'edited_at': row['edited_at'].isoformat() if row['edited_at'] else None,
                'edited_by': row['edited_by']
            }
            for row in rows
        }


def get_edited_fields_for_operation(operation_id: int) -> dict:
    """
    Get all manually edited fields for an operation
    Returns: {field_name: {edited_at, edited_by}, ...}
    """
    sql = text("""
        SELECT field_name, edited_at, edited_by
        FROM operation_field_edits
        WHERE operation_id = :operation_id
    """)
    
    with engine.connect() as conn:
        rows = conn.execute(sql, {"operation_id": operation_id}).mappings().fetchall()
        return {
            row['field_name']: {
                'edited_at': row['edited_at'].isoformat() if row['edited_at'] else None,
                'edited_by': row['edited_by']
            }
            for row in rows
        }


def clear_field_edit_flag(part_cost_id: int, field_name: str):
    """
    Clear edit flag for a field (when user wants to reset to auto-calculation)
    """
    sql = text("""
        DELETE FROM part_field_edits
        WHERE part_cost_id = :part_cost_id AND field_name = :field_name
    """)
    
    with engine.begin() as conn:
        conn.execute(sql, {
            "part_cost_id": part_cost_id,
            "field_name": field_name
        })
    
    print(f"Cleared edit flag for {field_name} on part {part_cost_id}")


def clear_operation_field_edit_flag(operation_id: int, field_name: str):
    """
    Clear edit flag for an operation field
    """
    sql = text("""
        DELETE FROM operation_field_edits
        WHERE operation_id = :operation_id AND field_name = :field_name
    """)
    
    with engine.begin() as conn:
        conn.execute(sql, {
            "operation_id": operation_id,
            "field_name": field_name
        })
    
    print(f"Cleared edit flag for {field_name} on operation {operation_id}")


def get_all_field_statuses_for_part(part_cost_id: int) -> dict:
    """
    Get comprehensive field status information for a part
    Returns which fields are edited, calculated, or system-readonly
    """
    edited_fields = get_edited_fields_for_part(part_cost_id)
    
    # Get all operations for this part
    operations = get_part_operations_by_part_id(part_cost_id)
    operation_edits = {}
    
    for op in operations:
        op_id = op['id']
        operation_edits[op_id] = get_edited_fields_for_operation(op_id)
    
    return {
        "part_cost_id": part_cost_id,
        "part_edited_fields": edited_fields,
        "operation_edited_fields": operation_edits,
        "system_readonly_fields": list(SYSTEM_READONLY_FIELDS),
        "user_editable_fields": list(USER_EDITABLE_FIELDS),
        "overridable_calculated_fields": list(OVERRIDABLE_CALCULATED_FIELDS)
    }

# ============================================================
# OPERATION MANAGEMENT FUNCTIONS
# ============================================================

def add_operation_to_part(part_cost_id: int, op_stage: str, op_name: str = ""):
    """
    Add a new operation row for a part.
    User can add up to 11 operations (OP1-OP10 + CF).
    """

    with engine.connect() as conn:
        part_row = conn.execute(
            text("SELECT part_number FROM part_cost WHERE id = :id"),
            {"id": part_cost_id}
        ).fetchone()

        if not part_row:
            raise ValueError(f"Part cost {part_cost_id} not found")

        part_number = part_row[0]

    insert_sql = text("""
        INSERT INTO part_operations (
            part_cost_id, part_number, op_stage, op_name,
            is_active, labour_type_source, machine_spec_source
        )
        VALUES (
            :part_cost_id, :part_number, :op_stage, :op_name,
            TRUE, 'AUTO', 'AUTO'
        )
        RETURNING id
    """)

    with engine.begin() as conn:
        result = conn.execute(insert_sql, {
            "part_cost_id": part_cost_id,
            "part_number": part_number,
            "op_stage": op_stage,
            "op_name":  op_name
        })
        operation_id = result.fetchone()[0]

    print(f"Added operation {op_stage} ({op_name}) for part_cost_id={part_cost_id}")

    recalculate_part_cost(part_cost_id)

    return operation_id


def delete_operation(operation_id: int):
    """
    Soft delete an operation (set is_active = FALSE).
    """

    with engine.begin() as conn:
        result = conn.execute(
            text("SELECT part_cost_id FROM part_operations WHERE id = :id"),
            {"id": operation_id}
        ).fetchone()

        if not result:
            raise ValueError(f"Operation {operation_id} not found")

        part_cost_id = result[0]

        conn.execute(
            text("UPDATE part_operations SET is_active = FALSE WHERE id = :id"),
            {"id": operation_id}
        )

    print(f"Deleted operation_id={operation_id}")
    recalculate_part_cost(part_cost_id)


# ============================================================
# INSERT FUNCTION
# ============================================================

def insert_part_dimensions(
    dimensions: dict,
    part_number: str,
    surface_finish: str = None,
    material_spec: str = None,
    material_type: str = None,
    material_category: str = None,
    epu_nos: float = None,
    no_of_batch_per_year: float = None,
    standard_sheet_length_mm: float = 2438.0,
    standard_sheet_width_mm: float = 1219.0,
    web_allowance_length_mm: float = None,
    web_allowance_width_mm: float = None,
    draw_bead_allowance_length_mm: str = None,
    draw_bead_allowance_width_mm: str = None,
    quantity_per_assembly: int = None,
    assy_level: str = None,
    description: str = None,
    part_cat: str = None,
    part_or_assy: str = None,
    zgs: str = None,
):
    """Insert part dimensions and calculate all values"""

    print("insert_part_dimensions CALLED")
    print("Part number:", part_number)
    print("Dimensions:", dimensions)

    # Set defaults
    if web_allowance_length_mm is None:
        web_allowance_length_mm = 2
    if web_allowance_width_mm is None:
        web_allowance_width_mm = 1

    material_spec = resolve_material_spec(material_spec)
    material_type = resolve_material_type(material_type)
    material_category = resolve_material_category(material_category)

    scrap_cost_per_kg = get_scrap_cost_per_kg(material_category)
    rm_cost_per_kg = get_rm_cost_per_kg(material_spec)

    epu_nos = resolve_epu_nos(epu_nos)
    no_of_batch_per_year = resolve_no_of_batch_per_year(no_of_batch_per_year)
    batch_qty = calculate_batch_qty(epu_nos, no_of_batch_per_year) if epu_nos else None

    volume_mm3 = float(dimensions. get("Volume_mm3", 0.0))
    surface_area_mm2 = float(dimensions.get("Surface_Area_mm2", 0.0))
    volume_cu_m = volume_mm3 / 1_000_000_000
    surface_area_sq_m = surface_area_mm2 / 1_000_000

    weight_kg = calculate_weight_kg(volume_mm3, material_category)

    insert_sql = text("""
        INSERT INTO part_cost (
            part_number, material_spec, part_length_mm, part_width_mm, part_height_mm, part_thick_mm,
            blank_length_mm, blank_width_mm, standard_sheet_length_mm, standard_sheet_width_mm,
            web_allowance_length_mm, web_allowance_width_mm, draw_bead_allowance_length_mm, draw_bead_allowance_width_mm,
            rm_cost_per_kg, volume_cu_m, surface_area_sq_m, material_type, material_category, surface_finish,
            weight_kg, scrap_cost_per_kg, epu_nos, no_of_batch_per_year, batch_qty, quantity_per_assembly, assy_level,
            description, part_cat, part_or_assy, zgs
        )
        VALUES (
            :part_number, :material_spec, :part_length, :part_width, :part_height, :part_thickness,
            :blank_length, :blank_width, :std_len, :std_wid,
            :web_len, :web_wid, :bead_len, :bead_wid,
            :rm_cost, :volume_cu_m, :surface_area_sq_m, :material_type, :material_category, :surface_finish,
            :weight_kg, :scrap_cost_per_kg, :epu_nos, :no_of_batch_per_year, :batch_qty, :quantity_per_assembly, :assy_level,
            :description, :part_cat, :part_or_assy, :zgs
        )
        RETURNING id
    """)

    try:
        with engine.begin() as conn:
            result = conn.execute(insert_sql, {
                "part_number":  part_number,
                "material_spec": material_spec,
                "part_length": dimensions["Length_mm"],
                "part_width": dimensions["Width_mm"],
                "part_height":  dimensions["Height_mm"],
                "part_thickness": dimensions["Thickness_mm"],
                "blank_length": dimensions["Blank_Length_mm"],
                "blank_width": dimensions["Blank_Width_mm"],
                "std_len": standard_sheet_length_mm,
                "std_wid": standard_sheet_width_mm,
                "web_len": web_allowance_length_mm,
                "web_wid": web_allowance_width_mm,
                "bead_len": draw_bead_allowance_length_mm,
                "bead_wid": draw_bead_allowance_width_mm,
                "rm_cost": rm_cost_per_kg,
                "volume_cu_m": volume_cu_m,
                "surface_area_sq_m": surface_area_sq_m,
                "material_type": material_type,
                "material_category":  material_category,
                "surface_finish": surface_finish,
                "weight_kg": weight_kg,
                "scrap_cost_per_kg": scrap_cost_per_kg,
                "epu_nos": epu_nos,
                "no_of_batch_per_year": no_of_batch_per_year,
                "batch_qty": batch_qty,
                "quantity_per_assembly": quantity_per_assembly,
                "assy_level": assy_level,
                "description": description,
                'part_cat': part_cat,
                'part_or_assy': part_or_assy,
                'zgs': zgs
            })

            part_cost_id = result.fetchone()[0]

            # Calculate all dependent values
            strip_size_width_mm = calculate_strip_size_width(
                dimensions["Blank_Length_mm"], web_allowance_length_mm,
                dimensions["Thickness_mm"], draw_bead_allowance_length_mm
            )
            strip_size_pitch_mm = calculate_strip_size_pitch(
                dimensions["Blank_Width_mm"], web_allowance_width_mm,
                dimensions["Thickness_mm"], draw_bead_allowance_width_mm
            )
            no_of_part_per_blank = calculate_no_of_part_per_blank(
                standard_sheet_length_mm, standard_sheet_width_mm,
                strip_size_width_mm, strip_size_pitch_mm
            )
            blank_wt = calculate_blank_weight(
                material_type, material_category,
                dimensions["Width_mm"], dimensions["Height_mm"],
                dimensions["Thickness_mm"], dimensions["Length_mm"],
                standard_sheet_length_mm, standard_sheet_width_mm,
                no_of_part_per_blank
            )

            rm_cost_per_part = rm_cost_per_kg * blank_wt if dimensions["Thickness_mm"] > 0 else 0.0
            scrap_wt = calculate_scrap_weight(rm_cost_per_part, blank_wt, weight_kg)
            scrap_cost_per_part = calculate_scrap_cost_per_part(scrap_wt, scrap_cost_per_kg)
            net_rm_cost = calculate_net_rm_cost(rm_cost_per_part, scrap_cost_per_part)
            outer_perimeter_mm = calculate_outer_perimeter_mm(
                material_type, dimensions["Blank_Length_mm"], dimensions["Blank_Width_mm"]
            )
            approx_blank_ton = calculate_approx_blank_ton(
                material_type, outer_perimeter_mm, dimensions["Thickness_mm"]
            )

            # Update part_cost with calculated values
            update_sql = text("""
                UPDATE part_cost
                SET 
                    strip_size_width_mm = :strip_width,
                    strip_size_pitch_mm = :strip_pitch,
                    no_of_part_per_blank = :no_parts,
                    rm_cost_per_part = :rm_cost_per_part,
                    blank_wt = :blank_wt,
                    scrap_wt = :scrap_wt,
                    scrap_cost_per_part = :scrap_cost_per_part,
                    net_rm_cost = :net_rm_cost,
                    outer_perimeter_mm = :outer_perimeter_mm,
                    approx_blank_ton = :approx_blank_ton
                WHERE id = :id
            """)

            conn.execute(update_sql, {
                "strip_width": strip_size_width_mm,
                "strip_pitch": strip_size_pitch_mm,
                "no_parts": no_of_part_per_blank,
                "blank_wt": blank_wt,
                "rm_cost_per_part": round(rm_cost_per_part, 2),
                "scrap_wt": scrap_wt,
                "scrap_cost_per_part": round(scrap_cost_per_part, 2),
                "net_rm_cost": round(net_rm_cost, 2),
                "outer_perimeter_mm": outer_perimeter_mm,
                "approx_blank_ton": approx_blank_ton,
                "id":  part_cost_id
            })

            # Create default operations (2 rows:  OP1, OP2)
            #create_default_operations(conn, part_cost_id, part_number)

            # Calculate operations
            assign_machine_to_operations(conn, part_cost_id)
            update_operation_labour_and_strokes(conn, part_cost_id)
            update_setup_time_min(conn, part_cost_id)
            update_cycle_time_min(conn, part_cost_id)
            update_mhr(conn, part_cost_id)

        # Process cost (separate transaction)
        update_process_cost(engine, part_cost_id)

        with engine.begin() as conn:
            update_total_process_cost(conn, part_cost_id)
            update_total_rm_process_cost(conn, part_cost_id)
            update_final_costs(conn, part_cost_id)
            update_total_part_cost_and_rate(conn, part_cost_id)

        print(f"✓ Part inserted successfully with id={part_cost_id}")

    except Exception as e:
        print("DB INSERT FAILED")
        print(e)
        raise

    return part_cost_id


# ============================================================
# UTILITY FUNCTIONS
# ============================================================

def get_all_parts():
    """Get all parts from part_cost table"""
    sql = text("""
        SELECT id, part_number, material_spec, material_category, weight_kg, 
               total_part_cost_jpy, rate_per_kg
        FROM part_cost
        ORDER BY id DESC
    """)
    with engine.connect() as conn:
        rows = conn.execute(sql).mappings().fetchall()
        return [dict(r) for r in rows]


def search_parts_by_number(part_number:  str):
    """Search parts by part number (partial match)"""
    sql = text("""
        SELECT id, part_number, material_spec, material_category, weight_kg, 
               total_part_cost_jpy, rate_per_kg
        FROM part_cost
        WHERE part_number ILIKE :search
        ORDER BY id DESC
    """)
    with engine.connect() as conn:
        rows = conn.execute(sql, {"search": f"%{part_number}%"}).mappings().fetchall()
        return [dict(r) for r in rows]


def delete_part(part_cost_id: int):
    """
    Delete a part and all its operations.
    This is a hard delete - use with caution.
    """
    with engine.begin() as conn:
        # First delete operations
        conn.execute(
            text("DELETE FROM part_operations WHERE part_cost_id = : id"),
            {"id": part_cost_id}
        )
        # Then delete part_cost
        conn.execute(
            text("DELETE FROM part_cost WHERE id = :id"),
            {"id": part_cost_id}
        )
    
    print(f"Deleted part_cost_id={part_cost_id} and all its operations")


def duplicate_part(part_cost_id: int, new_part_number: str):
    """
    Duplicate a part with a new part number.
    Copies all values and operations. 
    """
    # Get original part
    original_part = get_part_cost_by_id(part_cost_id)
    if not original_part:
        raise ValueError(f"Part {part_cost_id} not found")
    
    # Get original operations
    original_ops = get_part_operations_by_part_id(part_cost_id)
    
    # Remove id and change part_number
    del original_part['id']
    original_part['part_number'] = new_part_number
    
    # Build column names and values
    columns = list(original_part.keys())
    placeholders = [f":{col}" for col in columns]
    
    insert_sql = text(f"""
        INSERT INTO part_cost ({', '.join(columns)})
        VALUES ({', '.join(placeholders)})
        RETURNING id
    """)
    
    with engine.begin() as conn:
        result = conn.execute(insert_sql, original_part)
        new_part_id = result.fetchone()[0]
        
        # Copy operations
        for op in original_ops:
            del op['id']
            op['part_cost_id'] = new_part_id
            op['part_number'] = new_part_number
            
            op_columns = list(op.keys())
            op_placeholders = [f":{col}" for col in op_columns]
            
            op_insert_sql = text(f"""
                INSERT INTO part_operations ({', '.join(op_columns)})
                VALUES ({', '. join(op_placeholders)})
            """)
            conn.execute(op_insert_sql, op)
    
    print(f"Duplicated part {part_cost_id} to new part {new_part_id} with number {new_part_number}")
    return new_part_id


# ============================================================
# EXPORT FUNCTIONS
# ============================================================

def get_part_cost_summary(part_cost_id: int):
    """
    Get a summary of part cost for display/export. 
    Returns a dictionary with all important values.
    """
    part = get_part_cost_by_id(part_cost_id)
    if not part:
        return None
    
    operations = get_part_operations_by_part_id(part_cost_id)
    
    return {
        "part_info": {
            "id": part. get('id'),
            "part_number": part.get('part_number'),
            "description": part.get('description'),
            "material_type": part.get('material_type'),
            "material_category":  part.get('material_category'),
            "material_spec": part.get('material_spec'),
            "surface_finish": part.get('surface_finish'),
        },
        "dimensions": {
            "part_length_mm": part.get('part_length_mm'),
            "part_width_mm": part.get('part_width_mm'),
            "part_height_mm":  part.get('part_height_mm'),
            "part_thick_mm": part.get('part_thick_mm'),
            "weight_kg": part.get('weight_kg'),
            "volume_cu_m": part.get('volume_cu_m'),
            "surface_area_sq_m": part.get('surface_area_sq_m'),
        },
        "blank_info": {
            "blank_length_mm": part.get('blank_length_mm'),
            "blank_width_mm": part. get('blank_width_mm'),
            "blank_wt": part.get('blank_wt'),
            "strip_size_width_mm": part.get('strip_size_width_mm'),
            "strip_size_pitch_mm": part. get('strip_size_pitch_mm'),
            "no_of_part_per_blank": part.get('no_of_part_per_blank'),
        },
        "production":  {
            "epu_nos": part.get('epu_nos'),
            "no_of_batch_per_year": part.get('no_of_batch_per_year'),
            "batch_qty": part.get('batch_qty'),
        },
        "rm_costs": {
            "rm_cost_per_kg": part.get('rm_cost_per_kg'),
            "rm_cost_per_part": part.get('rm_cost_per_part'),
            "scrap_wt": part.get('scrap_wt'),
            "scrap_cost_per_kg": part.get('scrap_cost_per_kg'),
            "scrap_cost_per_part":  part.get('scrap_cost_per_part'),
            "net_rm_cost": part.get('net_rm_cost'),
        },
        "operations": [
            {
                "id": op.get('id'),
                "op_stage": op.get('op_stage'),
                "op_name": op.get('op_name'),
                "machine_spec": op.get('machine_spec'),
                "no_of_strokes": op.get('no_of_strokes'),
                "labour_type": op.get('labour_type'),
                "no_of_labour": op.get('no_of_labour'),
                "setup_time_min": op.get('setup_time_min'),
                "cycle_time_min":  op.get('cycle_time_min'),
                "mhr":  op.get('mhr'),
                "process_cost":  op.get('process_cost'),
            }
            for op in operations
        ],
        "total_costs": {
            "total_process_cost_jpy": part.get('total_process_cost_jpy'),
            "total_rm_process_cost_jpy": part. get('total_rm_process_cost_jpy'),
            "rejection":  part.get('rejection'),
            "material_oh_cost":  part.get('material_oh_cost'),
            "die_maint":  part.get('die_maint'),
            "mpo": part.get('mpo'),
            "sga": part.get('sga'),
            "profit_on_material": part.get('profit_on_material'),
            "profit_on_process": part.get('profit_on_process'),
            "total_cost": part.get('total_cost'),
            "total_part_cost_jpy": part. get('total_part_cost_jpy'),
            "rate_per_kg": part.get('rate_per_kg'),
        }
    }


# ============================================================
# TEST FUNCTION
# ============================================================

def test_connection():
    """Test database connection"""
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print("✓ Database connection successful")
            return True
    except Exception as e: 
        print(f"✗ Database connection failed: {e}")
        return False


# ============================================================
# MAIN (for testing)
# ============================================================
'''
if __name__ == "__main__": 
    # Test connection
    test_connection()
    
    # Print available dropdowns
    print("\n--- Available Dropdowns ---")
    print(f"Material Categories: {get_material_category_options()}")
    print(f"Material Specs: {get_material_spec_options()[:5]}...")
    print(f"Labour Types: {get_labour_types()}")
    print(f"OP Stages: {get_op_stage_options()}")
    print(f"Surface Finishes: {get_surface_finishes()}")
    
    # Example usage
    print("\n--- Example:  Insert Part ---")
    example_dimensions = {
        "Length_mm": 240.0,
        "Width_mm": 105.0,
        "Height_mm": 51.0,
        "Thickness_mm": 1.6,
        "Blank_Length_mm": 240.0,
        "Blank_Width_mm": 135.5,
        "Volume_mm3": 49221.7,
        "Surface_Area_mm2": 140446.0
    }
    
    # Uncomment to test insert
    part_id = insert_part_dimensions(
        dimensions=example_dimensions,
        part_number="TEST-001",
        material_category="Steel",
        material_spec="HTP540"
    )
    print(f"Inserted part with ID: {part_id}")
     # Get summary
    summary = get_part_cost_summary(part_id)
    print(f"Total Part Cost: {summary['total_costs']['total_part_cost_jpy']}")
'''

# ============================================================
# SAVE/RETRIEVE FUNCTIONS
# ============================================================

def save_part_data(part_cost_id: int, saved_by: str = None):
    """
    Mark part as saved and update save timestamp
    This is called when user clicks "Save" button
    """
    sql = text("""
        UPDATE part_cost
        SET 
            is_saved = TRUE,
            last_saved_at = CURRENT_TIMESTAMP,
            last_saved_by = :saved_by
        WHERE id = :part_cost_id
        RETURNING id, part_number, last_saved_at
    """)
    
    with engine.begin() as conn:
        result = conn.execute(sql, {
            "part_cost_id": part_cost_id,
            "saved_by": saved_by
        }).mappings().fetchone()
        
        if not result:
            raise ValueError(f"Part {part_cost_id} not found")
        
        saved_data = dict(result)
        # Convert timestamp to string
        if saved_data.get('last_saved_at'):
            saved_data['last_saved_at'] = saved_data['last_saved_at'].isoformat()
        
        return saved_data


def get_all_saved_parts():
    """
    Get all parts that have been explicitly saved
    Returns list for display in "Saved Parts" view
    """
    sql = text("""
        SELECT 
            id, 
            part_number, 
            description,
            material_spec, 
            material_category, 
            weight_kg, 
            total_part_cost_jpy, 
            rate_per_kg,
            is_saved,
            last_saved_at,
            last_saved_by,
            assy_level,
            part_cat
        FROM part_cost
        WHERE is_saved = TRUE
        ORDER BY last_saved_at DESC NULLS LAST, id DESC
    """)
    
    with engine.connect() as conn:
        rows = conn.execute(sql).mappings().fetchall()
        parts = []
        for row in rows:
            part_dict = dict(row)
            # Convert timestamp to string
            if part_dict.get('last_saved_at'):
                part_dict['last_saved_at'] = part_dict['last_saved_at'].isoformat()
            parts.append(part_dict)
        return parts


def get_unsaved_parts():
    """
    Get parts that have been created but not yet saved
    """
    sql = text("""
        SELECT 
            id, 
            part_number, 
            description,
            material_spec, 
            material_category, 
            weight_kg, 
            total_part_cost_jpy, 
            rate_per_kg,
            assy_level,
            part_cat
        FROM part_cost
        WHERE is_saved = FALSE OR is_saved IS NULL
        ORDER BY id DESC
    """)
    
    with engine.connect() as conn:
        rows = conn.execute(sql).mappings().fetchall()
        return [dict(r) for r in rows]


def mark_part_as_unsaved(part_cost_id: int):
    """
    Mark part as unsaved (has pending changes)
    This is called automatically when any field is edited
    """
    sql = text("""
        UPDATE part_cost
        SET is_saved = FALSE
        WHERE id = :part_cost_id
    """)
    
    with engine.begin() as conn:
        conn.execute(sql, {"part_cost_id": part_cost_id})
    
    print(f"Marked part {part_cost_id} as UNSAVED")

# ============================================================
# DROPDOWN/LIST FUNCTIONS FOR SAVED PARTS
# ============================================================

def get_saved_parts_dropdown():
    """
    Get simple list of saved part numbers for dropdown
    Returns minimal data - just what's needed for dropdown selection
    """
    sql = text("""
        SELECT 
            id, 
            part_number,
            description,
            last_saved_at
        FROM part_cost
        WHERE is_saved = TRUE
        ORDER BY last_saved_at DESC NULLS LAST, part_number ASC
    """)
    
    with engine.connect() as conn:
        rows = conn.execute(sql).mappings().fetchall()
        parts = []
        for row in rows:
            part_dict = {
                'id': row['id'],
                'part_number': row['part_number'],
                'description': row['description'],
                'last_saved_at': row['last_saved_at'].isoformat() if row['last_saved_at'] else None
            }
            parts.append(part_dict)
        return parts



