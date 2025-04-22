CS661 Assignment 1

1. 2D Isocontour Extraction

To run the isocontour extraction script:
python extractIsocontour.py <input_file.vti> <iso_value> <output_file.vtp>

Example:
python extractIsocontour.py Isabel_2D.vti 100 output_contour.vtp

Note: The iso_value should be between -1438 and 630.

2. VTK Volume Rendering

To run the volume rendering script:
python volumeRendering.py <input_file.vti> <phong_shading>

Example:
python volumeRendering.py Isabel_3D.vti true

Note: Set <phong_shading> to 'true' or 'false' (case-insensitive) to enable or disable Phong shading.

Requirements:
- VTK library
- Python 3.x
