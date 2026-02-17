#!/usr/bin/env python3
"""
STEP File Dimension Extractor
Computes Length, Width, Height, Thickness, and Blank Size

Author: CAD Engineer
Requirements: pythonocc-core 7.9.0, numpy
"""

import sys
import math
import numpy as np
from typing import Tuple, List, Optional

from OCC.Core.STEPControl import STEPControl_Reader
from OCC.Core.IFSelect import IFSelect_RetDone
from OCC.Core.Bnd import Bnd_Box
from OCC.Core.BRepBndLib import brepbndlib
from OCC.Core.TopExp import TopExp_Explorer
from OCC.Core.TopAbs import TopAbs_FACE
from OCC.Core.GeomAbs import GeomAbs_Plane, GeomAbs_Cylinder
from OCC.Core.BRepAdaptor import BRepAdaptor_Surface
from OCC.Core.GProp import GProp_GProps
from OCC.Core.BRepGProp import brepgprop
from OCC.Core.TopoDS import topods
from OCC.Core.BRepExtrema import BRepExtrema_DistShapeShape

import sys
from app.services.postgresq import insert_part_dimensions

K_FACTOR = 0.33


def read_step_file(file_path: str):
    try:
        reader = STEPControl_Reader()
        status = reader.ReadFile(file_path)
        if status != IFSelect_RetDone:   
            return None
        reader.TransferRoots()
        shape = reader.OneShape()
        if shape.   IsNull():
            return None
        return shape
    except:   
        return None


def compute_aabb(shape):
    bbox = Bnd_Box()
    brepbndlib.Add(shape, bbox)
    xmin, ymin, zmin, xmax, ymax, zmax = bbox.Get()
    return (abs(xmax-xmin), abs(ymax-ymin), abs(zmax-zmin)), (xmin, ymin, zmin, xmax, ymax, zmax)


def get_all_faces(shape):
    faces_data = []
    explorer = TopExp_Explorer(shape, TopAbs_FACE)
    
    while explorer.More():
        face = topods.Face(explorer.Current())
        try:
            surface = BRepAdaptor_Surface(face)
            surface_type = surface.GetType()
            
            props = GProp_GProps()
            brepgprop.SurfaceProperties(face, props)
            area = props.Mass()
            center = props.CentreOfMass()
            
            face_bbox = Bnd_Box()
            brepbndlib.Add(face, face_bbox)
            fxmin, fymin, fzmin, fxmax, fymax, fzmax = face_bbox.   Get()
            
            face_info = {
                'face':   face,
                'surface_type': surface_type,
                'area': area,
                'center': np.array([center.   X(), center.Y(), center.Z()]),
                'xmin': fxmin, 'xmax': fxmax,
                'ymin': fymin, 'ymax': fymax,
                'zmin': fzmin, 'zmax':   fzmax,
                'dx': fxmax - fxmin,
                'dy': fymax - fymin,
                'dz': fzmax - fzmin
            }
            
            if surface_type == GeomAbs_Plane:
                plane = surface.Plane()
                normal = plane.  Axis().Direction()
                location = plane.Location()
                d_coeff = -(normal.X()*location.X() + normal.Y()*location.Y() + normal.Z()*location.Z())
                face_info['normal'] = np.array([normal.  X(), normal.Y(), normal.Z()])
                face_info['d_coeff'] = d_coeff
                
            elif surface_type == GeomAbs_Cylinder:
                cylinder = surface.Cylinder()
                face_info['radius'] = cylinder.  Radius()
                axis = cylinder.Axis()
                face_info['axis_direction'] = np.array([axis.Direction().X(), axis.Direction().Y(), axis.Direction().Z()])
            
            faces_data.append(face_info)
        except:
            pass
        explorer.Next()
    
    return faces_data


def get_planar_faces(faces_data):
    return [f for f in faces_data if f['surface_type'] == GeomAbs_Plane]


def get_cylindrical_faces(faces_data):
    return [f for f in faces_data if f['surface_type'] == GeomAbs_Cylinder]


def are_normals_parallel(n1, n2, tolerance=0.02):
    n1 = np.array(n1) / np.linalg.norm(n1)
    n2 = np.array(n2) / np.linalg.norm(n2)
    return abs(np.dot(n1, n2)) > (1.0 - tolerance)


def is_axis_aligned_normal(normal, tolerance=0.1):
    normal = normal / np.linalg.norm(normal)
    for axis in range(3):
        if abs(abs(normal[axis]) - 1.0) < tolerance:
            return True, axis
    return False, -1


