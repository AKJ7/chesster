from mpl_toolkits.mplot3d import Axes3D
import matplotlib.pyplot as plt
import sys as sys
import os as os
sys.path.append(os.path.dirname(sys.path[0]))
from moduls.GenericSysFunctions import ImportCSV
import numpy as np
DIRPATH = os.path.dirname(__file__)
Dir = DIRPATH+"/Trainingsdaten/"
X = ImportCSV(Dir, "Input850.csv", ";")
Y = ImportCSV(Dir, "Output850.csv", ";")

fig = plt.figure()
ax = fig.add_subplot(211, projection='3d')
ax2 = fig.add_subplot(221, projection='3d')
ax.set_title('Simple Filtering')
ax.set_xlabel('x [px]')
ax.set_ylabel('y [px]')
ax.set_zlabel('Depth [mm]')
ax2.set_xlabel('X Robot KOS [mm]')
ax2.set_ylabel('Y Robot KOS [mm]')
ax2.set_zlabel('Z Robot KOS [mm]')
ax3 = fig.add_subplot(212, projection='3d')
ax4 = fig.add_subplot(222, projection='3d')
ax3.set_title('Advanced Filtering')
ax3.set_xlabel('x [px]')
ax3.set_ylabel('y [px]')
ax3.set_zlabel('Depth [mm]')
ax4.set_xlabel('X Robot KOS [mm]')
ax4.set_ylabel('Y Robot KOS [mm]')
ax4.set_zlabel('Z Robot KOS [mm]')

print(X.shape[1])

X_Hat = X.copy()

X = X[:, X_Hat[2,:]>500]
Y = Y[:, X_Hat[2,:]>500]
X_Hat = X.copy()

X = X[:, X_Hat[2,:]<1100]
Y = Y[:, X_Hat[2,:]<1100]
X_Hat = X.copy()

ax.scatter(X[0,:], X[1,:], X[2,:], c='red', marker='o')
ax2.scatter(Y[0,:], Y[1,:], Y[2,:], c='red', marker='o')
print(X.shape[1])

"""

sort = X[2,:].argsort()
X = X[:, sort]
Y = Y[:, sort]

def rolling_window(a, window):
    shape = a.shape[:-1] + (a.shape[-1] - window + 1, window)
    strides = a.strides + (a.strides[-1],)
    return np.lib.stride_tricks.as_strided(a, shape=shape, strides=strides)

sigma = np.std(rolling_window(X[2,:], 5), 1)
my = np.mean(rolling_window(X[2,:], 5), 1)

sigma = np.std(X[2,:])
my = np.mean(X[2,:])

X = X[:, X_Hat[2,:]>my-sigma]
Y = Y[:, X_Hat[2,:]>my-sigma]
X_Hat = X.copy()

X = X[:, X_Hat[2,:]<my+sigma]
Y = Y[:, X_Hat[2,:]<my+sigma]
X_Hat = X.copy()

ax3.scatter(X[0,:], X[1,:], X[2,:], c='red', marker='o')
ax4.scatter(Y[0,:], Y[1,:], Y[2,:], c='red', marker='o')

print(X.shape[1])
"""

plt.show()
