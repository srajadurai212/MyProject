import pandas as pd
import os

# Get the absolute path to the datasets folder
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATASETS_DIR = os.path.join(BASE_DIR, "datasets")

def load_material_kb(path=None):
    if path is None:
        path = os.path.join(DATASETS_DIR, "Material_KB.csv")
    return pd.read_csv(path)

def load_material_norm(path=None):
    if path is None:
        path = os.path.join(DATASETS_DIR, "Material_Normalization.csv")
    return pd.read_csv(path)

def load_supplier_master(path=None):
    if path is None:
        path = os.path.join(DATASETS_DIR, "Supplier_Master.csv")
    return pd.read_csv(path)

# Load once globally
MATERIAL_KB = load_material_kb()
MATERIAL_NORM = load_material_norm()
SUPPLIER_MASTER = load_supplier_master()
