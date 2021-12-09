import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')
import os as os
import numpy as np
DIRPATH = os.path.dirname(__file__)
Arbeitsraum=np.loadtxt(DIRPATH+'/Arbeitsraum.csv', delimiter=";", dtype=int)

for j in range(Arbeitsraum.shape[0]):
    ax.text(Arbeitsraum[j][0]+0.5,Arbeitsraum[j][1]-0.5,Arbeitsraum[j][2], f'P{j+1}:\nX: {Arbeitsraum[j, 0]}\nY: {Arbeitsraum[j, 1]}\nZ: {Arbeitsraum[j, 2]}', 'x')
    ax.scatter3D(Arbeitsraum[j][0],Arbeitsraum[j][1],Arbeitsraum[j][2], c='cyan')
plt.show()