def compute_extent_from_axis_aligned_faces(planar_faces, target_axis, aabb_extent):
    min_keys = ['xmin', 'ymin', 'zmin']
    max_keys = ['xmax', 'ymax', 'zmax']
    min_key, max_key = min_keys[target_axis], max_keys[target_axis]
    
    boundary_faces = []
    for face in planar_faces:
        if 'normal' not in face:
            continue
        is_aligned, face_axis = is_axis_aligned_normal(face['normal'])
        if is_aligned and face_axis == target_axis:   
            boundary_faces.append(face)
    
    extent_from_boundaries = None
    if len(boundary_faces) >= 2:
        positions = [(face[min_key] + face[max_key]) / 2 for face in boundary_faces]
        extent_from_boundaries = max(positions) - min(positions)
    
    parallel_faces = []
    for face in planar_faces:
        if 'normal' not in face:  
            continue
        is_aligned, face_axis = is_axis_aligned_normal(face['normal'])
        if is_aligned and face_axis != target_axis: 
            parallel_faces.append(face)
    
    extent_from_parallel = None
    if len(parallel_faces) >= 2:
        all_min = [face[min_key] for face in parallel_faces]
        all_max = [face[max_key] for face in parallel_faces]
        extent_from_parallel = max(all_max) - min(all_min)
    
    candidates = []
    if extent_from_boundaries and extent_from_boundaries > 0.1:
        candidates.append(extent_from_boundaries)
    if extent_from_parallel and extent_from_parallel > 0.1:
        candidates.append(extent_from_parallel)
    
    if not candidates:
        return aabb_extent
    
    valid_candidates = [c for c in candidates if c >= aabb_extent * 0.5]
    return min(valid_candidates) if valid_candidates else aabb_extent


def compute_bounding_box_dimensions(shape, faces_data):
    aabb_dims, _ = compute_aabb(shape)
    dims_with_axis = [(aabb_dims[0], 0), (aabb_dims[1], 1), (aabb_dims[2], 2)]
    dims_with_axis.sort(key=lambda x: x[0], reverse=True)
    
    planar_faces = get_planar_faces(faces_data)
    if len(planar_faces) < 2:
        dims = sorted(aabb_dims, reverse=True)
        return dims[0], dims[1], dims[2]
    
    computed_dims = []
    for aabb_val, axis in dims_with_axis: 
        aligned_extent = compute_extent_from_axis_aligned_faces(planar_faces, axis, aabb_val)
        computed_dims.append(aligned_extent)
    
    computed_dims.sort(reverse=True)
    return computed_dims[0], computed_dims[1], computed_dims[2]


def compute_thickness_from_planar_faces(planar_faces, max_possible):
    if len(planar_faces) < 2:
        return None
    
    thickness_candidates = []
    normal_groups = []
    
    for face in planar_faces:
        if 'normal' not in face:  
            continue
        normal = face['normal'] / np.linalg.norm(face['normal'])
        
        found_group = False
        for group in normal_groups:
            if are_normals_parallel(normal, group['normal']):
                group['faces'].append(face)
                found_group = True
                break
        if not found_group:
            normal_groups.append({'normal': normal, 'faces':    [face]})
    
    for group in normal_groups:
        faces = group['faces']
        if len(faces) < 2:
            continue
        faces_sorted = sorted(faces, key=lambda f: f['d_coeff'])
        
        for i in range(len(faces_sorted)):
            for j in range(i + 1, len(faces_sorted)):
                f1, f2 = faces_sorted[i], faces_sorted[j]
                try:
                    dist = BRepExtrema_DistShapeShape(f1['face'], f2['face'])
                    if dist.IsDone() and dist.NbSolution() > 0:
                        distance = dist.Value()
                        if 0.1 < distance < max_possible * 0.5:
                            thickness_candidates.append(distance)
                except:
                    pass
    
    if thickness_candidates:
        thickness_candidates.sort()
        groups = {}
        for t in thickness_candidates:
            found = False
            for key in groups:
                if abs(t - key) < 0.5:
                    groups[key].   append(t)
                    found = True
                    break
            if not found:
                groups[t] = [t]
        
        if groups:
            sorted_groups = sorted(groups.items(), key=lambda x: (-len(x[1]), x[0]))
            return sum(sorted_groups[0][1]) / len(sorted_groups[0][1])
    
    return None


def compute_thickness_from_cylindrical_faces(cylindrical_faces):
    if len(cylindrical_faces) < 2:
        return None
    
    radii = list(set([round(f['radius'], 3) for f in cylindrical_faces if 'radius' in f]))
    radii.sort()
    
    if len(radii) >= 2:
        return radii[1] - radii[0]
    return None


