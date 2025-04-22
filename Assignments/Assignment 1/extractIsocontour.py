# Importing VTK 
from vtk import *
import sys

# Linear Interpolation (LERP) function for 2 points
def interpolate(point1, value1, point2, value2, iso):
    a = abs(value1 - iso)
    b = abs(value2 - iso)
    alpha = a / (a + b)
    return (1 - alpha) * point1 + alpha * point2

def extractIsocontour(vti_file, iso_value, output_file):
    print("Reading Input File...")
    # Creating VTK XML image data reader
    file_reader = vtkXMLImageDataReader()
    file_reader.SetFileName(vti_file)
    file_reader.Update()

    # Getting the image data from file
    image_data = file_reader.GetOutput()

    # Getting dimensions from image
    dimensions = image_data.GetDimensions()
    print("Dimensions: ", dimensions)

    # Extracting X and Y dimensions (X = x-axis (horizontal), Y = y-axis(vertical))
    X, Y = dimensions[0], dimensions[1]
    scalar_data = image_data.GetPointData().GetScalars()

    # Creating VTK objects to store contour points and line segments
    points = vtkPoints()
    lines = vtkCellArray()
    
    print("Extracting Isocontour...")
    for i in range(X - 1): # Iteratign from left to right (horizontal)
        for j in range(Y - 1): # Iterating from bottom to top (vertical)
            # Getting 4 points from by following counter-clockwise order (A -> B -> C -> D)
            # D -- C
            # |    |
            # A -- B
            index_A = i + j * X
            index_B = (i + 1) + j * X
            index_C = (i + 1) + (j + 1) * X
            index_D = i + (j + 1) * X

            # Getting scalar value at each points A, B, C, D
            value_A = scalar_data.GetTuple1(index_A)
            value_B = scalar_data.GetTuple1(index_B)
            value_C = scalar_data.GetTuple1(index_C)
            value_D = scalar_data.GetTuple1(index_D)

            contour_points = []

            # Edge AB
            if (min(value_A, value_B) <= iso_value) and (iso_value <= max(value_A, value_B)):
                interp_X = interpolate(i, value_A, i + 1, value_B, iso_value)
                interp_Y = j
                contour_points.append(points.InsertNextPoint(interp_X, interp_Y, 0))
            
            # Edge BC
            if (min(value_B, value_C) <= iso_value) and (iso_value <= max(value_B, value_C)):
                interp_X = i + 1
                interp_Y = interpolate(j, value_B, j + 1, value_C, iso_value)
                contour_points.append(points.InsertNextPoint(interp_X, interp_Y, 0))
            
            # Edge CD
            if (min(value_C, value_D) <= iso_value) and (iso_value <= max(value_C, value_D)):
                interp_X = interpolate(i + 1, value_C, i, value_D, iso_value)
                interp_Y = j + 1
                contour_points.append(points.InsertNextPoint(interp_X, interp_Y, 0))
            
            # Edge DA
            if (min(value_D, value_A) <= iso_value) and (iso_value <= max(value_D, value_A)):
                interp_X = i
                interp_Y = interpolate(j + 1, value_D, j, value_A, iso_value)
                contour_points.append(points.InsertNextPoint(interp_X, interp_Y, 0))

            # Connecting points
            if len(contour_points) == 2:
                line  = vtkLine()
                line.GetPointIds().SetId(0, contour_points[0])
                line.GetPointIds().SetId(1, contour_points[1])
                lines.InsertNextCell(line)
            
            elif len(contour_points) == 4:
                line1 = vtkLine()
                line1.GetPointIds().SetId(0, contour_points[0])
                line1.GetPointIds().SetId(1, contour_points[1])
                lines.InsertNextCell(line1)

                line2 = vtkLine()
                line2.GetPointIds().SetId(0, contour_points[2])
                line2.GetPointIds().SetId(1, contour_points[3])
                lines.InsertNextCell(line2)

            # print(f"Cell ({i}, {j}): A={value_A}, B={value_B}, C={value_C}, D={value_D}")
            # print("Contour Points (in counterclockwise order):", contour_points)

    # Creating a PolyData object
    poly_data = vtkPolyData()
    poly_data.SetPoints(points)
    poly_data.SetLines(lines)

    # Saving in a .png file
    print("Saving to putput file", output_file)
    writer = vtkXMLPolyDataWriter()
    writer.SetFileName(output_file)
    writer.SetInputData(poly_data)
    writer.Write()

    print("Done!")

if __name__ == "__main__":
    if (len(sys.argv) != 4):
        print("Usage: python extractIsocontour.py <input_file.vti> <iso_value> <output_file.vtp>")
        sys.exit(1)
    
    vti_file = sys.argv[1]
    iso_value = float(sys.argv[2])
    output_file = sys.argv[3]

    # Checking if the iso_value is within valid range
    if (-1438 <= iso_value and iso_value <= 630):
        extractIsocontour(vti_file, iso_value, output_file)
    else:
        print("Error: iso_value not in range (-1438 to 630)")
        sys.exit(1)
