from mpl_toolkits.mplot3d import Axes3D
import matplotlib.pyplot as plt
import sys as sys
import os as os
sys.path.append(os.path.dirname(sys.path[0]))
from moduls.GenericSysFunctions import ImportCSV
import numpy as np
DIRPATH = os.path.dirname(__file__)
Dir = DIRPATH+"/Trainingsdaten/"
X = ImportCSV(Dir, "Input_2.csv", ";")
X[2,:] = X[2,:]
Y = ImportCSV(Dir, "Output_2.csv", ";")

fig = plt.figure()
ax = fig.add_subplot(211, projection='3d')
ax2 = fig.add_subplot(212, projection='3d')

ax.scatter(X[0,:], X[1,:], X[2,:], c='red', marker='o')
ax2.scatter(Y[0,:], Y[1,:], Y[2,:], c='red', marker='o')
ax.set_xlabel('x [px]')
ax.set_ylabel('y [px]')
ax.set_zlabel('Depth [mm]')
ax2.set_xlabel('X Robot KOS [mm]')
ax2.set_ylabel('Y Robot KOS [mm]')
ax2.set_zlabel('Z Robot KOS [mm]')
plt.show()
