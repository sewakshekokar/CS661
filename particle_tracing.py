import vtk
import numpy as np
import sys

# Step size and maximum number of steps
STEP_SIZE = 0.05 # How far to move in each RK4 step
MAX_STEPS = 1000 # Maximum number of integration steps

def load_VTK_file(filepath):
    """
    Loads a VTK file (.vti) and returns the data object.
    This function uses vtkXMLImageDataReader to read structured volumetric data.
    The output is a VTK data object that we can sample for vector values.
    """
    reader = vtk.vtkXMLImageDataReader()
    reader.SetFileName(filepath)
    reader.Update()
    return reader.GetOutput()

def is_within_bounds(point, bounds):
    """
    Check if a point lies within the bounds.
    This prevents us from tracing streamlines into areas where there is no data.
    """
    x, y, z = point
    return (bounds[0] <= x <= bounds[1] and
            bounds[2] <= y <= bounds[3] and
            bounds[4] <= z <= bounds[5])

def get_vector_at_point(data, point):
    """
    Interpolates the vector field at a specific point using vtkProbeFilter.
    It allows us to estimate vector values at arbitrary locations, not just grid points.
    """
    # Creating a single-point polydata
    point_polydata = vtk.vtkPolyData()
    points = vtk.vtkPoints()
    points.InsertNextPoint(point)
    point_polydata.SetPoints(points)

    # Using vtkProbeFilter to sample the vector field at the point
    probe = vtk.vtkProbeFilter()
    probe.SetInputData(point_polydata)
    probe.SetSourceData(data)
    probe.Update()

    output = probe.GetOutput()
    vectors = output.GetPointData().GetVectors()
    if vectors is None or vectors.GetNumberOfTuples() == 0:
        return None

    return np.array(vectors.GetTuple3(0))

def rk4_integration(data, point, step_size, bounds):
    """
    Performs one RK4 step to estimate the next point.
    It helps us trace smooth streamlines through a vector field.
    """
    # Sampling vectors at intermediate points to estimate the next point
    v1 = get_vector_at_point(data, point)
    if v1 is None:
        return None
    k1 = step_size * v1

    v2 = get_vector_at_point(data, point + k1 / 2)
    if v2 is None:
        return None
    k2 = step_size * v2

    v3 = get_vector_at_point(data, point + k2 / 2)
    if v3 is None:
        return None
    k3 = step_size * v3

    v4 = get_vector_at_point(data, point + k3)
    if v4 is None:
        return None
    k4 = step_size * v4

    # RK4 weighted average
    next_point = point + (k1 + 2 * k2 + 2 * k3 + k4) / 6

    # Ensuring the new point lies within bounds
    if not is_within_bounds(next_point, bounds):
        return None

    return next_point

def trace_streamline(field_data, seed_loc, step_size, max_steps):
    """
    Traces a full streamline from a seed point using RK4 in both directions.
    We go forward and backward from the seed to capture the entire streamline path.
    """
    bounds = field_data.GetBounds()
    # streamline = [seed_loc]

    # Forward integration
    forward = []
    current_point = seed_loc
    for i in range(max_steps):
        next_point = rk4_integration(field_data, current_point, step_size, bounds)
        if next_point is None:
            print(f"Forward integration stopped at step {i}")
            break
        forward.append(next_point)
        # streamline.append(next_point)
        current_point = next_point

    # Backward integration
    backward = []
    current_point = seed_loc
    for i in range(max_steps):
        next_point = rk4_integration(field_data, current_point, -step_size, bounds)
        if next_point is None:
            print(f"Backward integration stopped at step {i}")
            break
        backward.insert(0, next_point)
        current_point = next_point

    return backward + [seed_loc] + forward

def save_streamline(points_list, filename):
    """
    This saves the output file which is viewable in tools like ParaView.
    """
    points = vtk.vtkPoints()
    lines = vtk.vtkCellArray()

    for pt in points_list:
        points.InsertNextPoint(pt)

    # Creating a polyline that connects all points
    lines.InsertNextCell(len(points_list))
    for i in range(len(points_list)):
        lines.InsertCellPoint(i)

    polydata = vtk.vtkPolyData()
    polydata.SetPoints(points)
    polydata.SetLines(lines)

    writer = vtk.vtkXMLPolyDataWriter()
    writer.SetFileName(filename)
    writer.SetInputData(polydata)
    writer.Write()

    print(f"Streamline saved as: {filename}")

def main():
    """
    Expects the command line to provide a seed location (x, y, z),
    a .vti file and a .vtp file name to save streamline.
    """
    if len(sys.argv) != 6:
        print("Usage: python particle_tracing.py <x> <y> <z> tornado3d_vector.vti <output_file.vtp>")
        sys.exit(1)

    seed_location = np.array([float(sys.argv[1]), float(sys.argv[2]), float(sys.argv[3])])
    vtk_filename = sys.argv[4]

    vtk_file = load_VTK_file(vtk_filename)
    # Set the 'vectors' array as the active vector array
    vtk_file.GetPointData().SetActiveVectors("vectors")

    streamline = trace_streamline(vtk_file, seed_location, STEP_SIZE, MAX_STEPS)
    save_streamline(streamline, sys.argv[5])

if __name__ == "__main__":
    main()
