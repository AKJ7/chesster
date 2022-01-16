from doctest import OutputChecker
from mpl_toolkits.mplot3d import Axes3D
import matplotlib.pyplot as plt
import sys as sys
import os as os
sys.path.append(os.path.dirname(sys.path[0]))
from moduls.GenericSysFunctions import ImportCSV, ExportCSV
import numpy as np

DIRPATH = "C:/Mechatroniklabor/chesster/chesster/Vision-Based-Control" #Zuhause
Dir = DIRPATH+"/Trainingsdaten/"
Names = ["Input1991Filtered_newData", "Output1991Filtered_newData"]
Input = ImportCSV(Dir, Names[0]+".csv", ";")
Output = ImportCSV(Dir, Names[1]+".csv", ";")
DIRPATH = "C:/Mechatroniklabor/chesster/chesster/Vision-Based-Control" #Zuhause
Dir = DIRPATH+"/NeuralNetworkComparison/"
Error = ImportCSV(Dir, "ErrorNewData.csv", ";")

fig = plt.figure()
ax = fig.add_subplot(211, projection='3d')

ax2 = fig.add_subplot(221, projection='3d')
ax.set_title(f'Input-Space')
ax.set_xlabel('x [px]')
ax.set_ylabel('y [px]')
ax.set_zlabel('Depth [mm]')
ax2.set_title(f'Output-Space')
ax2.set_xlabel('X Robot KOS [mm]')
ax2.set_ylabel('Y Robot KOS [mm]')
ax2.set_zlabel('Z Robot KOS [mm]')

for i in range(Input[:,-100:].shape[1]):
    if Error[0,i]>5.0 or Error[0,i]<-5.0 or Error[1,i]>5.0 or Error[1,i]<-5.0:
        color = 'r'
    elif Error[0,i]>3.0 or Error[0,i]<-3.0 or Error[1,i]>3.0 or Error[1,i]<-3.0:
        color = 'yellow'
    else:
        color = 'green'

    ax.scatter(Input[0, i], Input[1, i], Input[2, i], color=color)
    ax2.scatter(Output[0, i], Output[1, i] ,Output[2, i], color=color)

plt.show()
