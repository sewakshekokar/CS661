# Importing libraries
from vtk import *
import sys

def volumeRender(vti_file, phong_shading):
    # Reading input file
    print("Reading Input File...")
    image_reader = vtkXMLImageDataReader()
    image_reader.SetFileName(vti_file)
    image_reader.Update()

    # Defining ColorTransferFunction as given in assignmnet
    color_trans_func = vtkColorTransferFunction()
    color_trans_func.AddRGBPoint(-4931.54, 0, 1, 1)
    color_trans_func.AddRGBPoint(-2508.95, 0, 0, 1)
    color_trans_func.AddRGBPoint(-1873.9, 0, 0, 0.5)
    color_trans_func.AddRGBPoint(-1027.16, 1, 0, 0)
    color_trans_func.AddRGBPoint(-298.031, 1, 0.4, 0)
    color_trans_func.AddRGBPoint(2594.97, 1, 1, 0)

    # Defining OpacityTransferFunction as given in assignment
    opa_trans_func = vtkPiecewiseFunction()
    opa_trans_func.AddPoint(-4931.54, 1.0)
    opa_trans_func.AddPoint(101.815, 0.002)
    opa_trans_func.AddPoint(2594.97, 0.0)

    # Setting up volume properties
    volume_property = vtkVolumeProperty()
    volume_property.SetColor(color_trans_func)
    volume_property.SetScalarOpacity(opa_trans_func)
    volume_property.SetInterpolationTypeToLinear()

    # If phong_shading is true
    if phong_shading:
        volume_property.ShadeOn()
        volume_property.SetAmbient(0.5)
        volume_property.SetDiffuse(0.5)
        volume_property.SetSpecular(0.5)
    
    volume_mapper = vtkSmartVolumeMapper()
    volume_mapper.SetInputConnection(image_reader.GetOutputPort())

    # Creating volume object
    volume = vtkVolume()
    volume.SetMapper(volume_mapper)
    volume.SetProperty(volume_property)

    outline_filter = vtkOutlineFilter()
    outline_filter.SetInputConnection(image_reader.GetOutputPort())

    outline_mapper = vtkPolyDataMapper()
    outline_mapper.SetInputConnection(outline_filter.GetOutputPort())

    outline_actor = vtkActor()
    outline_actor.SetMapper(outline_mapper)
    outline_actor.GetProperty().SetColor(0, 0, 0)

    # Creating render window
    renderer = vtkRenderer()
    render_window = vtkRenderWindow()
    render_window.SetSize(1000, 1000)
    render_window.AddRenderer(renderer)

    render_window_interactor = vtkRenderWindowInteractor()
    render_window_interactor.SetRenderWindow(render_window)

    renderer.AddVolume(volume)
    renderer.AddActor(outline_actor)
    renderer.SetBackground(1, 1, 1)

    print("Rendering volume...")
    render_window.Render()

    # print("Saving screenshot...")
    # window_to_image = vtkWindowToImageFilter()
    # window_to_image.SetInput(render_window)
    # window_to_image.Update()

    # writer = vtkPNGWriter()
    # writer.SetFileName("volume_render.png")
    # writer.SetInputConnection(window_to_image.GetOutputPort())
    # writer.Write()

    print("Displaying Render Window...")
    render_window_interactor.Start()


if __name__ == "__main__":
    if (len(sys.argv) != 3):
        print("Usage: python volumeRendering.py <input_file.vti> <phong_shading>")
        sys.exit(1)
    
    vti_file = sys.argv[1]
    phong_shading = sys.argv[2].lower() == 'true'

    volumeRender(vti_file, phong_shading)