def determine_part_type(faces_data):
    planar_faces = get_planar_faces(faces_data)
    cylindrical_faces = get_cylindrical_faces(faces_data)
    
    planar_area = sum(f['area'] for f in planar_faces)
    cylindrical_area = sum(f['area'] for f in cylindrical_faces)
    total_area = planar_area + cylindrical_area
    
    if total_area == 0:
        return 'mixed'
    
    if cylindrical_area / total_area > 0.7:
        return 'cylindrical'
    elif planar_area / total_area > 0.7:
        return 'planar'
    return 'mixed'


def compute_thickness(shape, faces_data, bbox_dimensions):
    max_possible = min(bbox_dimensions)
    part_type = determine_part_type(faces_data)
    
    if part_type == 'cylindrical':
        thickness = compute_thickness_from_cylindrical_faces(get_cylindrical_faces(faces_data))
        if thickness and thickness > 0:
            return thickness
    
    planar_faces = get_planar_faces(faces_data)
    if len(planar_faces) >= 2:
        thickness = compute_thickness_from_planar_faces(planar_faces, max_possible)
        if thickness and thickness > 0:
            return thickness
    
    return 0.0

def compute_volume_and_surface_area(shape) -> Tuple[float, float]:
    """
    Computes exact volume and surface area from STEP geometry.

    Returns:
        volume_mm3 (float)
        surface_area_mm2 (float)
    """
    props = GProp_GProps()

    # Volume
    brepgprop.VolumeProperties(shape, props)
    volume_mm3 = props.Mass()

    # Surface area
    props = GProp_GProps()
    brepgprop.SurfaceProperties(shape, props)
    surface_area_mm2 = props.Mass()

    return volume_mm3, surface_area_mm2


def identify_length_axis(faces_data, aabb_dims):
    """Identify length axis from AABB (largest dimension)."""
    return int(np.argmax(aabb_dims))


def get_main_profile_bends(cylindrical_faces, length_axis, thickness):
    """
    Get main profile bends - those with axis parallel to length direction.
    These are the bends that affect the blank width calculation.
    """
    if not cylindrical_faces:
        return []
    
    length_vec = np.zeros(3)
    length_vec[length_axis] = 1.0
    
    # Group cylindrical faces into bends
    bend_groups = []
    
    for cyl in cylindrical_faces:
        if 'axis_direction' not in cyl or 'radius' not in cyl: 
            continue
        
        axis = cyl['axis_direction']
        axis_norm = axis / np.linalg.norm(axis)
        
        # Check if axis is parallel to length direction
        if abs(np.dot(axis_norm, length_vec)) < 0.9:
            continue  # Not a main profile bend
        
        radius = cyl['radius']
        center = cyl['center']
        
        # Try to group with existing bend
        found_group = False
        for group in bend_groups:
            center_dist = np.linalg.norm(center - group['center'])
            if center_dist < thickness * 5: 
                group['radii'].append(radius)
                found_group = True
                break
        
        if not found_group:
            bend_groups.append({
                'center': center. copy(),
                'radii': [radius]
            })
    
    # Extract inner radius for each bend
    bends = []
    for group in bend_groups:
        inner_radius = min(group['radii'])
        bends.append({'inner_radius': inner_radius, 'center': group['center']})
    
    return bends


def compute_bend_allowance(inner_radius, thickness, bend_angle=math.pi/2):
    """BA = angle × (R + K × T)"""
    neutral_radius = inner_radius + K_FACTOR * thickness
    return bend_angle * neutral_radius


