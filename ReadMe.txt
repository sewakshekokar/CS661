FILES:
- particle_tracing.py       : Main script
- tornado3d_vector.vti      : Input 3D vector field (must contain a 'vectors' array)
- <output_file>.vtp         : Output streamline

USAGE:
python particle_tracing.py <x> <y> <z> tornado3d_vector.vti <output_file.vtp>

Example:
python particle_tracing.py 0 0 7 tornado3d_vector.vti streamline.vtp

REQUIREMENTS:
- Python 3
- VTK
- NumPy
