import vtk
import sys

#sys.stdout.write("HI")
output_folder = r'C:\Users\Dasha\Documents\images\holes_output' + r'\results'
# The source file
def extract():
    results = []
    minind = 0
    minrange = 9999
    for i in range(int(sys.argv[1])):
        fileName = output_folder + str(i) + ".vtu"
        reader = vtk.vtkXMLUnstructuredGridReader()
        reader.SetFileName(fileName)
        reader.Update()  # Needed because of GetScalarRange
        output = reader.GetOutput()
        potential = output.GetPointData().GetArray("Temperature:Temperature").GetRange()
        potval = potential[1] - potential[0]
        results.append([i, potval])
        if (minrange > potval):
            minrange = potval
            minind = 0        
    print(results[minind][0], file = sys.stdout) 


# rootsfile = r"C:\Users\Dasha\Documents\images\gen1results.vtu"
# connectfile = r"C:\Users\Dasha\Documents\images\gen2results.vtu"
# results = []
# minind = 0
# minrange = 9999
# # Read the source file.
# reader = vtk.vtkXMLUnstructuredGridReader()
# reader.SetFileName(rootsfile)
# reader.Update()  # Needed because of GetScalarRange
# output = reader.GetOutput()
# potential = output.GetPointData().GetArray("Temperature:Temperature").GetRange()
# potval = potential[1] - potential[0]
# results.append(["roots", potval])
# if (minrange > potval):
#     minrange = potval
#     minind = 0

# reader = vtk.vtkXMLUnstructuredGridReader()
# reader.SetFileName(connectfile)
# reader.Update()  # Needed because of GetScalarRange
# output = reader.GetOutput()
# potential = output.GetPointData().GetArray("Temperature:Temperature").GetRange()
# potval = potential[1] - potential[0]
# results.append(["connect", potval])
# if (minrange > potval):
#     minrange = potval
#     minind = 1
# print(results[minind][0], file = sys.stdout) 
# #sys.stdout.write("foobar")

extract()