def compute_blank_size(shape, faces_data, length, width, height, thickness):
    """
    Compute blank size for sheet metal parts.
    
    Method:
    1. Group main planar faces by normal direction
    2. For each unique normal, calculate width = total_area / (avg_length × face_count)
    3. Sum all unique normal widths
    4. Add bend allowances for main profile bends
    """
    if thickness <= 0:
        return length, width
    
    part_type = determine_part_type(faces_data)
    cylindrical_faces = get_cylindrical_faces(faces_data)
    planar_faces = get_planar_faces(faces_data)
    
    # Special case:   Cylindrical tube
    if part_type == 'cylindrical':  
        if len(cylindrical_faces) >= 2:
            radii = list(set([round(f['radius'], 3) for f in cylindrical_faces if 'radius' in f]))
            radii.sort()
            if len(radii) >= 2:
                inner_radius = radii[0]
                outer_radius = radii[-1]
                neutral_radius = (inner_radius + outer_radius) / 2
                blank_width = 2 * math.pi * neutral_radius
                return length, blank_width
    
    # Get AABB dimensions
    aabb_dims, _ = compute_aabb(shape)
    
    # Identify length axis
    length_axis = identify_length_axis(faces_data, aabb_dims)
    actual_length = aabb_dims[length_axis]
    
    # Blank length = actual length (no bends along length)
    blank_length = actual_length
    
    # Get extent keys
    extent_keys = ['dx', 'dy', 'dz']
    length_key = extent_keys[length_axis]
    
    # Get main faces (spanning >50% of length)
    min_span = actual_length * 0.5
    main_faces = [f for f in planar_faces if 'normal' in f and f[length_key] >= min_span]
    
    if not main_faces:
        min_span = actual_length * 0.3
        main_faces = [f for f in planar_faces if 'normal' in f and f[length_key] >= min_span]
    
    # Group faces by normal direction (rounded to 0.1)
    normal_groups = {}
    for f in main_faces:
        n = f['normal']
        n_norm = n / np.linalg.norm(n)
        n_key = (round(n_norm[0], 1), round(n_norm[1], 1), round(n_norm[2], 1))
        
        if n_key not in normal_groups:
            normal_groups[n_key] = []
        normal_groups[n_key].append(f)
    
    # Calculate width contribution from each unique normal direction
    total_flat_width = 0.0
    
    for n_key, faces in normal_groups.items():
        total_area = sum(f['area'] for f in faces)
        avg_length = sum(f[length_key] for f in faces) / len(faces)
        num_faces = len(faces)
        
        if avg_length > 0 and num_faces > 0:
            # Width = total_area / (avg_length × num_faces)
            # This gives the one-side width for this section
            section_width = total_area / avg_length / num_faces
            
            if section_width > thickness * 0.5:  # Ignore very thin faces
                total_flat_width += section_width
    
    # Get main profile bends and calculate bend allowances
    main_bends = get_main_profile_bends(cylindrical_faces, length_axis, thickness)
    
    total_bend_allowance = 0.0
    for bend in main_bends: 
        ba = compute_bend_allowance(bend['inner_radius'], thickness)
        total_bend_allowance += ba
    
    # Total blank width = flat sections + bend allowances
    blank_width = total_flat_width + total_bend_allowance
    
    # Sanity check
    min_expected = min(width, height)
    max_expected = width + height + len(main_bends) * 20
    
    if blank_width < min_expected * 0.8:
        # Fallback:  recalculate with different method
        # Use total_area / (length × 3) as approximation
        total_area = sum(f['area'] for f in main_faces)
        blank_width = total_area / (actual_length * 3) + total_bend_allowance
    
    # Ensure blank_length matches the returned length
    if abs(blank_length - length) > 1.0:
        blank_length = length
    
    return blank_length, blank_width

def extract_dimensions(step_file_path):
    shape = read_step_file(step_file_path)
    if shape is None:
        return None

    faces_data = get_all_faces(shape)

    # Bounding dimensions
    length, width, height = compute_bounding_box_dimensions(shape, faces_data)

    # Thickness
    thickness = compute_thickness(shape, faces_data, (length, width, height))

    # Blank size
    blank_length, blank_width = compute_blank_size(
        shape, faces_data, length, width, height, thickness
    )

    volume_mm3, surface_area_mm2 = compute_volume_and_surface_area(shape)

    return {
        'Length_mm': round(length, 3),
        'Width_mm': round(width, 3),
        'Height_mm': round(height, 3),
        'Thickness_mm': round(thickness, 3),
        'Blank_Length_mm': round(blank_length, 3),
        'Blank_Width_mm': round(blank_width, 3),
        'Volume_mm3': round(volume_mm3, 2),
        'Surface_Area_mm2': round(surface_area_mm2, 2)
    }


'''
def main():
    if len(sys.argv) < 2:
        print("Usage: python process_cad.py <step_file.stp>")
        sys.exit(1)

    step_file_path = sys.argv[1]
    part_number = step_file_path.split("\\")[-1].replace(".stp", "")

    print(f"\n{'='*60}")
    print("STEP Dimension Extractor")
    print(f"{'='*60}")
    print(f"Input file: {step_file_path}")
    print(f"{'='*60}\n")

    dimensions = extract_dimensions(step_file_path)

    if dimensions is None:
        print("Error: Failed to extract dimensions")
        sys.exit(1)
    # ---- Print results (optional) ----
    print("Extracted Dimensions:")
    for k, v in dimensions.items():
        print(f"  {k}: {v}")
    # ---- STORE INTO POSTGRES ----
    insert_part_dimensions(dimensions, part_number)

    print("\nDimensions stored successfully in database")

if __name__ == "__main__":
    main()
'''


